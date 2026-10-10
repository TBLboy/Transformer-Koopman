"""S8b: evaluate T1' term structure and stabilizability on the P2 deploy checkpoint.
Read-only. Project interpreter (edmddl2).
"""
import sys
from pathlib import Path

import numpy as np
import torch

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
from scipy.linalg import solve_discrete_are, eigvals

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
pth = ROOT / "训练代码" / "deploy" / "algorithms" / "tk_assets" / "model_assets" / "platform2_full_model.pth"
ck = torch.load(str(pth), map_location="cpu", weights_only=False)
A = np.asarray(ck["koopman_A"], dtype=float)
B = np.asarray(ck["koopman_B"], dtype=float)
print("A", A.shape, "B", B.shape)
rho = max(abs(eigvals(A)))
print(f"rho(A) = {rho:.4f}   ||A||_2 = {np.linalg.norm(A, 2):.4f}   ||B||_2 = {np.linalg.norm(B, 2):.4f}")

# stabilizability: PBH test on unstable eigenvalues
n = A.shape[0]
ctrb = B.copy()
for i in range(n - 1):
    ctrb = np.hstack([ctrb, np.linalg.matrix_power(A, i + 1) @ B])
print("controllability matrix rank:", np.linalg.matrix_rank(ctrb), "of", n)
unstable = [w for w in eigvals(A) if abs(w) >= 1.0]
print("unstable eigenvalues (>=1):", [f"{w:.3f}" for w in unstable])
pairs = []
for w in unstable:
    M = np.hstack([A - w * np.eye(n), B])
    pairs.append(np.linalg.matrix_rank(M))
print("PBH ranks [A-wI, B] for unstable modes:", pairs, "(need == n for stabilizability)")

# try LQR
Q = np.eye(n)
R = np.eye(B.shape[1])
print("\n--- LQR attempt (Q=I, R=I) ---")
try:
    P = solve_discrete_are(A, B, Q, R)
    K = np.linalg.solve(R + B.T @ P @ B, B.T @ P @ A)
    Acl = A - B @ K
    # DARE residual check (reviewer C-5 defect fix)
    dare_res = A.T @ P @ A - P + Q - A.T @ P @ B @ np.linalg.solve(R + B.T @ P @ B, B.T @ P @ A)
    print(f"DARE residual ||.||_F = {np.linalg.norm(dare_res):.3e}  (should be ~0)")
    rho_cl = max(abs(eigvals(Acl)))
    vq = eigvals(Q + K.T @ R @ K)
    lam = vq.real.min() / eigvals(P).max()
    ratio = np.sqrt(eigvals(P).max() / eigvals(P).min())
    print(f"rho(A_cl) = {rho_cl:.6f}  (Schur? {rho_cl < 1.0})  ||A_cl||_2 = {np.linalg.norm(Acl, 2):.4f}")
    print(f"lambda = {lam:.3e}  (lambda>0? {lam > 0})  cond(P) = {np.linalg.eigvalsh(P).max()/np.linalg.eigvalsh(P).min():.3e}")
    print(f"lambda = {lam:.6f}  sqrt(lmax/lmin)= {ratio:.4f}  1-sqrt(1-lam)={1-np.sqrt(1-lam):.4f}")
    print(f"T1' coefficient = ratio/(1-sqrt(1-lam)) = {ratio/(1-np.sqrt(1-lam)):.4f}")
    Delta, m = 1.0, B.shape[1]
    emax = Delta * np.sqrt(m) / 2.0
    beta = np.linalg.norm(B, 2) * emax
    print(f"e_max = {emax:.4f} steps   ||B|| e_max = {beta:.4f}")
    for eps in [0.01, 0.05, 0.1]:
        D = eps + beta   # delta unknown (no reference data) -> set 0
        print(f"  eps={eps}: D(no delta)={D:.4f} -> UUB radius = {ratio/(1-np.sqrt(1-lam))*D:.4f}")
except Exception as e:
    print("DARE failed:", repr(e))
print("DONE")
