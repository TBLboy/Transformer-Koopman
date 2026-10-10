from pathlib import Path
import json
import math
import numpy as np
import torch
import torch.nn as nn

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
CKPT = ROOT / "训练代码" / "deploy" / "algorithms" / "tk_assets" / "model_assets" / "platform2_full_model.pth"
DATA = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\testB_ref_defect.json")

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div)
        pe[:, 1::2] = torch.cos(position * div)
        self.register_buffer("pe", pe.unsqueeze(0))
    def forward(self, x):
        return x + self.pe[:, :x.size(1), :]

class PatchTSTEncoder(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.P = cfg["encoder"]["history_length"]; self.p = cfg["encoder"]["patch_length"]
        self.n = cfg["data"]["state_dim"]; self.d = cfg["encoder"]["latent_dim"]
        self.d_model = cfg["encoder"]["d_model"]; self.n_layers = cfg["encoder"]["n_layers"]
        self.d_history = self.d - self.n; self.num_patches = self.P // self.p
        self.patch_embedding = nn.Linear(self.p * self.n, self.d_model)
        self.positional_encoding = PositionalEncoding(self.d_model)
        layer = nn.TransformerEncoderLayer(d_model=self.d_model, nhead=cfg["encoder"]["n_heads"],
                                           dim_feedforward=cfg["encoder"]["d_ff"],
                                           dropout=cfg["encoder"].get("dropout", 0.1), batch_first=True)
        self.transformer = nn.TransformerEncoder(layer, num_layers=self.n_layers)
        self.projection = nn.Linear(self.d_model, self.d_history)
    def forward(self, xh):
        x_t = xh[:, -1, :]
        b = xh.shape[0]
        patches = xh.reshape(b, self.num_patches, self.p, self.n).reshape(b, self.num_patches, self.p * self.n)
        e = self.positional_encoding(self.patch_embedding(patches))
        enc = self.transformer(e)
        pooled = torch.mean(enc, dim=1)
        h_t = self.projection(pooled)
        return torch.cat([x_t, h_t], dim=1)

o = torch.load(CKPT, map_location="cpu", weights_only=False)
cfg = o["config"]; msd = o["model_state_dict"]; norm = o["normalization"]
A = np.asarray(o["koopman_A"], float); B = np.asarray(o["koopman_B"], float)
n, m = B.shape

enc = PatchTSTEncoder(cfg)
enc_sd = {k[len("encoder."):]: v for k, v in msd.items() if k.startswith("encoder.")}
enc.load_state_dict(enc_sd)
enc.eval()

x_mean = np.asarray(norm.get("x_mean", np.zeros(n)), float).reshape(1, -1)
x_std = np.asarray(norm.get("x_std", np.ones(n)), float).reshape(1, -1)

P = cfg["encoder"]["history_length"]
Bpinv = np.linalg.pinv(B)
Pproj = B @ Bpinv
ImP = np.eye(n) - Pproj

def traj_windows(x, tid):
    zs = []
    for t in np.unique(tid):
        xi = x[tid == t]
        if len(xi) < P + 1:
            continue
        xn = (xi - x_mean) / x_std
        hist = np.stack([xn[k - P + 1:k + 1] for k in range(P - 1, len(xn))], axis=0)  # (T, P, n)
        with torch.no_grad():
            z = enc(torch.tensor(hist, dtype=torch.float32)).numpy()
        zs.append(z)
    return zs

results = {}
for f in ["train.npz", "val.npz"]:
    z = np.load(DATA / f)
    x, tid = z["x"].astype(float), z["trajectory_id"]
    zs = traj_windows(x, tid)
    abs_def, rel_def, abs_d = [], [], []
    for zz in zs:
        d = zz[1:] - zz[:-1] @ A.T  # z_{k+1} - A z_k
        r = d @ ImP.T
        nd = np.linalg.norm(d, axis=1)
        nr = np.linalg.norm(r, axis=1)
        abs_def.append(nr); rel_def.append(nr / (nd + 1e-12)); abs_d.append(nd)
    abs_def = np.concatenate(abs_def); rel_def = np.concatenate(rel_def); abs_d = np.concatenate(abs_d)
    results[f] = {
        "n_samples": int(len(abs_def)),
        "mean_abs_increment": float(abs_d.mean()),
        "mean_abs_defect": float(abs_def.mean()),
        "median_abs_defect": float(np.median(abs_def)),
        "p95_abs_defect": float(np.percentile(abs_def, 95)),
        "mean_relative_defect": float(rel_def.mean()),
        "median_relative_defect": float(np.median(rel_def)),
    }

results["note"] = "reference = measured trajectory; defect=(I-BB+)(z_{k+1}-A z_k) in normalized latent; P2 only (no P1 checkpoint)"
print(json.dumps(results, indent=2))
OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
