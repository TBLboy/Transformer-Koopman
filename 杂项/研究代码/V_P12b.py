from pathlib import Path
import json
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
P1D = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
P2D = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\V_P12b.json")

def eig_stats(J):
    S = 0.5 * (J + J.T); e = np.linalg.eigvalsh(S)
    return float(e[0]), float(e[-1])

def local_fit_full(phi, u, d, k=300, n_query=700):
    tree = cKDTree(phi)
    idx = np.linspace(0, len(phi) - 1, n_query).astype(int)
    emins, emaxs = [], []
    for i in idx:
        _, nb = tree.query(phi[i], k=k)
        X = np.hstack([np.ones((k, 1)), u[nb]])
        th, *_ = np.linalg.lstsq(X, d[nb], rcond=None)
        lo, hi = eig_stats(th[1:].T)
        emins.append(lo); emaxs.append(hi)
    emins = np.array(emins); emaxs = np.array(emaxs)
    pd = (emins > 0); nd = (emaxs < 0); mixed = ~pd & ~nd
    return {"lam_min_median": float(np.median(emins)), "lam_max_median": float(np.median(emaxs)),
            "frac_PD(both_pos)": float(pd.mean()), "frac_ND(both_neg)": float(nd.mean()),
            "frac_indefinite": float(mixed.mean())}

def ambiguity_knn(phi_u, d, k=15, n_query=500):
    tree = cKDTree(phi_u)
    idx = np.linspace(0, len(phi_u) - 1, n_query).astype(int)
    spreads = []
    for i in idx:
        _, nb = tree.query(phi_u[i], k=k)
        dd = d[nb]
        spreads.append(float(np.linalg.norm(dd.std(0))))
    base = float(np.linalg.norm(d.std(0)))
    return {"ambig_spread_median": float(np.median(spreads)), "baseline_spread": base,
            "ambig_over_baseline": float(np.median(spreads) / base)}

def corr_sign(u, d):
    C = np.corrcoef(np.hstack([u, d]).T)[:u.shape[1], u.shape[1]:]
    return C.tolist()

res = {}

# ---- P1 ----
z1 = np.load(P1D / "train.npz")
x1 = z1["x"].astype(float); u1 = z1["u"].astype(float); t1 = z1["t"].astype(float); tid1 = z1["trajectory_id"]
D1, U1, PHI1 = [], [], []
for t in np.unique(tid1):
    m = np.where(tid1 == t)[0]
    if len(m) < 5: continue
    tt = t1[m]; xx = x1[m]; uu = u1[m]
    o = np.argsort(tt); tt = tt[o]; xx = xx[o]; uu = uu[o]
    dtv = np.diff(tt); pos = dtv[dtv > 0]
    if len(pos) == 0: continue
    dtv = np.where(dtv <= 0, np.median(pos), dtv)
    acc = (xx[1:, 1:6:2] - xx[:-1, 1:6:2]) / dtv[:, None]
    D1.append(acc); U1.append(uu[:-1]); PHI1.append(np.hstack([xx[:-1, 0:6:2], xx[:-1, 1:6:2]]))
D1 = np.concatenate(D1); U1 = np.concatenate(U1); PHI1 = np.concatenate(PHI1)
res["P1"] = {"n": int(len(D1)), "corr_u_d": corr_sign(U1, D1),
             "local_eig": local_fit_full(PHI1, U1, D1, k=400, n_query=700),
             "ambiguity": ambiguity_knn(np.hstack([PHI1, U1]), D1, k=15, n_query=500)}

# ---- P2 ----
z2 = np.load(P2D / "train.npz")
x2 = z2["x"].astype(float); u2 = z2["u"].astype(float); tid2 = z2["trajectory_id"]
D2, U2, PHI2 = [], [], []
L = 3
for t in np.unique(tid2):
    m = np.where(tid2 == t)[0]
    if len(m) < L + 2: continue
    xx = x2[m]; uu = u2[m]
    for kk in range(L, len(xx) - 1):
        D2.append(xx[kk + 1] - xx[kk]); U2.append(uu[kk])
        ctx = [xx[kk - j] for j in range(L)] + [uu[kk - j] for j in range(1, L + 1) if kk - j >= 0]
        PHI2.append(np.concatenate(ctx))
D2 = np.array(D2); U2 = np.array(U2); PHI2 = np.array(PHI2)
res["P2"] = {"n": int(len(D2)), "corr_u_d": corr_sign(U2, D2),
             "local_eig": local_fit_full(PHI2, U2, D2, k=300, n_query=700),
             "ambiguity": ambiguity_knn(np.hstack([PHI2, U2]), D2, k=15, n_query=500)}

print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
