from pathlib import Path
import json
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
P1D = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
P2D = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\V_Z1.json")
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
    tree = cKDTree(phi); idx = np.arange(0, len(phi), stride); J = []
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

# ---------- Z0: adversarial time-varying sector ----------
def z0(seed=0):
    out = {}
    for name, mu, L in (("P2", 5.4e-4, 6.6e-3), ("P1", 5.25, 599.8)):
        N = 6; kappa = L / mu
        a_const = 2.0 / (L + mu)
        ach = cheb_gains(N, mu, L)
        # adversary: given alpha_k, choose lambda in {mu,L} maximizing |1-alpha*lambda|
        def adv_prod(alphas):
            p = 1.0
            for a in alphas:
                lam = mu if abs(1 - a * mu) >= abs(1 - a * L) else L
                p *= abs(1 - a * lam)
            return p
        out[name] = {"kappa": kappa,
                     "const_adversarial_N6": adv_prod(np.full(N, a_const)),
                     "cheb_adversarial_N6": adv_prod(ach),
                     "const_theory_(q*)^N": ((kappa - 1) / (kappa + 1)) ** N}
    return out

# ---------- Z1: actual-J replay ----------
def clip(v, tau):
    n = np.linalg.norm(v)
    return v if n <= tau else v * (tau / n)

def replay(Jseq, mu, L, N=10, tau_beta=1.0, n_win=300, seed=0):
    rng = np.random.default_rng(seed)
    d = Jseq.shape[1]
    a = 2.0 / (L + mu)
    starts = rng.integers(0, max(1, len(Jseq) - N - 1), size=n_win)
    res = {"const": [], "clip": [], "errc": []}
    du_max = {"const": [], "clip": [], "errc": []}
    mem = []
    for s in starts:
        Jw = Jseq[s:s + N]
        if len(Jw) < N: continue
        for _ in range(8):
            e0 = rng.standard_normal(d); e0 /= np.linalg.norm(e0)
            # const
            e = e0.copy(); du = 0.0
            for k in range(N):
                v = a * e; du = max(du, np.linalg.norm(v)); e = e - Jw[k] @ v
            res["const"].append(np.linalg.norm(e)); du_max["const"].append(du)
            # naive clip
            tau = tau_beta * a  # scale relative to alpha (e0 unit -> ||alpha e0||=a)
            e = e0.copy(); du = 0.0
            for k in range(N):
                v = clip(a * e, tau); du = max(du, np.linalg.norm(v)); e = e - Jw[k] @ v
            res["clip"].append(np.linalg.norm(e)); du_max["clip"].append(du)
            # errc
            e = e0.copy(); m = np.zeros(d); du = 0.0
            for k in range(N):
                v = a * e + m; duk = clip(v, tau); m = v - duk; du = max(du, np.linalg.norm(duk))
                e = e - Jw[k] @ duk
            res["errc"].append(np.linalg.norm(e)); du_max["errc"].append(du); mem.append(np.linalg.norm(m))
    q = lambda x: [round(float(np.quantile(x, p)), 5) for p in (0.5, 0.95, 0.99)]
    return {kk: {"q50/95/99": q(res[kk]), "max_du_mean": round(float(np.mean(du_max[kk])), 4)} for kk in res} | \
           {"errc_mem_mean": round(float(np.mean(mem)), 4), "errc_mem_max": round(float(np.max(mem)), 4), "tau_beta": tau_beta}

res = {"Z0": z0()}
# P2
phi2, u2, d2 = build_P2(); J2 = local_J(phi2, u2, d2, rect=S0, stride=7)
ev2 = np.array([np.linalg.eigvalsh(0.5 * (j + j.T)) for j in J2])
mu2, L2 = float(np.quantile(ev2[:, 0], 0.05)), float(np.quantile(ev2[:, -1], 0.95))
res["P2"] = {"mu": mu2, "L": L2}
for tb in (0.5, 1.0, 2.0):
    res["P2"][f"beta{tb}"] = replay(J2, mu2, L2, tau_beta=tb)
# P1 (use PD-subset interval)
phi1, u1, d1 = build_P1(); J1 = local_J(phi1, u1, d1, rect=None, stride=7)
ev1 = np.array([np.linalg.eigvalsh(0.5 * (j + j.T)) for j in J1]); pos = ev1[:, 0] > 0
mu1, L1 = float(np.quantile(ev1[pos, 0], 0.05)), float(np.quantile(ev1[pos, -1], 0.95))
res["P1"] = {"mu": mu1, "L": L1, "frac_pd": float(pos.mean())}
for tb in (0.5, 1.0, 2.0):
    res["P1"][f"beta{tb}"] = replay(J1[pos], mu1, L1, tau_beta=tb)

print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
