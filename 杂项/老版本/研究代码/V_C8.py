from pathlib import Path
import json
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
P1D = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
P2D = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\V_C8.json")
S0 = np.diag([-1.0, 1.0])

def build_P2(L=3):
    z = np.load(P2D / "train.npz")
    x = z["x"].astype(float); u = z["u"].astype(float); tid = z["trajectory_id"]
    D, U, PHI = [], [], []
    for t in np.unique(tid):
        m = np.where(tid == t)[0]
        if len(m) < L + 2: continue
        xx = x[m]; uu = u[m]
        for k in range(L, len(xx) - 1):
            D.append(xx[k + 1] - xx[k]); U.append(uu[k])
            ctx = [xx[k - j] for j in range(L)] + [uu[k - j] for j in range(1, L + 1) if k - j >= 0]
            PHI.append(np.concatenate(ctx))
    return np.array(PHI), np.array(U), np.array(D)

def build_P1():
    z = np.load(P1D / "train.npz")
    x = z["x"].astype(float); u = z["u"].astype(float); t = z["t"].astype(float); tid = z["trajectory_id"]
    D, U, PHI = [], [], []
    for tt in np.unique(tid):
        m = np.where(tid == tt)[0]
        if len(m) < 5: continue
        tt_v = t[m]; xx = x[m]; uu = u[m]
        o = np.argsort(tt_v); tt_v = tt_v[o]; xx = xx[o]; uu = uu[o]
        dt = np.diff(tt_v); pos = dt[dt > 0]
        if len(pos) == 0: continue
        dt = np.where(dt <= 0, np.median(pos), dt)
        acc = (xx[1:, 1:6:2] - xx[:-1, 1:6:2]) / dt[:, None]
        D.append(acc); U.append(uu[:-1]); PHI.append(np.hstack([xx[:-1, 0:6:2], xx[:-1, 1:6:2]]))
    return np.concatenate(PHI), np.concatenate(U), np.concatenate(D)

def local_sym_eigs(phi, u, d, rect=None, k=300, n_query=900):
    tree = cKDTree(phi)
    idx = np.linspace(0, len(phi) - 1, n_query).astype(int)
    lmins, lmaxs = [], []
    for i in idx:
        _, nb = tree.query(phi[i], k=k)
        X = np.hstack([np.ones((k, 1)), u[nb]])
        th, *_ = np.linalg.lstsq(X, d[nb], rcond=None)
        J = th[1:].T
        if rect is not None: J = rect @ J
        e = np.linalg.eigvalsh(0.5 * (J + J.T))
        lmins.append(e[0]); lmaxs.append(e[-1])
    return np.array(lmins), np.array(lmaxs)

def spectral_report(lmins, lmaxs):
    mu = float(np.quantile(lmins, 0.05)); L = float(np.quantile(lmaxs, 0.95))
    # also medians
    mu_med = float(np.median(lmins)); L_med = float(np.median(lmaxs))
    return {"mu_q05": mu, "L_q95": L, "kappa_q": L / mu if mu > 0 else None,
            "mu_median": mu_med, "L_median": L_med, "kappa_median": L_med / mu_med if mu_med > 0 else None,
            "frac_lmin_pos": float((lmins > 0).mean())}

def cheb_gains(N, mu, L):
    a = (L + mu) / 2.0; b = (L - mu) / 2.0
    return np.array([1.0 / (a + b * np.cos((2 * j - 1) * np.pi / (2 * N))) for j in range(1, N + 1)])

def worst_case_contraction(N, mu, L, mode="cheb"):
    lam = np.linspace(mu, L, 4001)
    if mode == "const":
        a = 2.0 / (L + mu); p = np.abs(1 - a * lam)
    else:
        alphas = cheb_gains(N, mu, L)
        p = np.ones_like(lam)
        for a in alphas:
            p *= np.abs(1 - a * lam)
    return float(p.max())

res = {}

# ---- P1 ----
P1 = build_P1(); lm1, lx1 = local_sym_eigs(*P1, rect=None)
res["P1"] = spectral_report(lm1, lx1)

# ---- P2 (rectified S0) ----
P2 = build_P2(); lm2, lx2 = local_sym_eigs(*P2, rect=S0)
res["P2"] = spectral_report(lm2, lx2)
res["P2_unrectified"] = spectral_report(*local_sym_eigs(*P2, rect=None))

# ---- theoretical Chebyshev vs constant ----
N = 6
res["theory_N6"] = {}
for name, r in (("P1", res["P1"]), ("P2", res["P2"])):
    mu, L = r["mu_q05"], r["L_q95"]
    if mu is None or mu <= 0: res["theory_N6"][name] = {"note": "mu<=0 -> interval invalid"}; continue
    kappa = L / mu
    q_const = (kappa - 1) / (kappa + 1)
    q_cheb = (np.sqrt(kappa) - 1) / (np.sqrt(kappa) + 1)
    res["theory_N6"][name] = {
        "kappa": kappa,
        "const_gain_1step_rate": q_const,
        "cheb_1step_equiv_rate": q_cheb,
        "const_Nstep_worst": float(q_const ** N),
        "cheb_Nstep_worst_theory": float(2 * q_cheb ** N),
        "cheb_Nstep_worst_empirical": worst_case_contraction(N, mu, L, "cheb"),
        "const_Nstep_worst_empirical": worst_case_contraction(N, mu, L, "const"),
    }

print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
