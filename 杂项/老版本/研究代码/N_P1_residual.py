from pathlib import Path
import json
import numpy as np
from scipy.linalg import solve_discrete_are

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
DATA = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\N_P1_residual.json")

def load(f):
    z = np.load(DATA / f)
    return (z["x"].astype(float), z["u"].astype(float),
            z["t"].astype(float), z["trajectory_id"])

def pairs(x, u, tid):
    X, U, Y = [], [], []
    for tr in np.unique(tid):
        m = tid == tr
        xi, ui = x[m], u[m]
        if len(xi) < 2:
            continue
        X.append(xi[:-1]); U.append(ui[:-1]); Y.append(xi[1:])
    return np.concatenate(X), np.concatenate(U), np.concatenate(Y)

def fit_lti(X, U, Y, lam=1e-8):
    Phi = np.concatenate([X, U], axis=1)          # (N, 9)
    W = np.linalg.solve(Phi.T @ Phi + lam * np.eye(Phi.shape[1]), Phi.T @ Y)
    A = W[:X.shape[1], :].T                         # 6x6
    B = W[X.shape[1]:, :].T                         # 6x3
    return A, B

def stats(a):
    a = np.asarray(a)
    return {"mean": float(a.mean()), "median": float(np.median(a)), "p95": float(np.percentile(a, 95))}

xt, ut, tt, tidt = load("train.npz")
xv, uv, tv, tidv = load("val.npz")
Xtr, Utr, Ytr = pairs(xt, ut, tidt)
Xva, Uva, Yva = pairs(xv, uv, tidv)

A, B = fit_lti(Xtr, Utr, Ytr)
n, m = B.shape
Bpinv = np.linalg.pinv(B)
Proj_B = B @ Bpinv                    # projector onto im(B) (input-reachable)
Proj_perp = np.eye(n) - Proj_B

R = Yva - Xva @ A.T - Uva @ B.T       # state-space residual (N,6)
r2 = np.sum(R * R, axis=1) + 1e-30
frac_B = np.sum((R @ Proj_B.T) * R, axis=1) / r2
frac_perp = np.sum((R @ Proj_perp.T) * R, axis=1) / r2

# split residual energy by state group: positions (0,2,4) vs velocities (1,3,5)
res_energy_mean = np.mean(R * R, axis=0)

# LQR gain on identified (A,B), Q=I, R=I -> policy-null dim
try:
    Pare = solve_discrete_are(A, B, np.eye(n), np.eye(m))
    K = np.linalg.solve(np.eye(m) + B.T @ Pare @ B, B.T @ Pare @ A)
    svK = np.linalg.svd(K, compute_uv=False)
    rankK = int(np.sum(svK > 1e-8 * svK[0]))
    lqr = {"rank_K": rankK, "policy_null_dim": n - rankK, "sigma_K": [float(s) for s in svK]}
except Exception as e:
    lqr = {"error": str(e)}

# control sensitivity of the residual via K: ||K r|| / (sigma_max ||r||)
try:
    sigma_max = float(np.linalg.svd(K, compute_uv=False)[0])
    sens = np.linalg.norm(R @ K.T, axis=1) / (sigma_max * np.linalg.norm(R, axis=1) + 1e-30)
    sens_stats = stats(sens)
except Exception:
    sens_stats = None

results = {
    "model": {"A_spectral_radius": float(np.max(np.abs(np.linalg.eigvals(A)))),
              "rank_B": int(np.linalg.matrix_rank(B)), "n": n, "m": m},
    "state_residual_energy_mean_per_dim": [float(v) for v in res_energy_mean],
    "position_dims_total_energy": float(res_energy_mean[[0, 2, 4]].sum()),
    "velocity_dims_total_energy": float(res_energy_mean[[1, 3, 5]].sum()),
    "residual_energy_frac_in_im_B": stats(frac_B),
    "residual_energy_frac_orthogonal_to_B": stats(frac_perp),
    "residual_policy_sensitivity_via_LQR_K": sens_stats,
    "LQR_on_identified_AB": lqr,
    "verdict": ("Fully-actuated P1: if velocity(m=3) residual dominates and frac_in_im_B ~1, residual is input-reachable -> control-relevant, "
                "leaving little 'prediction-only' residual; policy-null subspace of a static gain is small and not physically meaningful."),
}
print(json.dumps(results, indent=2))
OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
