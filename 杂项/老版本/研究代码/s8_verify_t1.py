"""S8 minimal numerical validation of corrected Theorem T1 (phase2 theory construction).
Checks:
  1. DARE identity A_cl^T P A_cl = P - Q - K_c^T R K_c
  2. A_cl Schur but possibly ||A_cl|| > 1 (non-normal) -> old bound invalid, T1 valid
  3. Simulated closed-loop error <= T1 UUB radius
  4. Monotonicity of UUB radius in D = eps + ||B|| a_max + delta
  5. Feedforward-infeasibility term (delta) is necessary (C3)
Uses project interpreter (numpy/scipy). No training code touched.
"""
import sys
import numpy as np
from scipy.linalg import solve_discrete_are, solve_discrete_lyapunov

np.set_printoptions(precision=5, suppress=True)
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

rng = np.random.default_rng(0)


def dlqr(A, B, Q, R):
    P = solve_discrete_are(A, B, Q, R)
    K = np.linalg.solve(R + B.T @ P @ B, B.T @ P @ A)
    return P, K


def t1_radius(P, Q, R, K, D):
    lam_min = np.linalg.eigvalsh(Q + K.T @ R @ K).min()
    lam = lam_min / np.linalg.eigvalsh(P).max()
    ratio = np.sqrt(np.linalg.eigvalsh(P).max() / np.linalg.eigvalsh(P).min())
    uub = ratio * D / (1.0 - np.sqrt(1.0 - lam))
    return lam, ratio, uub


print("=" * 72)
print("TEST 1: DARE identity and Schur-but-norm>1 (non-normal A)")
print("=" * 72)
A = np.array([[0.90, 2.0], [0.0, 0.90]])   # rho=0.9, non-normal
B = np.array([[1.0], [1.0]])
Q = np.eye(2)
R = np.eye(1)
print("rho(A) =", f"{max(abs(np.linalg.eigvals(A))):.4f}", " ||A||_2 =", f"{np.linalg.norm(A, 2):.4f}")
P, K = dlqr(A, B, Q, R)
Acl = A - B @ K
print("A_cl =", Acl.tolist())
print("rho(A_cl) =", f"{max(abs(np.linalg.eigvals(Acl))):.4f}", " ||A_cl||_2 =", f"{np.linalg.norm(Acl, 2):.4f}")
lhs = Acl.T @ P @ Acl
rhs = P - Q - K.T @ R @ K
print("|| A_cl^T P A_cl - (P - Q - K^T R K) || =", f"{np.linalg.norm(lhs - rhs):.2e}", "(should be ~0)")
print("old-bound denominator 1-||A_cl|| =", f"{1 - np.linalg.norm(Acl, 2):.4f}", "(<=0 => old bound meaningless)"
      if np.linalg.norm(Acl, 2) >= 1 else "(>0)")

print()
print("=" * 72)
print("TEST 2: simulated closed-loop error vs T1 UUB radius")
print("=" * 72)
eps = 0.02
beta = 0.03
delta = 0.04
D = eps + beta + delta
lam, ratio, uub = t1_radius(P, Q, R, K, D)
print(f"D = {D:.4f}  lambda = {lam:.5f}  sqrt(lmax/lmin) = {ratio:.4f}  T1 UUB radius = {uub:.5f}")

N = 4000
e = np.array([1.0, -0.5])
worst = 0.0
for k in range(N):
    d = rng.normal(size=2)
    d = d / np.linalg.norm(d) * D      # worst-case direction magnitude D
    e = Acl @ e + d
    if k > N // 2:
        worst = max(worst, np.linalg.norm(e))
print(f"simulated max ||e|| (2nd half) = {worst:.5f} <= T1 radius {uub:.5f}? {worst <= uub}")

print()
print("=" * 72)
print("TEST 3: monotonicity of T1 radius in D (and hence in delta, beta)")
print("=" * 72)
prev = None
mono = True
for Dv in [0.01, 0.05, 0.1, 0.5]:
    _, _, r = t1_radius(P, Q, R, K, Dv)
    print(f"D = {Dv:.2f} -> radius = {r:.5f}")
    if prev is not None and r < prev:
        mono = False
    prev = r
print("monotone increasing in D:", mono)

print()
print("=" * 72)
print("TEST 4: C3 necessity of feedforward-infeasibility term (delta)")
print("=" * 72)
# B_G = [1;0], reference difference d_k = [0;1] (orthogonal to range(B_G)) -> P_G d = d, delta=1
B_G = np.array([[1.0], [0.0]])
d_ref = np.array([0.0, 1.0])
P_G = np.eye(2) - B_G @ np.linalg.pinv(B_G)
print("P_G d_ref =", (P_G @ d_ref).tolist(), " (delta = ||P_G d_ref|| =", f"{np.linalg.norm(P_G @ d_ref):.4f})")
# error dynamics: e+ = A_cl e + P_G d_ref ; with A_cl = A - B_G K, K from 1-input LQR on (A,B_G)
P2, K2 = dlqr(A, B_G, np.eye(2), np.eye(1))
Acl2 = A - B_G @ K2
e = np.zeros(2)
hist_ignore = []   # ignoring the term
hist_keep = []     # keeping the term
e_ig = np.zeros(2)
for k in range(3000):
    e_ig = Acl2 @ e_ig                      # term ignored
    e = Acl2 @ e + P_G @ d_ref              # term kept
    if k > 2500:
        hist_ignore.append(np.linalg.norm(e_ig))
        hist_keep.append(np.linalg.norm(e))
print(f"ignore term: steady ||e|| ~ {np.mean(hist_ignore):.4f} (does NOT reflect constant forcing)")
print(f"keep   term: steady ||e|| ~ {np.mean(hist_keep):.4f} (nonzero offset from feedforward infeasibility)")
print("delta term necessary:", np.mean(hist_keep) > 1e-3)

print()
print("=" * 72)
print("TEST 5: P2 actuator redundancy -> beta pricing (corrected framing)")
print("=" * 72)
# Differential map G: v=(dx,dy) in R^2 -> a=(R,L,D,U) in R^4 ; G is 4x2, INJECTIVE (ker G = {0}).
G = np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, -1.0], [0.0, 1.0]])
print("G shape", G.shape, "rank", np.linalg.matrix_rank(G), "ker(G) dim (R^2) =", 2 - np.linalg.matrix_rank(G))
# The UNCOMMANDED tension/common-mode bias lives in range(G)^perp (subset of actuator space R^4).
U, s, _ = np.linalg.svd(G)
comp_basis = U[:, 2:4]                # 4x2 orthonormal basis of range(G)^perp
print("range(G)^perp basis (tension/common-mode, 4-D):\n", comp_basis.T)
B = np.array([[1.0, 2.0, 0.5, 0.0],   # d=2, actuator dim m_a=4
              [0.0, 1.0, 1.0, 0.5]])
B_G = B @ G
print("B_G = B @ G (d x 2) =", B_G.tolist(), " rank =", np.linalg.matrix_rank(B_G))
a_perp = comp_basis @ np.array([0.3, -0.2])   # admissible tension bias in range(G)^perp
print("||G^T a_perp|| (should be ~0) =", f"{np.linalg.norm(G.T @ a_perp):.2e}",
      "  (a_perp orthogonal to range(G): NOT reachable by any v)")
eff_null = B @ a_perp
print("effect B a_perp on lifted dynamics =", eff_null.tolist(), " ||B a_perp|| =", f"{np.linalg.norm(eff_null):.4f}")
print("beta = ||B|| a_max enters bound iff this is nonzero:", np.linalg.norm(eff_null) > 1e-9)
# C4 boundary: if B annihilates range(G)^perp, tension bias does not affect dynamics
B_null = np.array([[1.0, -1.0, 0.0, 0.0], [0.0, 0.0, 1.0, -1.0]])   # orthogonal to comp_basis
print("C4 case: B orthogonal to range(G)^perp -> ||B a_perp|| =",
      f"{np.linalg.norm(B_null @ a_perp):.2e}", "(beta=0, redundancy does not enter bound)")
print()
print("ALL CHECKS DONE")
