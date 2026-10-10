from pathlib import Path
import json
import numpy as np
import torch
from scipy.linalg import solve_discrete_are

CKPT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\deploy\algorithms\tk_assets\model_assets\platform2_full_model.pth")
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\testA_gauge_v2.json")
rng = np.random.default_rng(0)

o = torch.load(CKPT, map_location="cpu", weights_only=False)
A = np.asarray(o["koopman_A"], float)
B = np.asarray(o["koopman_B"], float)
n, m = B.shape
C = np.zeros((2, n)); C[:, :2] = np.eye(2)

def lqr_K(A, B, Q, R):
    P = solve_discrete_are(A, B, Q, R)
    return P, np.linalg.solve(R + B.T @ P @ B, B.T @ P @ A)

def sim_physical(Ax, Bx, K, zr, Cmap, Tsim=400):
    z = np.zeros(n); ys = []
    for k in range(Tsim - 1):
        u = -K @ (z - zr[k])
        z = Ax @ z + Bx @ u
        ys.append(Cmap @ z)
    return np.array(ys)

results = {"alphas": {}, "note": "transformed reference zr'=S zr; physical output y'=C S^{-1} z'=C z'"}
for alpha in [0.01, 0.1, 1.0, 10.0]:
    Q = np.diag(np.r_[np.ones(2) * 1.0, np.ones(n - 2) * alpha])
    R = np.eye(m)
    P0, K0 = lqr_K(A, B, Q, R)
    rel_diffs, track_diffs, eig_diffs = [], [], []
    for trial in range(8):
        T = rng.standard_normal((n - 2, n - 2))
        while abs(np.linalg.det(T)) < 1e-3:
            T = rng.standard_normal((n - 2, n - 2))
        S = np.eye(n); S[2:, 2:] = T
        Sinv = np.linalg.inv(S)
        Ap, Bp = S @ A @ Sinv, S @ B
        Pp, Kp = lqr_K(Ap, Bp, Q, R)
        Kp_back = Kp @ S
        rel_diffs.append(float(np.linalg.norm(K0 - Kp_back) / np.linalg.norm(K0)))
        # fair simulation with correctly transformed reference
        zr = rng.standard_normal((400, n))
        y0 = sim_physical(A, B, K0, zr, C)
        y1 = sim_physical(Ap, Bp, Kp, zr @ S.T, C)
        track_diffs.append(float(np.linalg.norm(y0 - y1) / (np.linalg.norm(y0) + 1e-12)))
        eig_diffs.append(float(abs(np.max(np.abs(np.linalg.eigvals(A - B @ K0))) - np.max(np.abs(np.linalg.eigvals(Ap - Bp @ Kp))))))
    results["alphas"]["alpha_%g" % alpha] = {
        "K_relative_diff_mean": float(np.mean(rel_diffs)),
        "K_relative_diff_max": float(np.max(rel_diffs)),
        "physical_tracking_relative_diff_mean": float(np.mean(track_diffs)),
        "physical_tracking_relative_diff_max": float(np.max(track_diffs)),
        "closed_loop_spectral_radius_diff_max": float(np.max(eig_diffs)),
    }

print(json.dumps(results, indent=2))
OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
