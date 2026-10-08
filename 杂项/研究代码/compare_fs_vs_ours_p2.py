# -*- coding: utf-8 -*-
"""Head-to-head on P2 (soft robot): previous method FS-KOOPMAN vs our new model.

Same raw trajectory (default 93, the only trajectory that is a TEST trajectory in
BOTH splits). Open-loop rollout with true inputs; both models start from the true
initial condition (our model additionally uses the true P-step history window).

Outputs:
  杂项/图表/p2_fs_vs_ours_<traj>.png
  杂项/实验结果/p2_fs_vs_ours_<traj>.json
"""
import os, sys, json
import numpy as np
import torch

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ---- our model ----
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gate_context_koopman import CtxKoopman, build_split, H_MAX, REPO, DEV  # noqa: E402
from gate14_stabilize import BudgetedCtxKoopman  # noqa: E402
from patchtst_koopman.utils.config_loader import load_config  # noqa: E402

# ---- previous method ----
MC = r"D:\Project\my_lunwen\建模代码"
sys.path.insert(0, MC)
from modeling.trainers.fs_edmd import OursKoopmanTrainer  # noqa: E402

ROOT = r"D:\Project\Transformer-Koopman\Transformer-Koopman"
CKPT = os.path.join(ROOT, "杂项", "模型检查点")
RAW = os.path.join(ROOT, "数据备份", "软体平台数据", "原始数据")
FIGDIR = os.path.join(ROOT, "杂项", "图表")
RESDIR = os.path.join(ROOT, "杂项", "实验结果")
OLD = r"D:\Project\my_lunwen\结果备份\软体平台训练结果"
OLDDATA = r"D:\Project\my_lunwen\数据备份\软体平台\处理后的数据"

TRAJ = int(sys.argv[1]) if len(sys.argv) > 1 else 93
H = H_MAX
STRIDE = 20

# ---- norms ----
cfg = load_config(os.path.join(REPO, "configs", "platform2.yaml"))
data_dir = os.path.abspath(os.path.join(REPO, cfg["data"]["data_dir"]))
P = cfg["encoder"]["history_length"]
_, _, _, _, norm = build_split(data_dir, "train", cfg)
meta = np.load(os.path.join(OLDDATA, "meta.npz"), allow_pickle=True)
oxm, oxs, oum, ous = meta["x_mean"], meta["x_scale"], meta["u_mean"], meta["u_scale"]

# ---- models ----
new = BudgetedCtxKoopman(cfg, r=2, delta_A=0.07).to(DEV)
new.load_state_dict(torch.load(os.path.join(CKPT, "A_stab_openloop_lam0.0_rho0.99.pt"), map_location=DEV), strict=False)
new.eval()
fs = OursKoopmanTrainer(verbose=False).load(os.path.join(OLD, "fs_edmd.pkl"))

# ---- data (raw physical units) ----
d = np.load(os.path.join(RAW, f"{TRAJ:02d}.npz"))
x_raw = d["x"].astype(np.float64); u_raw = d["u"].astype(np.float64)
print(f"trajectory {TRAJ}: n={len(x_raw)}  x={x_raw.shape}  u={u_raw.shape}")


def ours_rollout(xx, uu, k, H, scheduled=True):
    """xx,uu already normalized by OUR norm.

    scheduled=True  : RTI-SP style --- encode ONCE, propagate the latent, re-schedule
                      the context from the rolled-out history at each step.
    scheduled=False : re-encode the (rolled-out) history window with the encoder each step.
    """
    xh = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
    uh = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
    preds = []
    with torch.no_grad():
        z = new.encoder(xh) if scheduled else None
        for h in range(1, H + 1):
            ut = torch.tensor(uu[k + h - 1], dtype=torch.float32).unsqueeze(0).to(DEV)
            if scheduled:
                A, Bm = new.get_AB(xh, uh)
                z = torch.einsum('nij,nj->ni', A, z) + torch.einsum('nij,nj->ni', Bm, ut)
                xn = new.decoder(z)
            else:
                xn = new(xh, uh, ut)
            xh = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
            uh = torch.cat([uh[:, 1:, :], ut.unsqueeze(1)], dim=1)
            preds.append(xn.squeeze(0).cpu().numpy())
    return np.array(preds)


def fs_rollout(xx, uu, k, H):
    """FS-KOOPMAN in its own normalized space; xx,uu raw physical."""
    x0n = (xx[k] - oxm) / oxs
    usn = [(uu[k + h] - oum) / ous for h in range(H)]
    pn = fs.predict(x0n, usn)
    return pn * oxs + oxm


xn = (x_raw - norm["x_mean"]) / norm["x_std"]
un = (u_raw - norm["u_mean"]) / norm["u_std"]

err = {"fs": {h: [] for h in range(1, H + 1)},
       "ours_sched": {h: [] for h in range(1, H + 1)},
       "ours_reenc": {h: [] for h in range(1, H + 1)}}
example = None
for k in range(P - 1, len(x_raw) - H - 1, STRIDE):
    gt = x_raw[k + 1:k + 1 + H]
    pf = fs_rollout(x_raw, u_raw, k, H)
    ps = ours_rollout(xn, un, k, H, scheduled=True) * norm["x_std"] + norm["x_mean"]
    pr = ours_rollout(xn, un, k, H, scheduled=False) * norm["x_std"] + norm["x_mean"]
    for h in range(1, H + 1):
        err["fs"][h].append(np.linalg.norm(pf[h - 1] - gt[h - 1]))
        err["ours_sched"][h].append(np.linalg.norm(ps[h - 1] - gt[h - 1]))
        err["ours_reenc"][h].append(np.linalg.norm(pr[h - 1] - gt[h - 1]))
    if example is None:
        example = (k, gt, pf, ps, pr)

rmse = {name: {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in err[name].items()} for name in err}
print(f"\n=== rollout RMSE on raw trajectory {TRAJ} (physical units), {len(err['fs'][1])} rollouts ===")
print("  H      FS-KOOPMAN   ours(sched)  ours(reenc)")
for h in [1, 5, 10, 20]:
    print(f"  {h:<4}   {rmse['fs'][h]:.5f}      {rmse['ours_sched'][h]:.5f}     {rmse['ours_reenc'][h]:.5f}")

# ---- plot ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

k, gt, pf, ps, pr = example
fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
ax = axes[0]
ax.plot(gt[:, 0], gt[:, 1], "k-o", ms=3, lw=2.2, label="ground truth")
ax.plot(pf[:, 0], pf[:, 1], "--s", color="tab:green", ms=3, lw=1.6, label="FS-KOOPMAN (previous)")
ax.plot(ps[:, 0], ps[:, 1], "-^", color="tab:blue", ms=3, lw=1.6, label="ours: A(c) scheduled")
ax.plot(pr[:, 0], pr[:, 1], "-.", color="tab:cyan", ms=3, lw=1.4, label="ours: A(c) re-encode")
ax.scatter([gt[0, 0]], [gt[0, 1]], s=90, facecolors="none", edgecolors="k", zorder=5)
ax.set_title(f"P2 trajectory {TRAJ}, open-loop rollout (H={H})")
ax.set_xlabel("state 1 (physical)"); ax.set_ylabel("state 2 (physical)")
ax.legend(fontsize=8); ax.grid(alpha=0.3); ax.set_aspect("equal", adjustable="datalim")

ax = axes[1]
hh = np.arange(1, H + 1)
ax.semilogy(hh, [np.linalg.norm(pf[h - 1] - gt[h - 1]) for h in hh], "--s", color="tab:green", ms=3, label="FS-KOOPMAN")
ax.semilogy(hh, [np.linalg.norm(ps[h - 1] - gt[h - 1]) for h in hh], "-^", color="tab:blue", ms=3, label="ours: scheduled")
ax.semilogy(hh, [np.linalg.norm(pr[h - 1] - gt[h - 1]) for h in hh], "-.", color="tab:cyan", ms=3, label="ours: re-encode")
ax.set_title("Per-step error vs horizon"); ax.set_xlabel("horizon step h")
ax.set_ylabel("||x_hat - x_true|| (physical, log)")
ax.legend(fontsize=8); ax.grid(alpha=0.3, which="both")

fig.suptitle(f"P2 soft-robot trajectory {TRAJ}: FS-KOOPMAN vs Transformer-Koopman (A(c))", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.96])
f1 = os.path.join(FIGDIR, f"p2_fs_vs_ours_{TRAJ}.png")
fig.savefig(f1, dpi=150); plt.close(fig)
print("saved:", f1)

jf = os.path.join(RESDIR, f"p2_fs_vs_ours_{TRAJ}.json")
with open(jf, "w", encoding="utf-8", newline="") as fh:
    json.dump({"trajectory": TRAJ, "H": H, "stride": STRIDE, "n_rollouts": len(err["fs"][1]),
               "models": {"fs_koopman": "fs_edmd.pkl (previous method)",
                          "ours": "A_stab_openloop_lam0.0_rho0.99.pt (history-conditioned A(c))"},
               "rmse_physical": rmse}, fh, ensure_ascii=False, indent=2)
print("saved:", jf)
