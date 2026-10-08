from pathlib import Path
import json
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
P2D = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
P1D = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\V_Z2.json")
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
        tv = t[m]; xx = x[m]; uu = u[m]; o = np.argsort(tv)
        tv = tv[o]; xx = xx[o]; uu = uu[o]
        dt = np.diff(tv); pos = dt[dt > 0]
        if len(pos) == 0: continue
        dt = np.where(dt <= 0, np.median(pos), dt)
        acc = (xx[1:, 1:6:2] - xx[:-1, 1:6:2]) / dt[:, None]
        D.append(acc); U.append(uu[:-1]); PHI.append(np.hstack([xx[:-1, 0:6:2], xx[:-1, 1:6:2]]))
    return np.concatenate(PHI), np.concatenate(U), np.concatenate(D)

def geo_median(P, iters=50):
    P = np.asarray(P); y = np.median(P, axis=0)
    for _ in range(iters):
        dist = np.linalg.norm(P - y, axis=1); w = 1.0 / np.maximum(dist, 1e-9)
        y = (P * w[:, None]).sum(0) / w.sum()
    return y

def z2(phi, u, d, rect, k=300, B=25, n_query=200, seed=0):
    rng = np.random.default_rng(seed)
    tree = cKDTree(phi)
    idx = np.linspace(0, len(phi) - 1, n_query).astype(int)
    single, mean_c, med_c, geo_c = [], [], [], []
    for i in idx:
        _, nb = tree.query(phi[i], k=k)
        cands = []
        for b in range(B):
            sel = rng.choice(nb, size=k, replace=True)
            X = np.hstack([np.ones((k, 1)), u[sel]])
            th, *_ = np.linalg.lstsq(X, d[sel], rcond=None)
            J = th[1:].T
            if rect is not None: J = rect @ J
            dstar = d[i] if rect is None else rect @ d[i]
            try: ub = np.linalg.solve(J, dstar)
            except np.linalg.LinAlgError: continue
            cands.append(ub)
        if len(cands) < 3: continue
        cands = np.array(cands)
        truth = u[i]
        single.append(np.linalg.norm(cands[0] - truth))
        mean_c.append(np.linalg.norm(cands.mean(0) - truth))
        med_c.append(np.linalg.norm(np.median(cands, 0) - truth))
        geo_c.append(np.linalg.norm(geo_median(cands) - truth))
    f = lambda x: {"q50": round(float(np.median(x)), 4), "q95": round(float(np.quantile(x, .95)), 4),
                   "mean": round(float(np.mean(x)), 4)}
    # disagreement among candidates (correlated failures?)
    return {"single": f(single), "mean": f(mean_c), "coord_median": f(med_c), "geo_median": f(geo_c)}

res = {}
p2 = build_P2(); res["P2"] = z2(*p2, rect=S0)
p1 = build_P1(); res["P1"] = z2(*p1, rect=None)
print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
