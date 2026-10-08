from pathlib import Path
import json, math
import numpy as np
import torch
import torch.nn as nn
from scipy.linalg import solve_discrete_are

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
CKPT = ROOT / "训练代码" / "deploy" / "algorithms" / "tk_assets" / "model_assets" / "platform2_full_model.pth"
DATA = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\N_P2_policy_null.json")

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
        x_t = xh[:, -1, :]; b = xh.shape[0]
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
enc.load_state_dict(enc_sd); enc.eval()

x_mean = np.asarray(norm.get("x_mean", np.zeros(n)), float).reshape(1, -1)
x_std = np.asarray(norm.get("x_std", np.ones(n)), float).reshape(1, -1)
P = cfg["encoder"]["history_length"]

# LQR gain on deployed (A,B), Q=I, R=I
Pare = solve_discrete_are(A, B, np.eye(n), np.eye(m))
K = np.linalg.solve(np.eye(m) + B.T @ Pare @ B, B.T @ Pare @ A)  # m x n
svK = np.linalg.svd(K, compute_uv=False)
rankK = int(np.sum(svK > 1e-8 * svK[0]))
sigma_max = float(svK[0])
# projectors on latent
Kr = np.linalg.pinv(K) @ K          # row space projector (policy-sensitive)
Proj_row = Kr
Proj_null = np.eye(n) - Kr          # ker(K) projector (policy-null)

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
        hist = np.stack([xn[k - P + 1:k + 1] for k in range(P - 1, len(xn))], axis=0)
        with torch.no_grad():
            z = enc(torch.tensor(hist, dtype=torch.float32)).numpy()
        zs.append(z)
    return zs

def stats(a):
    a = np.asarray(a)
    return {"mean": float(a.mean()), "median": float(np.median(a)), "p95": float(np.percentile(a, 95))}

results = {"config": {"n_latent": n, "m_input": m, "rank_K": rankK,
                      "policy_null_dim": n - rankK, "sigma_K": [float(s) for s in svK],
                      "note": "LQR Q=I,R=I on deployed (A,B); policy-null = ker(K)"}}

for f in ["train.npz", "val.npz"]:
    z = np.load(DATA / f)
    x, tid = z["x"].astype(float), z["trajectory_id"]
    zs = traj_windows(x, tid)
    fr_row, fr_null, rat = [], [], []       # per-sample policy energy fractions + sensitivity
    horizon_A, horizon_cl = {t: [] for t in range(6)}, {t: [] for t in range(6)}
    Acl = A - B @ K
    for zz in zs:
        d = zz[1:] - zz[:-1] @ A.T          # (T, n) latent increment
        r = d @ ImP.T                        # reachability defect (row)
        nd2 = np.sum(d * d, axis=1) + 1e-30
        r2 = np.sum(r * r, axis=1)
        # policy projections of the *increment* and of the *defect*
        erow = np.sum((r @ Proj_row.T) * r, axis=1) / (r2 + 1e-30)
        enull = np.sum((r @ Proj_null.T) * r, axis=1) / (r2 + 1e-30)
        fr_row.append(erow); fr_null.append(enull)
        # policy sensitivity of defect: ||K d|| / (sigma_max ||d||)
        rat.append(np.linalg.norm(d @ K.T, axis=1) / (sigma_max * np.linalg.norm(d, axis=1) + 1e-30))
        # temporal: does one-step defect stay policy-null over horizon? use r rows
        for t in range(6):
            At = np.linalg.matrix_power(A, t)
            Aclt = np.linalg.matrix_power(Acl, t)
            horizon_A[t].append(np.linalg.norm((At @ r.T).T @ K.T, axis=1) / (sigma_max * np.linalg.norm(r, axis=1) + 1e-30))
            horizon_cl[t].append(np.linalg.norm((Aclt @ r.T).T @ K.T, axis=1) / (sigma_max * np.linalg.norm(r, axis=1) + 1e-30))
    fr_row = np.concatenate(fr_row); fr_null = np.concatenate(fr_null); rat = np.concatenate(rat)
    results[f] = {
        "defect_energy_frac_policy_relevant(row K)": stats(fr_row),
        "defect_energy_frac_policy_null(ker K)": stats(fr_null),
        "defect_policy_sensitivity_normKd_over_sigmax_d": stats(rat),
        "horizon_policy_sensitivity_openloop_A^t": {str(t): stats(np.concatenate(horizon_A[t])) for t in range(6)},
        "horizon_policy_sensitivity_closedloop_(A-BK)^t": {str(t): stats(np.concatenate(horizon_cl[t])) for t in range(6)},
    }

results["verdict"] = ("If defect energy is dominated by ker(K) and sensitivity<<1, N1/N2 premise holds (defect is policy-null). "
                      "If open/closed-loop horizon sensitivity grows, ker(K) is NOT invariant under A -> one-step policy-null is not trajectory policy-null.")
print(json.dumps(results, indent=2))
OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
