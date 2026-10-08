from pathlib import Path
import json
import numpy as np
from scipy.spatial import cKDTree
import torch, torch.nn as nn, torch.nn.functional as F

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
P1D = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
P2D = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\V_T6.json")

S0 = np.diag([-1.0, 1.0])

def inertia(J, tol=1e-9):
    e = np.linalg.eigvalsh(0.5 * (J + J.T))
    n0 = int((np.abs(e) <= tol).sum())
    return int((e > tol).sum()), int((e < -tol).sum()), n0

def stats_vec(x):
    x = np.asarray(x)
    return {"median": float(np.median(x)), "q05": float(np.quantile(x, 0.05)),
            "q95": float(np.quantile(x, 0.95)), "frac_pos": float((x > 0).mean()),
            "frac_neg": float((x < 0).mean())}

def local_analysis(phi, u, d, k=300, n_query=900):
    tree = cKDTree(phi)
    idx = np.linspace(0, len(phi) - 1, n_query).astype(int)
    res = {"pd_symJ": 0, "pd_symS0J": 0, "pd_symScJ": 0, "pd_symSrJ": 0, "n": 0}
    inert = {"(2,0,0)": 0, "(1,1,0)": 0, "(0,2,0)": 0, "other": 0}
    dets, angs, scales = [], [], []
    for i in idx:
        _, nb = tree.query(phi[i], k=k)
        X = np.hstack([np.ones((k, 1)), u[nb]])
        th, *_ = np.linalg.lstsq(X, d[nb], rcond=None)
        J = th[1:].T
        sJ = 0.5 * (J + J.T); eJ = np.linalg.eigvalsh(sJ)
        scale = np.linalg.norm(sJ) + 1e-15
        res["pd_symJ"] += int(eJ[0] > 1e-6 * scale)
        # one-sided S0 = diag(-1,1)
        sS = 0.5 * (S0 @ J + J.T @ S0); eS = np.linalg.eigvalsh(sS)
        res["pd_symS0J"] += int(eS[0] > 1e-6 * scale)
        # context-adaptive S(c) = diag(sign(diag(sym J)))  (per-context)
        sgn = np.sign(np.diag(sJ)); sgn[sgn == 0] = 1.0
        Sc = np.diag(sgn)
        sSc = 0.5 * (Sc @ J + J.T @ Sc); eSc = np.linalg.eigvalsh(sSc)
        res["pd_symScJ"] += int(eSc[0] > 1e-6 * scale)
        # randomized fixed S (average sign of mean sym J) - done later; here use diag(-1,1)^1 sign flip on largest-|diag|
        # eigenframe angle
        w, V = np.linalg.eigh(sJ)
        angs.append(np.arctan2(V[1, -1], V[0, -1]))
        dets.append(float(np.linalg.det(J)))
        scales.append(float(np.linalg.svd(J, compute_uv=False)[-1]))
        it = inertia(sJ, tol=1e-6 * scale)
        key = f"({it[0]},{it[1]},{it[2]})"
        inert[key if key in inert else "other"] += 1
        res["n"] += 1
    for kk in ("pd_symJ", "pd_symS0J", "pd_symScJ"):
        res[kk] = res[kk] / res["n"]
    # circular std of eigenframe angle (double angle trick)
    a = np.array(angs); C = np.mean(np.cos(2 * a)); S = np.mean(np.sin(2 * a))
    res["eigenframe_circ_std_deg"] = float(np.degrees(np.sqrt(-2 * np.log(np.hypot(C, S) + 1e-12)) / 2))
    res["inertia_distribution"] = inert
    res["det_sign"] = {"frac_pos": float(np.mean(np.array(dets) > 0)),
                       "frac_neg": float(np.mean(np.array(dets) < 0))}
    res["sigma_min_J"] = stats_vec(scales)
    return res

def build_P2():
    z2 = np.load(P2D / "train.npz")
    x2 = z2["x"].astype(float); u2 = z2["u"].astype(float); tid2 = z2["trajectory_id"]
    D, U, PHI = [], [], []
    L = 3
    for t in np.unique(tid2):
        m = np.where(tid2 == t)[0]
        if len(m) < L + 2: continue
        xx = x2[m]; uu = u2[m]
        for kk in range(L, len(xx) - 1):
            D.append(xx[kk + 1] - xx[kk]); U.append(uu[kk])
            ctx = [xx[kk - j] for j in range(L)] + [uu[kk - j] for j in range(1, L + 1) if kk - j >= 0]
            PHI.append(np.concatenate(ctx))
    return np.array(PHI), np.array(U), np.array(D)

res = {}
PHI2, U2, D2 = build_P2()
res["P2"] = local_analysis(PHI2, U2, D2, k=300, n_query=900)

# ---- T6-3 potential-gradient model (integrability cost) ----
torch.manual_seed(0)
Pc = torch.tensor(PHI2, dtype=torch.float32); Uc = torch.tensor(U2, dtype=torch.float32); Dc = torch.tensor(D2, dtype=torch.float32)
n = len(Pc); perm = torch.randperm(n); ntr = int(0.85 * n)
tri, vai = perm[:ntr], perm[ntr:]
cu = torch.cat([Pc, Uc], 1); du = Pc.shape[1]; uc_dim = Uc.shape[1]

class Pot(nn.Module):
    def __init__(s, h=64):
        super().__init__(); s.f = nn.Sequential(nn.Linear(cu.shape[1], h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, 1))
    def forward(s, c, u): return s.f(torch.cat([c, u], 1)).squeeze(-1)

class Vec(nn.Module):
    def __init__(s, h=64):
        super().__init__(); s.f = nn.Sequential(nn.Linear(cu.shape[1], h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, uc_dim))
    def forward(s, c, u): return s.f(torch.cat([c, u], 1))

def train_pot(epochs=4000, lr=2e-3):
    m = Pot(); opt = torch.optim.Adam(m.parameters(), lr=lr)
    for _ in range(epochs):
        opt.zero_grad()
        c = Pc[tri].clone().requires_grad_(True); u = Uc[tri].clone().requires_grad_(True)
        phi = m(c, u).sum()
        g = torch.autograd.grad(phi, u, create_graph=True)[0]
        F.mse_loss(g, Dc[tri]).backward(); opt.step()
    c = Pc[vai].clone().requires_grad_(True); u = Uc[vai].clone().requires_grad_(True)
    g = torch.autograd.grad(m(c, u).sum(), u)[0]
    with torch.no_grad():
        rmse = float(torch.sqrt(F.mse_loss(g, Dc[vai])))
    return rmse

def train_vec(epochs=4000, lr=2e-3):
    m = Vec(); opt = torch.optim.Adam(m.parameters(), lr=lr)
    for _ in range(epochs):
        opt.zero_grad(); F.mse_loss(m(Pc[tri], Uc[tri]), Dc[tri]).backward(); opt.step()
    with torch.no_grad():
        rmse = float(torch.sqrt(F.mse_loss(m(Pc[vai], Uc[vai]), Dc[vai])))
    return rmse

res["T6_3_potential_vs_vector_val_rmse"] = {"potential_gradient": train_pot(), "unrestricted_vector": train_vec()}

print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
