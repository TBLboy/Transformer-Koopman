from pathlib import Path
import json, math
import numpy as np
import torch
import torch.nn as nn
from scipy.linalg import solve_discrete_are, null_space

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
CKPT = ROOT / "训练代码" / "deploy" / "algorithms" / "tk_assets" / "model_assets" / "platform2_full_model.pth"
DATA = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\D_P2.json")

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

def orth(A, tol=1e-9):
    if A.size == 0: return A
    U, s, _ = np.linalg.svd(A, full_matrices=False)
    return U[:, s > tol]

def proj(B):
    if B.size == 0: return np.zeros((B.shape[0], B.shape[0]))
    return B @ np.linalg.pinv(B)

def intersect(B1, B2, tol=1e-9):
    if B1.size == 0 or B2.size == 0:
        return np.zeros((B1.shape[0] if B1.size else B2.shape[0], 0))
    N = null_space(np.hstack([B1, -B2]))
    basis = B1 @ N[:B1.shape[1], :]
    if basis.size == 0: return np.zeros((B1.shape[0], 0))
    U, s, _ = np.linalg.svd(basis, full_matrices=False)
    return U[:, s > tol]

o = torch.load(CKPT, map_location="cpu", weights_only=False)
cfg = o["config"]; norm = o["normalization"]
A = np.asarray(o["koopman_A"], float); B = np.asarray(o["koopman_B"], float)
n, m = B.shape
out_dim = cfg["data"]["state_dim"]
C = np.hstack([np.eye(out_dim), np.zeros((out_dim, n - out_dim))])

enc = PatchTSTEncoder(cfg)
enc_sd = {k[len("encoder."):]: v for k, v in o["model_state_dict"].items() if k.startswith("encoder.")}
enc.load_state_dict(enc_sd); enc.eval()
x_mean = np.asarray(norm.get("x_mean", np.zeros(n)), float).reshape(1, -1)
x_std = np.asarray(norm.get("x_std", np.ones(n)), float).reshape(1, -1)
u_mean = np.asarray(norm.get("u_mean", np.zeros(m)), float).reshape(1, -1)
u_std = np.asarray(norm.get("u_std", np.ones(m)), float).reshape(1, -1)
P = cfg["encoder"]["history_length"]

# ---- D1: maximal (A,B)-controlled invariant subspace inside ker C ----
kerC = orth(null_space(C))
imB = orth(B)
V = kerC.copy()
conv = []
for _ in range(50):
    Vplus = orth(np.hstack([V, imB]))
    Pplus = proj(Vplus)
    pre = null_space((np.eye(n) - Pplus) @ A)
    Vnew = intersect(V, orth(pre))
    conv.append(int(Vnew.shape[1]))
    if Vnew.shape[1] == V.shape[1]:
        V = Vnew; break
    V = Vnew
Vstar = V
P_V = proj(Vstar)
benign_basis = orth(np.hstack([imB, Vstar]))
Pben = proj(benign_basis)

# ---- D2: task-family sensitivity envelope ----
rng = np.random.default_rng(0)
rows, rank_curve = [], []
for k in range(200):
    Q = np.diag(rng.uniform(0.1, 10.0, n)); R = np.diag(rng.uniform(0.1, 10.0, m))
    try:
        Pq = solve_discrete_are(A, B, Q, R)
        K = np.linalg.solve(R + B.T @ Pq @ B, B.T @ Pq @ A)
        rows.append(K); rank_curve.append(int(np.linalg.matrix_rank(np.vstack(rows), tol=1e-6)))
    except Exception:
        pass

def traj_windows(x, tid):
    zs, idxs = [], []
    for t in np.unique(tid):
        xi = x[tid == t]; ii = np.where(tid == t)[0]
        if len(xi) < P + 1: continue
        xn = (xi - x_mean) / x_std
        hist = np.stack([xn[j - P + 1:j + 1] for j in range(P - 1, len(xn))], axis=0)
        with torch.no_grad():
            z = enc(torch.tensor(hist, dtype=torch.float32)).numpy()
        zs.append(z); idxs.append(ii[P - 1:])
    return zs, idxs

res = {"D1": {"Vstar_dim": int(Vstar.shape[1]), "kerC_dim": int(kerC.shape[1]),
              "imB_dim": int(imB.shape[1]), "benign_dim": int(benign_basis.shape[1]),
              "convergence_dims": conv},
       "D2": {"rank_curve_at_1_10_50_200": [rank_curve[0], rank_curve[min(9, len(rank_curve)-1)],
                                             rank_curve[min(49, len(rank_curve)-1)], rank_curve[-1]],
              "full_rank_is": n}}

for f in ["train.npz", "val.npz"]:
    z = np.load(DATA / f)
    x, u, tid = z["x"].astype(float), z["u"].astype(float), z["trajectory_id"]
    zs, idxs = traj_windows(x, tid)
    rhoV, rhoM, rhoH = [], [], []
    all_def, all_H = [], []
    for zz, ii in zip(zs, idxs):
        if len(zz) < 2: continue
        d = zz[1:] - zz[:-1] @ A.T
        un = (u[ii[:-1]] - u_mean) / u_std
        d = d - un @ B.T
        e2 = np.sum(d * d, axis=1) + 1e-30
        rhoV.append(np.sum((d @ P_V.T) * d, axis=1) / e2)
        rhoM.append(np.sum((d @ proj(imB).T) * d, axis=1) / e2)
        dH = d - d @ Pben.T
        rhoH.append(np.sum(dH * dH, axis=1) / e2)
        all_def.append(np.linalg.norm(d, axis=1)); all_H.append(np.linalg.norm(dH, axis=1))
    rhoV = np.concatenate(rhoV); rhoM = np.concatenate(rhoM); rhoH = np.concatenate(rhoH)
    all_def = np.concatenate(all_def); all_H = np.concatenate(all_H)
    res[f] = {
        "n": int(len(rhoV)),
        "D1_rho_V_outputnulling": {"mean": float(rhoV.mean()), "median": float(np.median(rhoV))},
        "rho_matched_imB": {"mean": float(rhoM.mean()), "median": float(np.median(rhoM))},
        "rho_harmful_complement_benign": {"mean": float(rhoH.mean()), "median": float(np.median(rhoH))},
        "D3_q95_full_defect": float(np.percentile(all_def, 95)),
        "D3_q95_harmful_defect": float(np.percentile(all_H, 95)),
        "D3_ratio_q95_harmful_over_full": float(np.percentile(all_H, 95) / (np.percentile(all_def, 95) + 1e-30)),
        "D5_u_abs_max": float(np.abs(u).max()),
    }

res["verdict"] = ("D1: rho_V>0.5 -> M1 strong; <0.1 -> downgrade shielding. "
                  "D2: rank saturating <<10 -> task-family quotient nontrivial; ->10 -> M9 kill. "
                  "D3: q95_harmful<<q95_full -> M2 value. D5: |u| far below 300 -> M4 kill.")
print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
