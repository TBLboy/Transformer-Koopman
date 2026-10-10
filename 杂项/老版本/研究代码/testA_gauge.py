from pathlib import Path
import json
import numpy as np
import torch
from scipy.linalg import solve_discrete_are

CKPT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\deploy\algorithms\tk_assets\model_assets\platform2_full_model.pth")
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\testA_gauge.json")
rng = np.random.default_rng(0)

o = torch.load(CKPT, map_location="cpu", weights_only=False)
A = np.asarray(o["koopman_A"], float)
B = np.asarray(o["koopman_B"], float)
n, m = B.shape
assert A.shape == (n, n)
C = np.zeros((2, n)); C[:, :2] = np.eye(2)

Qx = np.eye(2)
alpha = 1.0
Q = np.diag(np.r_[np.ones(2) * 1.0, np.ones(n - 2) * alpha])
R = np.eye(m)

def lqr_K(A, B, Q, R):
    P = solve_discrete_are(A, B, Q, R)
    K = np.linalg.solve(R + B.T @ P @ B, B.T @ P @ A)
    return P, K

P0, K0 = lqr_K(A, B, Q, R)

# random invertible transform on the hidden block only (preserve physical coords)
T = rng.standard_normal((n - 2, n - 2))
while abs(np.linalg.det(T)) < 1e-3:
    T = rng.standard_normal((n - 2, n - 2))
S = np.eye(n)
S[2:, 2:] = T
Sinv = np.linalg.inv(S)
Ap = S @ A @ Sinv
Bp = S @ B

# physical invariance check: C A^j B must be unchanged
inv_err = 0.0
for j in range(0, 6):
    inv_err = max(inv_err, float(np.abs(C @ np.linalg.matrix_power(A, j) @ B - C @ np.linalg.matrix_power(Ap, j) @ Bp).max()))

P1, K1 = lqr_K(Ap, Bp, Q, R)

# compare the control law as an operator on original coordinates z:
#   original: u = -K0 z
#   transformed (expressed back in z): u = -K1 (S z) = -(K1 S) z
K1_back = K1 @ S
rel_diff = float(np.linalg.norm(K0 - K1_back) / np.linalg.norm(K0))

# closed-loop eigenvalues
cl0 = np.linalg.eigvals(A - B @ K0)
cl1 = np.linalg.eigvals(Ap - Bp @ K1)
cl1_back = np.linalg.eigvals(A - B @ K1_back)

# simulate physical tracking under both controllers on a random reference
Tsim = 300
zr = rng.standard_normal((Tsim, n))
z0 = np.zeros(n); z1 = np.zeros(n)
ys0, ys1 = [], []
for k in range(Tsim - 1):
    u0 = -K0 @ (z0 - zr[k])
    u1 = -K1 @ (z1 - zr[k])
    z0 = A @ z0 + B @ u0
    z1 = Ap @ z1 + Bp @ u1
    ys0.append(C @ z0); ys1.append(C @ z1)
ys0 = np.array(ys0); ys1 = np.array(ys1)
track_diff = float(np.linalg.norm(ys0 - ys1) / (np.linalg.norm(ys0) + 1e-12))

res = {
    "n": n, "m": m, "alpha": alpha,
    "physical_invariance_max_abs_error": inv_err,
    "control_law_relative_difference_on_original_coords": rel_diff,
    "closed_loop_eig_original_max_abs": float(np.max(np.abs(cl0))),
    "closed_loop_eig_transformed_max_abs": float(np.max(np.abs(cl1))),
    "closed_loop_eig_transformed_back_max_abs": float(np.max(np.abs(cl1_back))),
    "physical_tracking_relative_difference": track_diff,
    "sample_K0_rows": K0[:2].tolist(),
    "sample_K1_back_rows": K1_back[:2].tolist(),
    "verdict": "If physical predictions are invariant but the control law / closed-loop differs, the gauge pathology is confirmed.",
}
valid = "(I2 block preserved, physical map invariant: %s)" % (inv_err < 1e-9)
print(valid)
print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
