from pathlib import Path
import json
import numpy as np
import torch
from scipy.linalg import solve_discrete_are

CKPT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\deploy\algorithms\tk_assets\model_assets\platform2_full_model.pth")
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\testA_gauge_v3.json")
rng = np.random.default_rng(1)

o = torch.load(CKPT, map_location="cpu", weights_only=False)
A = np.asarray(o["koopman_A"], float)
B = np.asarray(o["koopman_B"], float)
n = A.shape[0]
m = B.shape[1]
C = np.zeros((2, n)); C[:, :2] = np.eye(2)

def lqr_K(Ax, Bx, Q, R):
    P = solve_discrete_are(Ax, Bx, Q, R)
    K = np.linalg.solve(R + Bx.T @ P @ Bx, Bx.T @ P @ Ax)
    if not np.all(np.isfinite(K)):
        raise np.linalg.LinAlgError("non-finite gain")
    return K

def make_T(cond_target, k):
    U, _ = np.linalg.qr(rng.standard_normal((k, k)))
    V, _ = np.linalg.qr(rng.standard_normal((k, k)))
    s = np.logspace(0.0, float(np.log10(cond_target)), k)
    return U @ np.diag(s) @ V.T

def sim(Ax, Bx, K, zr, Tsim=500):
    nn = Ax.shape[0]
    z = np.zeros(nn)
    ys = []
    for j in range(Tsim - 1):
        u = -K @ (z - zr[j])
        z = Ax @ z + Bx @ u
        ys.append(C @ z)
    return np.array(ys)

grid = {}
for alpha in [1.0, 10.0, 100.0, 1000.0]:
    Q = np.diag(np.r_[np.ones(2) * 1.0, np.ones(n - 2) * alpha])
    R = np.eye(m)
    K0 = lqr_K(A, B, Q, R)
    assert K0.shape == (m, n), K0.shape
    row = {}
    for ct in [1.0, 1e2, 1e4, 1e6]:
        relK, relY, n_fail = [], [], 0
        for _ in range(4):
            T = make_T(ct, n - 2)
            S = np.eye(n); S[2:, 2:] = T
            Sinv = np.linalg.inv(S)
            Ap = S @ A @ Sinv
            Bp = S @ B
            try:
                Kp = lqr_K(Ap, Bp, Q, R)
            except Exception:
                n_fail += 1
                continue
            relK.append(float(np.linalg.norm(K0 - Kp @ S) / np.linalg.norm(K0)))
            zr = rng.standard_normal((500, n))
            y0 = sim(A, B, K0, zr)
            y1 = sim(Ap, Bp, Kp, zr @ S.T)
            relY.append(float(np.linalg.norm(y0 - y1) / (np.linalg.norm(y0) + 1e-12)))
        row["condT_%g" % ct] = {
            "K_rel_max": max(relK) if relK else None,
            "track_rel_max": max(relY) if relY else None,
            "n_dare_failures_out_of_4": n_fail,
        }
    grid["alpha_%g" % alpha] = row

print(json.dumps(grid, indent=2))
OUT.write_text(json.dumps(grid, indent=2), encoding="utf-8")
