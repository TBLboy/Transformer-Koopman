from pathlib import Path
import json, math
import numpy as np
import torch
import torch.nn as nn

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
CKPT = ROOT / "训练代码" / "deploy" / "algorithms" / "tk_assets" / "model_assets" / "platform2_full_model.pth"
DATA = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\D_P2_DWR.json")

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
out_dim = cfg["data"]["state_dim"]
C = np.hstack([np.eye(out_dim), np.zeros((out_dim, n - out_dim))])
enc = PatchTSTEncoder(cfg)
enc.load_state_dict({k[len("encoder."):]: v for k, v in o["model_state_dict"].items() if k.startswith("encoder.")})
enc.eval()
x_mean = np.asarray(norm.get("x_mean", np.zeros(n)), float).reshape(1, -1)
x_std = np.asarray(norm.get("x_std", np.ones(n)), float).reshape(1, -1)
u_mean = np.asarray(norm.get("u_mean", np.zeros(m)), float).reshape(1, -1)
u_std = np.asarray(norm.get("u_std", np.ones(m)), float).reshape(1, -1)
P = cfg["encoder"]["history_length"]
H = 10
Q = np.eye(out_dim)          # output-space weight
R = 0.1 * np.eye(m)

def traj_latent(x, tid):
    out = []
    for t in np.unique(tid):
        xi = x[tid == t]; ii = np.where(tid == t)[0]
        if len(xi) < P + 1: continue
        xn = (xi - x_mean) / x_std
        hist = np.stack([xn[j - P + 1:j + 1] for j in range(P - 1, len(xn))], axis=0)
        with torch.no_grad():
            z = enc(torch.tensor(hist, dtype=torch.float32)).numpy()
        out.append((z, ii[P - 1:]))
    return out

def score_window(z_win, u_win):
    # z_win: (H+1, n), u_win: (H, m) normalized
    zn = z_win.copy()
    zhat = [zn[0]]
    for k in range(H):
        zhat.append(A @ zhat[-1] + B @ u_win[k])
    zhat = np.array(zhat)                      # (H+1,n)
    d = zn[1:] - zn[:-1] @ A.T - u_win @ B.T   # defect along TRUE trajectory
    r = zn @ C.T                               # reference = measured physical output
    # adjoint / costate on nominal trajectory
    lam = np.zeros((H + 1, n)); 
    for k in range(H, 0, -1):
        res = C @ (zhat[k] - zn[k])
        g = C.T @ Q @ res
        lam[k] = g + (A.T @ lam[k + 1] if k + 1 <= H else 0)
    sdwr = abs(np.sum([lam[k + 1] @ d[k] for k in range(H)]))
    draw = float(np.sum(np.linalg.norm(d, axis=1)))
    dJ = float(np.sum([np.sum((C @ (zhat[k] - zn[k]))**2) for k in range(1, H + 1)]))
    return sdwr, draw, dJ

rows = []
for f in ["train.npz", "val.npz"]:
    z = np.load(DATA / f)
    x, u, tid = z["x"].astype(float), z["u"].astype(float), z["trajectory_id"]
    for zz, ii in traj_latent(x, tid):
        un = (u[ii] - u_mean) / u_std
        T = len(zz)
        for s in range(0, T - H - 1, 5):
            sdwr, draw, dJ = score_window(zz[s:s + H + 1], un[s:s + H])
            rows.append((sdwr, draw, dJ, f))

import numpy as np
arr = np.array([(a, b, c) for a, b, c, _ in rows])
sdwr, draw, dJ = arr[:, 0], arr[:, 1], arr[:, 2]
def corr(a, b):
    a = a - a.mean(); b = b - b.mean()
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-30))
res = {
    "n_windows": int(len(rows)), "H": H,
    "corr_raw_defect_vs_dJ": corr(draw, dJ),
    "corr_DWR_vs_dJ": corr(sdwr, dJ),
    "pearson_spearman_note": "Pearson on raw magnitudes",
    "verdict": "If corr(DWR,dJ) >> corr(raw,dJ), M3 supported; if not, downgrade.",
}
print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
