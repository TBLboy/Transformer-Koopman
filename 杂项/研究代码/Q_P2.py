from pathlib import Path
import json, math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
CKPT = ROOT / "训练代码" / "deploy" / "algorithms" / "tk_assets" / "model_assets" / "platform2_full_model.pth"
DATA = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\Q_P2.json")

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
enc = PatchTSTEncoder(cfg)
enc.load_state_dict({k[len("encoder."):]: v for k, v in o["model_state_dict"].items() if k.startswith("encoder.")})
enc.eval()
x_mean = np.asarray(norm.get("x_mean", np.zeros(cfg["data"]["state_dim"])), float).reshape(1, -1)
x_std = np.asarray(norm.get("x_std", np.ones(cfg["data"]["state_dim"])), float).reshape(1, -1)
u_mean = np.asarray(norm.get("u_mean", np.zeros(cfg["data"]["control_dim"])), float).reshape(1, -1)
u_std = np.asarray(norm.get("u_std", np.ones(cfg["data"]["control_dim"])), float).reshape(1, -1)
print("x_mean", x_mean, "u_mean", u_mean, "u_std", u_std)
P = cfg["encoder"]["history_length"]
n = cfg["encoder"]["latent_dim"]; m = cfg["data"]["control_dim"]

def latents(split):
    z = np.load(DATA / f"{split}.npz")
    x, u, tid = z["x"].astype(float), z["u"].astype(float), z["trajectory_id"]
    trs = []
    for t in np.unique(tid):
        xi = x[tid == t]; ui = u[tid == t]
        if len(xi) < P + 2: continue
        xn = (xi - x_mean) / x_std; un = (ui - u_mean) / u_std
        hist = np.stack([xn[j - P + 1:j + 1] for j in range(P - 1, len(xn))], axis=0)
        with torch.no_grad():
            zz = enc(torch.tensor(hist, dtype=torch.float32)).numpy()
        uu = un[P - 1:]
        trs.append((zz, uu))
    return trs

def stack(trs):
    Z, U, Zp = [], [], []
    for zz, uu in trs:
        Z.append(zz[:-1]); U.append(uu[:-1]); Zp.append(zz[1:])
    return np.concatenate(Z), np.concatenate(U), np.concatenate(Zp)

tr = stack(latents("train")); va = stack(latents("val"))
Ztr, Utr, Zptr = tr; Zva, Uva, Zpva = va
print("train", Ztr.shape, "val", Zva.shape)

def effrank(cov_ev, thresh):
    ev = np.sort(cov_ev)[::-1]; evn = ev / ev.sum()
    return int(np.searchsorted(np.cumsum(evn), thresh) + 1)

# ---------- baseline (alpha=0) LS ----------
Xtr = np.hstack([Ztr, Utr]); Xva = np.hstack([Zva, Uva])
th0, *_ = np.linalg.lstsq(Xtr, Zptr, rcond=None)
R0tr = Zptr - Xtr @ th0; R0va = Zpva - Xva @ th0
rmse0_tr = float(np.sqrt((R0tr**2).mean())); rmse0_va = float(np.sqrt((R0va**2).mean()))
ev0 = np.linalg.eigvalsh(np.cov(R0tr.T))
res = {"baseline": {"rmse_train": round(rmse0_tr, 6), "rmse_val": round(rmse0_va, 6),
                    "resid_eig_rank_90": effrank(ev0, 0.90), "resid_eig_rank_99": effrank(ev0, 0.99),
                    "resid_eig_norm": [round(float(v), 5) for v in (np.sort(ev0)[::-1] / ev0.sum())]}}

# ---------- T4-1: linear prefeedback invariance (Q0) ----------
rng = np.random.default_rng(0)
norms = []
for i in range(20):
    K = rng.normal(0, 1, size=(m, n))
    Vtr = Utr - Ztr @ K.T
    th, *_ = np.linalg.lstsq(np.hstack([Ztr, Vtr]), Zptr, rcond=None)
    Rk = Zptr - np.hstack([Ztr, Vtr]) @ th
    norms.append(float(np.sqrt((Rk**2).mean())))
res["T4_1_linear_prefeedback"] = {
    "Q0_prediction": "residual norm invariant to linear prefeedback",
    "baseline_rmse_train": round(rmse0_tr, 6),
    "random_K_rmse_train_mean": round(float(np.mean(norms)), 6),
    "random_K_rmse_train_std": round(float(np.std(norms)), 9),
    "max_abs_dev_from_baseline": round(float(np.max(np.abs(np.array(norms) - rmse0_tr))), 9),
}

# ---------- torch joint-fit helpers ----------
torch.manual_seed(0)
Zt = torch.tensor(Ztr, dtype=torch.float32); Ut = torch.tensor(Utr, dtype=torch.float32); Zpt = torch.tensor(Zptr, dtype=torch.float32)
Zv = torch.tensor(Zva, dtype=torch.float32); Uv = torch.tensor(Uva, dtype=torch.float32); Zpv = torch.tensor(Zpva, dtype=torch.float32)
Xtr_full = torch.cat([Zt, Ut], 1); th_init = torch.tensor(th0, dtype=torch.float32)

def fit_q1(alpha_fn, params, epochs=3000, lr=3e-3):
    A = nn.Parameter(th_init[:n].clone()); B = nn.Parameter(th_init[n:].clone())
    opt = torch.optim.Adam(list(params) + [A, B], lr=lr)
    for _ in range(epochs):
        opt.zero_grad()
        alpha = alpha_fn(Zt)
        pred = Zt @ A + (Ut - alpha) @ B
        loss = F.mse_loss(pred, Zpt)
        loss.backward(); opt.step()
    with torch.no_grad():
        alpha_tr = alpha_fn(Zt); pred_tr = Zt @ A + (Ut - alpha_tr) @ B
        alpha_va = alpha_fn(Zv); pred_va = Zv @ A + (Uv - alpha_va) @ B
        Rtr = (Zpt - pred_tr).numpy(); Rva = (Zpv - pred_va).numpy()
    ev = np.linalg.eigvalsh(np.cov(Rtr.T))
    return {"rmse_train": float(np.sqrt((Rtr**2).mean())), "rmse_val": float(np.sqrt((Rva**2).mean())),
            "resid_rank_90": effrank(ev, 0.90), "resid_rank_99": effrank(ev, 0.99),
            "alpha_mean_abs_train": float(alpha_tr.abs().mean()), "Rtr": Rtr, "Rva": Rva}

# Q1a: linear alpha = Kz (should match baseline)
Klin = nn.Linear(n, m)
res_lin = fit_q1(lambda Z: Klin(Z), [Klin.weight, Klin.bias])
# Q1b: quadratic alpha on z
class QuadA(nn.Module):
    def __init__(s): super().__init__(); s.W = nn.Linear(n + n*n, m, bias=True)
    def forward(s, Z):
        zz = torch.cat([Z, (Z.unsqueeze(2) * Z.unsqueeze(1)).reshape(Z.shape[0], -1)], 1)
        return s.W(zz)
quad = QuadA()
res_quad = fit_q1(lambda Z: quad(Z), [quad.W.weight, quad.W.bias], epochs=4000)
# Q1c: small MLP alpha
class MLP(nn.Module):
    def __init__(s, h=32): super().__init__(); s.f = nn.Sequential(nn.Linear(n, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, m))
    def forward(s, Z): return s.f(Z)
mlp = MLP()
res_mlp = fit_q1(lambda Z: mlp(Z), list(mlp.parameters()), epochs=4000)

# Q1d: FULL nonlinear drift f(z): z+ = A z + B u + f(z)  (rank-unconstrained channel)
class FullF(nn.Module):
    def __init__(s, h=32): super().__init__(); s.f = nn.Sequential(nn.Linear(n, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, n))
    def forward(s, Z): return s.f(Z)
ff = FullF()
def fit_full(fn, params, epochs=4000, lr=3e-3):
    A = nn.Parameter(th_init[:n].clone()); B = nn.Parameter(th_init[n:].clone())
    opt = torch.optim.Adam(list(params) + [A, B], lr=lr)
    for _ in range(epochs):
        opt.zero_grad()
        pred = Zt @ A + Ut @ B + fn(Zt)
        F.mse_loss(pred, Zpt).backward(); opt.step()
    with torch.no_grad():
        Rtr = (Zpt - (Zt @ A + Ut @ B + fn(Zt))).numpy()
        Rva = (Zpv - (Zv @ A + Uv @ B + fn(Zv))).numpy()
    ev = np.linalg.eigvalsh(np.cov(Rtr.T))
    return {"rmse_train": float(np.sqrt((Rtr**2).mean())), "rmse_val": float(np.sqrt((Rva**2).mean())),
            "resid_rank_90": effrank(ev, 0.90), "resid_rank_99": effrank(ev, 0.99), "Rtr": Rtr, "Rva": Rva}
res_full = fit_full(lambda Z: ff(Z), list(ff.parameters()))

res["T4_2_feedback_closure"] = {
    "linear_alpha_Kz": {k: round(v, 6) for k, v in res_lin.items() if k not in ("Rtr", "Rva")},
    "quadratic_alpha": {k: round(v, 6) for k, v in res_quad.items() if k not in ("Rtr", "Rva")},
    "mlp_alpha_rank_m": {k: round(v, 6) for k, v in res_mlp.items() if k not in ("Rtr", "Rva")},
    "full_nonlinear_drift_rank_n": {k: round(v, 6) for k, v in res_full.items() if k not in ("Rtr", "Rva")},
    "note": "alpha must be rank<=m=2 (prefeedback); full drift is the unconstrained upper bound (rank<=n=10)",
}

# ---------- T4-3: residual block-Hankel spectrum (baseline residual) ----------
def hankel_spectrum(Rtr, L=10):
    # Rtr: (N,10) is not sequential-ordered across traj; recompute per traj instead
    return None
# rebuild per-traj residuals
def per_traj_residual(split):
    out = []
    for zz, uu in latents(split):
        r = zz[1:] - np.hstack([zz[:-1], uu[:-1]]) @ th0
        out.append(r)
    return out
rt_tr = per_traj_residual("train"); rt_va = per_traj_residual("val")
def block_hankel(rs, L=10):
    cols = []
    for r in rs:
        T = len(r)
        if T < L: continue
        H = np.stack([r[i:i + T - L + 1] for i in range(L)], axis=0)  # (L*n, T-L+1)
        cols.append(H.reshape(L * r.shape[1], -1))
    return np.concatenate(cols, axis=1)
Htr = block_hankel(rt_tr); Hva = block_hankel(rt_va)
sv_tr = np.linalg.svd(Htr, compute_uv=False); sv_va = np.linalg.svd(Hva, compute_uv=False)
def order_from_sv(sv, thresh):
    e = sv**2; e = e / e.sum(); return int(np.searchsorted(np.cumsum(e), thresh) + 1)
res["T4_3_residual_hankel"] = {
    "L": 10,
    "hankel_rank_90_train": order_from_sv(sv_tr, 0.90), "hankel_rank_99_train": order_from_sv(sv_tr, 0.99),
    "hankel_rank_90_val": order_from_sv(sv_va, 0.90), "hankel_rank_99_val": order_from_sv(sv_va, 0.99),
    "top10_sv_norm_train": [round(float(v), 5) for v in (sv_tr[:10] / sv_tr[0])],
    "note": "if covariance rank low but Hankel rank high -> instantaneous low-rank but NOT low-order dynamics",
}

# ---------- T4-4: obstruction subspace reproducibility ----------
def traj_pca_basis(split, r=4):
    bases = []
    for rr in per_traj_residual(split):
        if len(rr) < r + 1: continue
        U, S, Vt = np.linalg.svd(rr - rr.mean(0), full_matrices=False)
        bases.append(Vt[:r].T)  # (n, r)
    return bases
bases = traj_pca_basis("train", 4)
angs = []
for i in range(len(bases)):
    for j in range(i + 1, len(bases)):
        s = np.linalg.svd(bases[i].T @ bases[j], compute_uv=False)
        angs.append(np.arccos(np.clip(s, -1, 1)))
angs = np.array(angs)  # (pairs, r)
res["T4_4_obstruction_reproducibility"] = {
    "n_trajectories": len(bases), "r": 4, "n_pairs": len(angs),
    "principal_angle_mean_deg": [round(float(np.degrees(angs[:, k].mean())), 2) for k in range(4)],
    "principal_angle_max_deg": [round(float(np.degrees(angs[:, k].max())), 2) for k in range(4)],
    "note": "small angles => reproducible obstruction subspace (Q3/Q5 viable); large => artifact",
}

# ---------- T4-5: obstruction mode placement feasibility (baseline residual E) ----------
Ue, Se, Vte = np.linalg.svd(np.cov(R0tr.T), full_matrices=False)
r_use = effrank(np.linalg.eigvalsh(np.cov(R0tr.T)), 0.99)
A_hat = th0[:n].T; B_hat = th0[n:].T
E = Vte[:r_use].T  # (n, r)
def place(rho=0.5):
    best = None
    for it in range(30):
        K = torch.tensor(np.random.default_rng(it).normal(0, 0.5, (m, n)), dtype=torch.float32, requires_grad=True)
        opt = torch.optim.Adam([K], lr=5e-3)
        Et = torch.tensor(E, dtype=torch.float32); At = torch.tensor(A_hat, dtype=torch.float32); Bt = torch.tensor(B_hat, dtype=torch.float32)
        for _ in range(1500):
            opt.zero_grad()
            Acl = At - Bt @ K
            leak = torch.linalg.matrix_norm((torch.eye(n) - Et @ Et.T) @ Acl @ Et)
            AE = torch.linalg.pinv(Et) @ Acl @ Et
            rhoE = torch.linalg.eigvals(AE).abs().max()
            loss = leak + 5.0 * torch.relu(rhoE - rho) + 0.001 * torch.linalg.matrix_norm(K)**2
            loss.backward(); opt.step()
        with torch.no_grad():
            Acl = At - Bt @ K
            leak = float(torch.linalg.matrix_norm((torch.eye(n) - Et @ Et.T) @ Acl @ Et))
            AE = torch.linalg.pinv(Et) @ Acl @ Et
            rhoE = float(torch.linalg.eigvals(AE).abs().max())
            rho_cl = float(torch.linalg.eigvals(Acl).abs().max())
        if best is None or leak < best[0]: best = (leak, rhoE, rho_cl)
    return best
leak_best, rhoE_best, rho_cl_best = place()
res["T4_5_mode_placement"] = {
    "r": int(r_use), "baseline_rho_A": round(float(np.max(np.abs(np.linalg.eigvals(A_hat)))), 4),
    "optimized_leakage": round(leak_best, 5), "optimized_rho_E": round(rhoE_best, 4),
    "optimized_rho_closedloop": round(rho_cl_best, 4),
    "note": "if leakage~0 and rho_E<<1 at low task cost -> Q3 feasible; if not -> eigenstructure assign fails",
}

print(json.dumps(res, indent=2, default=str))
OUT.write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
