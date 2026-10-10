from pathlib import Path
import json
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
P1D = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
P2D = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\V_C8c.json")
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

def local_J(phi, u, d, rect=None, k=300, stride=1):
    tree = cKDTree(phi)
    idx = np.arange(0, len(phi), stride)
    J = []
    for i in idx:
        _, nb = tree.query(phi[i], k=k)
        X = np.hstack([np.ones((k, 1)), u[nb]])
        th, *_ = np.linalg.lstsq(X, d[nb], rcond=None)
        JJ = th[1:].T
        if rect is not None: JJ = rect @ JJ
        J.append(JJ)
    return np.array(J)

def cheb_gains(N, mu, L):
    a = (L + mu) / 2.0; b = (L - mu) / 2.0
    return np.array([1.0 / (a + b * np.cos((2 * j - 1) * np.pi / (2 * N))) for j in range(1, N + 1)])

def oracle_const(Jw):
    d = Jw.shape[1]
    ev = np.array([np.linalg.eigvalsh(0.5 * (j + j.T)) for j in Jw])
    lomin, lomax = ev[:, 0].min(), ev[:, -1].max()
    a = 2.0 / (lomax + lomin) if (lomax + lomin) > 1e-12 else 0.0
    return a

def sim_window(Jw, alphas, n_init=20, seed=0):
    rng = np.random.default_rng(seed)
    d = Jw.shape[1]; res = []
    for _ in range(n_init):
        e = rng.standard_normal(d); e /= np.linalg.norm(e)
        for j in range(len(Jw)):
            e = (np.eye(d) - alphas[j] * Jw[j]) @ e
        res.append(np.linalg.norm(e))
    return float(np.median(res))

def run(Jseq, mu, L, Ns=(4, 6, 8), n_win=400, seed=0):
    rng = np.random.default_rng(seed)
    out = {}
    Nmax = max(Ns)
    starts = rng.integers(0, max(1, len(Jseq) - Nmax - 1), size=n_win)
    for N in Ns:
        ac = 2.0 / (L + mu)
        ach = cheb_gains(N, mu, L)
        r_c, r_ch, r_or, oob = [], [], [], 0
        for s in starts:
            Jw = Jseq[s:s + N]
            if len(Jw) < N: continue
            r_c.append(sim_window(Jw, np.full(N, ac)))
            r_ch.append(sim_window(Jw, ach))
            ao = oracle_const(Jw); r_or.append(sim_window(Jw, np.full(N, ao)))
            ev = np.array([np.linalg.eigvalsh(0.5 * (j + j.T)) for j in Jw])
            oob += int(((ev[:, 0] < mu) | (ev[:, -1] > L)).sum())
        n_steps = N * len(r_c)
        out[f"N{N}"] = {"const_med": float(np.median(r_c)), "cheb_med": float(np.median(r_ch)),
                        "oracle_const_med": float(np.median(r_or)),
                        "cheb_better_frac": float(np.mean(np.array(r_ch) < np.array(r_c))),
                        "oob_frac": oob / max(1, n_steps)}
    return out

res = {}
# P2
phi2, u2, d2 = build_P2(); J2 = local_J(phi2, u2, d2, rect=S0, stride=7)
ev2 = np.array([np.linalg.eigvalsh(0.5 * (j + j.T)) for j in J2])
lm2, lx2 = ev2[:, 0], ev2[:, -1]
res["P2"] = {
    "wide": {"mu": float(np.quantile(lm2, .05)), "L": float(np.quantile(lx2, .95))},
    "tight": {"mu": float(np.median(lm2)), "L": float(np.median(lx2))}}
for tag, iv in (("wide", res["P2"]["wide"]), ("tight", res["P2"]["tight"])):
    res["P2"][tag]["kappa"] = iv["L"] / iv["mu"]
    res["P2"][tag]["replay"] = run(J2, iv["mu"], iv["L"])

# P1
phi1, u1, d1 = build_P1(); J1 = local_J(phi1, u1, d1, rect=None, stride=7)
ev1 = np.array([np.linalg.eigvalsh(0.5 * (j + j.T)) for j in J1])
lm1, lx1 = ev1[:, 0], ev1[:, -1]; pos = lm1 > 0
res["P1"] = {
    "wide": {"mu": float(np.quantile(lm1[pos], .05)), "L": float(np.quantile(lx1[pos], .95))},
    "tight": {"mu": float(np.median(lm1[pos])), "L": float(np.median(lx1[pos]))},
    "frac_pos": float(pos.mean())}
for tag, iv in (("wide", res["P1"]["wide"]), ("tight", res["P1"]["tight"])):
    res["P1"][tag]["kappa"] = iv["L"] / iv["mu"]
    res["P1"][tag]["replay"] = run(J1[pos], iv["mu"], iv["L"])

print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
