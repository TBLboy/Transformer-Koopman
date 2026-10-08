from pathlib import Path
import json
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
P1D = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
P2D = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\V_C8b.json")
S0 = np.diag([-1.0, 1.0])

# reuse builders (compact)
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

def local_J(phi, u, d, rect=None, k=300):
    tree = cKDTree(phi)
    J = []
    for i in range(len(phi)):
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

def run_case(Jseq, mu, L, N=6, n_init=200, seed=0):
    rng = np.random.default_rng(seed)
    d = Jseq.shape[1]
    alphas_c = cheb_gains(N, mu, L)
    a_const = 2.0 / (L + mu)
    res_c, res_ch, oob = [], [], 0
    # windows of length N
    for s in range(0, len(Jseq) - N, N):
        Jw = Jseq[s:s + N]
        for _ in range(n_init // 4):
            e0 = rng.standard_normal(d); e0 /= np.linalg.norm(e0)
            ec = e0.copy(); ech = e0.copy()
            for j in range(N):
                ec = (np.eye(d) - a_const * Jw[j]) @ ec
                ech = (np.eye(d) - alphas_c[j] * Jw[j]) @ ech
            res_c.append(np.linalg.norm(ec)); res_ch.append(np.linalg.norm(ech))
        # out-of-band rate: eigenvalues of sym J outside [mu,L]
        for j in range(N):
            ev = np.linalg.eigvalsh(0.5 * (Jw[j] + Jw[j].T))
            if ev[0] < mu or ev[-1] > L: oob += 1
    return {"const_median_final": float(np.median(res_c)), "cheb_median_final": float(np.median(res_ch)),
            "const_mean_final": float(np.mean(res_c)), "cheb_mean_final": float(np.mean(res_ch)),
            "cheb_better_frac": float(np.mean(np.array(res_ch) < np.array(res_c))),
            "oob_frac": oob / (N * max(1, (len(Jseq) // N)))}

res = {}
# P2
phi2, u2, d2 = build_P2()
J2 = local_J(phi2, u2, d2, rect=S0)
lm2 = np.array([np.linalg.eigvalsh(0.5 * (j + j.T))[0] for j in J2])
lx2 = np.array([np.linalg.eigvalsh(0.5 * (j + j.T))[-1] for j in J2])
mu2 = float(np.quantile(lm2, 0.05)); L2 = float(np.quantile(lx2, 0.95))
res["P2"] = {"mu": mu2, "L": L2, "kappa": L2 / mu2}
res["P2"]["replay"] = run_case(J2, mu2, L2)

# P1
phi1, u1, d1 = build_P1()
J1 = local_J(phi1, u1, d1, rect=None)
lm1 = np.array([np.linalg.eigvalsh(0.5 * (j + j.T))[0] for j in J1])
lx1 = np.array([np.linalg.eigvalsh(0.5 * (j + j.T))[-1] for j in J1])
# use PD subset for interval
pos = lm1 > 0
mu1 = float(np.quantile(lm1[pos], 0.05)); L1 = float(np.quantile(lx1[pos], 0.95))
res["P1"] = {"mu": mu1, "L": L1, "kappa": L1 / mu1, "frac_pos": float(pos.mean())}
res["P1"]["replay_all"] = run_case(J1, mu1, L1)
res["P1"]["replay_pd_subset"] = run_case(J1[pos], mu1, L1)

print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
