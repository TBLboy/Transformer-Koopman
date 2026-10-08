from pathlib import Path
import json, math
import numpy as np
import torch
import torch.nn as nn

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
CKPT = ROOT / "训练代码" / "deploy" / "algorithms" / "tk_assets" / "model_assets" / "platform2_full_model.pth"
DATA = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\D_P2_D7.json")

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div); pe[:, 1::2] = torch.cos(position * div)
        self.register_buffer("pe", pe.unsqueeze(0))
    def forward(self, x): return x + self.pe[:, :x.size(1), :]

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
        x_t = xh[:, -1, :]; b = xh.shape[0]
        patches = xh.reshape(b, self.num_patches, self.p, self.n).reshape(b, self.num_patches, self.p * self.n)
        e = self.positional_encoding(self.patch_embedding(patches))
        enc = self.transformer(e); pooled = torch.mean(enc, dim=1)
        return torch.cat([x_t, self.projection(pooled)], dim=1)

o = torch.load(CKPT, map_location="cpu", weights_only=False)
cfg = o["config"]; norm = o["normalization"]
A = np.asarray(o["koopman_A"], float); B = np.asarray(o["koopman_B"], float)
n, m = B.shape
enc = PatchTSTEncoder(cfg)
enc.load_state_dict({k[len("encoder."):]: v for k, v in o["model_state_dict"].items() if k.startswith("encoder.")})
enc.eval()
x_mean = np.asarray(norm.get("x_mean", np.zeros(n)), float).reshape(1, -1)
x_std = np.asarray(norm.get("x_std", np.ones(n)), float).reshape(1, -1)
u_mean = np.asarray(norm.get("u_mean", np.zeros(m)), float).reshape(1, -1)
u_std = np.asarray(norm.get("u_std", np.ones(m)), float).reshape(1, -1)
P = cfg["encoder"]["history_length"]

resid = []; nl_ratio = []
for f in ["train.npz", "val.npz"]:
    z = np.load(DATA / f)
    x, u, tid = z["x"].astype(float), z["u"].astype(float), z["trajectory_id"]
    for t in np.unique(tid):
        xi = x[tid == t]; ui = u[tid == t]
        if len(xi) < P + 4: continue
        xn = (xi - x_mean) / x_std; un = (ui - u_mean) / u_std
        hist = np.stack([xn[j - P + 1:j + 1] for j in range(P - 1, len(xn))], axis=0)
        with torch.no_grad():
            zz = enc(torch.tensor(hist, dtype=torch.float32)).numpy()
        uu = un[P - 1:]
        # 1-step residual
        d1 = zz[1:] - zz[:-1] @ A.T - uu[:-1] @ B.T
        resid.append(d1)
        # curvature: 2-step linear prediction error vs 1-step
        z2_pred = (zz[:-2] @ A.T + uu[:-2] @ B.T) @ A.T + uu[1:-1] @ B.T
        e2 = np.linalg.norm(zz[2:] - z2_pred, axis=1)
        e1 = np.linalg.norm(d1[:-1], axis=1)
        nl_ratio.append(e2 / (e1 + 1e-12))

R = np.concatenate(resid, 0)
ev = np.linalg.eigvalsh(np.cov(R.T))
ev = np.sort(ev)[::-1]; evn = ev / ev.sum()
nlr = np.concatenate(nl_ratio, 0)
res = {
    "n_residual_samples": int(R.shape[0]),
    "residual_cov_eigvals_normalized": [round(float(v), 5) for v in evn],
    "effective_rank_99pct": int(np.searchsorted(np.cumsum(evn), 0.99) + 1),
    "effective_rank_90pct": int(np.searchsorted(np.cumsum(evn), 0.90) + 1),
    "two_step_vs_one_step_ratio_median": float(np.median(nlr)),
    "two_step_vs_one_step_ratio_q95": float(np.quantile(nlr, 0.95)),
    "verdict": "Low effective rank (<n) => low-dim obstruction (M5 viable); effective rank ~= n => no compact obstruction geometry.",
}
print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
