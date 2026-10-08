from pathlib import Path
import json
import math
import numpy as np
import torch
import torch.nn as nn

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
CKPT = ROOT / "训练代码" / "deploy" / "algorithms" / "tk_assets" / "model_assets" / "platform2_full_model.pth"
DATA = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\test_r1_multistep.json")

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div); pe[:, 1::2] = torch.cos(position * div)
        self.register_buffer("pe", pe.unsqueeze(0))
    def forward(self, x): return x + self.pe[:, :x.size(1), :]

class Enc(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.P = cfg["encoder"]["history_length"]; self.p = cfg["encoder"]["patch_length"]
        self.n = cfg["data"]["state_dim"]; self.d = cfg["encoder"]["latent_dim"]
        self.d_model = cfg["encoder"]["d_model"]; self.num_patches = self.P // self.p
        self.patch_embedding = nn.Linear(self.p * self.n, self.d_model)
        self.positional_encoding = PositionalEncoding(self.d_model)
        layer = nn.TransformerEncoderLayer(d_model=self.d_model, nhead=cfg["encoder"]["n_heads"],
                                           dim_feedforward=cfg["encoder"]["d_ff"],
                                           dropout=cfg["encoder"].get("dropout", 0.1), batch_first=True)
        self.transformer = nn.TransformerEncoder(layer, num_layers=cfg["encoder"]["n_layers"])
        self.projection = nn.Linear(self.d_model, self.d - self.n)
    def forward(self, xh):
        b = xh.shape[0]
        patches = xh.reshape(b, self.num_patches, self.p, self.n).reshape(b, self.num_patches, self.p * self.n)
        e = self.positional_encoding(self.patch_embedding(patches))
        return torch.cat([xh[:, -1, :], self.projection(torch.mean(self.transformer(e), dim=1))], dim=1)

o = torch.load(CKPT, map_location="cpu", weights_only=False)
cfg = o["config"]; norm = o["normalization"]
A = np.asarray(o["koopman_A"], float); B = np.asarray(o["koopman_B"], float)
n = A.shape[0]
enc = Enc(cfg)
enc.load_state_dict({k[len("encoder."):]: v for k, v in o["model_state_dict"].items() if k.startswith("encoder.")})
enc.eval()
x_mean = np.asarray(norm["x_mean"], float).reshape(1, -1); x_std = np.asarray(norm["x_std"], float).reshape(1, -1)
u_mean = np.asarray(norm["u_mean"], float).reshape(1, -1); u_std = np.asarray(norm["u_std"], float).reshape(1, -1)
P = cfg["encoder"]["history_length"]

def proj_onto(cols):
    Q, _ = np.linalg.qr(cols)
    return Q @ Q.T

def reach_basis(H):
    return np.concatenate([np.linalg.matrix_power(A, i) @ B for i in range(H)], axis=1)

res = {}
for f in ["train.npz", "val.npz"]:
    z = np.load(DATA / f)
    x, u, tid = z["x"].astype(float), z["u"].astype(float), z["trajectory_id"]
    xn = (x - x_mean) / x_std; un = (u - u_mean) / u_std
    for H in [1, 2, 3, 4, 6, 8, 10]:
        if H > n:
            continue
        Pr = proj_onto(reach_basis(H))
        AbsH = np.linalg.matrix_power(A, H)
        defs, ds = [], []
        for t in np.unique(tid):
            idx = np.where(tid == t)[0]
            if len(idx) < P + H:
                continue
            hist = np.stack([xn[idx[k] - P + 1:idx[k] + 1] for k in range(P - 1, len(idx) - H)], axis=0)
            with torch.no_grad():
                zz = enc(torch.tensor(hist, dtype=torch.float32)).numpy()
            zt = np.stack([xn[idx[k]] for k in range(P - 1, len(idx) - H)], axis=0)
            zH = np.stack([xn[idx[k + H]] for k in range(P - 1, len(idx) - H)], axis=0)
            # NOTE: zz approximates z at history end; use zz as z_k and zz shifted H as z_{k+H}
            # shift within same trajectory using encoder again for z_{k+H}
            histH = np.stack([xn[idx[k + H] - P + 1:idx[k + H] + 1] for k in range(P - 1, len(idx) - H)], axis=0)
            with torch.no_grad():
                zzH = enc(torch.tensor(histH, dtype=torch.float32)).numpy()
            d = zzH - zz @ AbsH.T
            r = d @ (np.eye(n) - Pr).T
            defs.append(np.linalg.norm(r, axis=1)); ds.append(np.linalg.norm(d, axis=1))
        defs = np.concatenate(defs); ds = np.concatenate(ds)
        res.setdefault(f, {})["H=%d" % H] = {
            "mean_abs_increment": float(ds.mean()),
            "mean_abs_defect": float(defs.mean()),
            "median_rel_defect": float(np.median(defs / (ds + 1e-12))),
            "mean_rel_defect": float(np.mean(defs / (ds + 1e-12))),
        }

print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
