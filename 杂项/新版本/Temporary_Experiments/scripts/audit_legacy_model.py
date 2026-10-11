# -*- coding: utf-8 -*-
"""Gate 0: reproduce the legacy (deployed) Platform-2 model end-to-end.

Loads the self-contained deploy assets (no dependency on the training package or
on the stale config data path), runs an open-loop H-step rollout on the frozen
test split, and prints RMSE so it can be compared with the recorded legacy result.

Read-only: reads .pth/.json/.npz, writes nothing except stdout.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
EXP_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(EXP_DIR)))
DEPLOY = os.path.join(REPO, "代码部分", "老版本", "训练代码", "deploy", "algorithms", "tk_assets")
PROC = os.path.join(REPO, "数据备份", "软体平台数据", "处理后的数据")
sys.path.insert(0, os.path.dirname(DEPLOY))  # so `tk_assets` is importable

CKPT = os.path.join(DEPLOY, "model_assets", "platform2_full_model.pth")
META = os.path.join(DEPLOY, "model_assets", "platform2_metadata.json")

print("=" * 78)
print("A. checkpoint / metadata inspection")
print("=" * 78)
obj = torch.load(CKPT, map_location="cpu", weights_only=False)
print("  top-level type:", type(obj).__name__)
if isinstance(obj, dict):
    for k in sorted(obj.keys()):
        v = obj[k]
        if hasattr(v, "shape"):
            print("    %-24s tensor %s" % (k, tuple(v.shape)))
        elif isinstance(v, dict):
            print("    %-24s dict keys=%s" % (k, sorted(v.keys())[:20]))
        else:
            print("    %-24s %r" % (k, str(v)[:160]))
sd = obj.get("model_state_dict", obj.get("state_dict", obj)) if isinstance(obj, dict) else obj
if isinstance(sd, dict):
    layers = sorted({k for k in sd if k.startswith("encoder.transformer.layers.")})
    print("  encoder transformer layer keys (%d):" % len(layers))
    for k in layers:
        print("     ", k, tuple(sd[k].shape) if hasattr(sd[k], "shape") else "")
print("  metadata:", json.dumps(json.load(open(META, encoding="utf-8")), ensure_ascii=False))

print()
print("=" * 78)
print("B. build the standalone model exactly as deployed")
print("=" * 78)
meta = json.load(open(META, encoding="utf-8"))
cfg = {
    "data": {"state_dim": meta["state_dim"], "control_dim": meta["control_dim"]},
    "encoder": {
        "history_length": meta["history_length"], "patch_length": meta["patch_length"],
        "latent_dim": meta["latent_dim"], "d_model": meta["d_model"],
        "n_layers": meta["n_layers"], "n_heads": meta["n_heads"],
        "d_ff": 64, "dropout": 0.1, "readout_method": "mean",
    },
    "koopman": {"rho_max": 0.9999},
}
from tk_assets.transformer_koopman_model import PatchTSTKoopmanModel  # noqa: E402

model = PatchTSTKoopmanModel(cfg)
missing, unexpected = model.load_state_dict(sd, strict=False)
print("  cfg:", json.dumps(cfg, ensure_ascii=False))
print("  missing keys :", list(missing))
print("  unexpected   :", list(unexpected))
model.eval()

print()
print("=" * 78)
print("C. open-loop rollout on the frozen test split")
print("=" * 78)
d = np.load(os.path.join(PROC, "test.npz"))
x_raw = d["x"].astype(np.float64)
u_raw = d["u"].astype(np.float64)
tid = d["trajectory_id"]
P = meta["history_length"]

norm = obj.get("normalization") if isinstance(obj, dict) else None
if norm is None:
    # fall back to train-only constants from the Gate 0 audit
    x_mean = np.array([-0.696318, 0.048996]); x_std = np.array([3.243583, 3.415089])
    u_mean = np.array([0.238027, -0.091383]); u_std = np.array([27.962413, 28.133323])
    print("  normalization: NOT in checkpoint -> using train-only audit constants")
else:
    x_mean = np.asarray(norm["x_mean"], float).ravel()
    x_std = np.asarray(norm["x_std"], float).ravel()
    u_mean = np.asarray(norm["u_mean"], float).ravel()
    u_std = np.asarray(norm["u_std"], float).ravel()
    print("  normalization: from checkpoint")
print("  x_mean=%s x_std=%s" % (x_mean, x_std))

A = np.asarray(obj["koopman_A"], dtype=np.float64)
ev = np.linalg.eigvals(A)
print("  rho(koopman_A) computed = %.6f   (checkpoint field = %s)"
      % (float(np.max(np.abs(ev))), obj.get("spectral_radius")))
print("  koopman_A type=%s dtype=%s, model dtype=%s"
      % (type(obj["koopman_A"]).__name__, np.asarray(obj["koopman_A"]).dtype,
         next(model.parameters()).dtype))

H = 10
dt = next(model.parameters()).dtype
rows = []
for traj in range(int(tid.max()) + 1):
    m = tid == traj
    x = (x_raw[m] - x_mean) / x_std
    u = (u_raw[m] - u_mean) / u_std
    if len(x) < P + H:
        continue
    # single fixed start per trajectory (first legal index) to avoid overlapping windows
    hist = torch.tensor(x[:P], dtype=dt).unsqueeze(0)
    preds = []
    cur = hist.clone()
    with torch.no_grad():
        for h in range(H):
            ut = torch.tensor(u[P + h], dtype=dt).unsqueeze(0)
            xp = model(cur, ut).unsqueeze(1)
            preds.append(xp)
            cur = torch.cat([cur[:, 1:, :], xp], dim=1)
    pred = torch.cat(preds, 1).squeeze(0).numpy().astype(np.float64)
    tgt = x[P:P + H]
    rows.append((traj, pred, tgt))

errs = np.concatenate([(p - t) for _, p, t in rows], 0)
rmse_n = float(np.sqrt(np.mean(errs ** 2)))
rmse_n_per_ch = np.sqrt(np.mean(errs ** 2, axis=0))
print("  trajectories evaluated: %d, start index fixed at 0, H=%d" % (len(rows), H))
print("  normalized RMSE (all steps/channels): %.6f" % rmse_n)
print("  normalized RMSE per channel        : %s" % np.round(rmse_n_per_ch, 6))
# physical-unit RMSE (denormalise)
errs_phys = np.concatenate([(p * x_std + x_mean) - (t * x_std + x_mean) for _, p, t in rows], 0)
print("  physical-unit RMSE (all steps/ch)  : %.6f" % float(np.sqrt(np.mean(errs_phys ** 2))))
print("  physical-unit RMSE per channel     : %s"
      % np.round(np.sqrt(np.mean(errs_phys ** 2, axis=0)), 6))
print()
print("  NOTE legacy recorded rollout RMSE for Platform 2 (PatchTST-Koopman) = 0.474")
print("       (source: D:/Project/code-projectv2/.project-log/business-logic/main.md:43)")
