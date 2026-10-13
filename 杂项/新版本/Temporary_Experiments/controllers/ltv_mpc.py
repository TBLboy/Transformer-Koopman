# -*- coding: utf-8 -*-
"""Frozen-schedule LTV-MPC (plan section 7.1, Theory_Package/06).

Per time step k:
  1. z_0 = encoder(X_k);
  2. warm start  bar U  = shift of the previous solution (documented tail fill);
  3. nominal rollout on the FULL model with bar U  ->  bar A_i, bar B_i;
  4. freeze bar A_i, bar B_i and solve the convex LTV QP;
  5. apply u_0, shift the history, repeat.

Cost (plan section 7.1, measurement space):
    sum_{i=1..N} ||C z_i - x_i^ref||_Q^2  +  sum_{i=0..N-1} ||u_i - u_i^ref||_R^2
  + sum_{i=0..N-1} ||u_i - u_{i-1}||_S^2 ,   terminal weight P on i = N.

Documented deviation from Theory_Package/06 section 1: 06 writes the state cost in
LATENT space (||z_i - z_i^ref||_Q^2) while the plan writes it in MEASUREMENT space
(||C z_i - x_i^ref||_Q^2).  A latent reference is not defined by the data, so the
plan's measurement-space form is implemented; this is recorded as a theory-code
consistency item in reports/control_comparison.md.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import scipy.sparse as sp

_HERE = os.path.dirname(os.path.abspath(__file__))
_MODELS = os.path.join(os.path.dirname(_HERE), "models")
if _MODELS not in sys.path:
    sys.path.insert(0, _MODELS)
import device as _device                            # noqa: E402

try:
    import osqp
    HAVE_OSQP = True
except Exception:                                   # pragma: no cover
    HAVE_OSQP = False


def _dev_n_state():
    return int(_device.current()["n_state"])


def _dev_n_ctrl():
    return int(_device.current()["n_ctrl"])


def _model_n_ctrl(model):
    """Control dimension of a trained scheduled model (B0 is (latent, n_ctrl))."""
    if hasattr(model, "B0"):
        return int(model.B0.shape[1])
    return _dev_n_ctrl()


# ------------------------------------------------------------------ affine map
def prediction_matrices(A_bar, B_bar, z0):
    """Z = F + G U for the frozen LTV model (Theory_Package/06 section 4).

    A_bar: (N, d, d), B_bar: (N, d, m), z0: (d,)
    returns F: (N, d), G: (N, d, N*m)   with the *time-descending* product order
    prod_{j=a..b} A_j := A_b A_{b-1} ... A_a (empty product = I).
    """
    N, d, _ = A_bar.shape
    m = B_bar.shape[2]
    F = np.zeros((N, d))
    G = np.zeros((N, d, N * m))
    # S[i, t] := A_{i-1} A_{i-2} ... A_t   (for t <= i-1); computed backwards.
    for i in range(1, N + 1):
        F[i - 1] = _prod(A_bar, 0, i - 1) @ z0
        for t in range(i):
            S = _prod(A_bar, t + 1, i - 1)           # A_{i-1}...A_{t+1}
            G[i - 1, :, t * m:(t + 1) * m] = S @ B_bar[t]
    return F, G


def _prod(A_bar, a, b):
    """A_b A_{b-1} ... A_a  (empty product when a > b)."""
    d = A_bar.shape[1]
    P = np.eye(d)
    for j in range(a, b + 1):
        P = A_bar[j] @ P
    return P


def cost_matrices(F, G, x_ref, u_ref, Q, P_term, R, S, u_prev, n_state=None):
    """M, f, const with  J(U) = U^T M U + 2 f^T U + const  (06 section 4, measurement space).

    ``const`` is the U-independent part; it is returned so that the quadratic form
    can be compared with the direct summation (Gate 3 objective test).

    ``n_state`` defaults to ``x_ref.shape[1]``, so the same code serves any device.
    """
    N, d, Nm = G.shape
    m = Nm // N
    if n_state is None:
        n_state = int(x_ref.shape[1])
    C = np.zeros((n_state, d))
    C[:, :n_state] = np.eye(n_state)
    Cbar = np.kron(np.eye(N), C)                                  # (N*n, N*d)
    Qbar = np.kron(np.eye(N), Q)
    Qbar[(N - 1) * n_state:, (N - 1) * n_state:] = P_term         # terminal block
    Rbar = np.kron(np.eye(N), R)
    Sbar = np.kron(np.eye(N), S)
    D = np.eye(Nm)
    for i in range(1, N):
        D[i * m:(i + 1) * m, (i - 1) * m:i * m] = -np.eye(m)
    chat = np.zeros(Nm)
    chat[:m] = -u_prev

    CG = Cbar @ G.reshape(N * d, Nm)
    CF = Cbar @ F.reshape(N * d)
    Xref = x_ref[1:N + 1].reshape(N * n_state)
    Uref = u_ref.reshape(Nm)

    M = CG.T @ Qbar @ CG + Rbar + D.T @ Sbar @ D
    f = CG.T @ Qbar @ (CF - Xref) - Rbar @ Uref + D.T @ Sbar @ chat
    w = CF - Xref
    const = float(w @ Qbar @ w + Uref @ Rbar @ Uref + chat @ Sbar @ chat)
    return M, f, const


def cost_value(U, F, G, x_ref, u_ref, Q, P_term, R, S, u_prev, n_state=None):
    """Direct summation of the same cost -- used to validate M, f."""
    N, d, Nm = G.shape
    m = Nm // N
    if n_state is None:
        n_state = int(x_ref.shape[1])
    Z = F + np.tensordot(G.reshape(N, d, Nm), U, axes=([2], [0]))
    J = 0.0
    for i in range(N):
        W = Q if i < N - 1 else P_term
        e = Z[i, :n_state] - x_ref[i + 1]
        J += e @ W @ e
    for i in range(N):
        ui = U[i * m:(i + 1) * m]
        du = ui - u_ref[i]
        J += du @ R @ du
        prev = u_prev if i == 0 else U[(i - 1) * m:i * m]
        dr = ui - prev
        J += dr @ S @ dr
    return float(J)


def cost_value_quadratic(U, M, f, const=0.0):
    return float(U @ M @ U + 2 * f @ U + const)


# ------------------------------------------------------------------ QP solve
def _bounds(v, N, m):
    """Expand a scalar or per-channel bound into the stacked (N*m,) vector."""
    a = np.asarray(v, dtype=float)
    if a.ndim == 0:
        return np.full(N * m, float(a))
    if a.shape == (m,):
        return np.tile(a, N)
    raise ValueError("bound must be a scalar or a vector of length %d" % m)


def solve_qp(M, f, u_min, u_max, N, m, eps_abs=1e-8, eps_rel=1e-8, max_iter=20000):
    """min 0.5 U^T (2M) U + (2f)^T U  s.t.  u_min <= U <= u_max.

    ``u_min``/``u_max`` may be scalars or per-channel vectors of length ``m``.
    """
    Nm = N * m
    P = sp.csc_matrix(2.0 * M)
    q = 2.0 * f
    A = sp.eye(Nm, format="csc")
    lo = _bounds(u_min, N, m)
    hi = _bounds(u_max, N, m)
    prob = osqp.OSQP()
    prob.setup(P=sp.triu(P, format="csc"), q=q, A=A, l=lo, u=hi,
               eps_abs=eps_abs, eps_rel=eps_rel, max_iter=max_iter,
               verbose=False, polish=True)
    res = prob.solve()
    status = str(res.info.status)
    return np.asarray(res.x), {"status": status,
                               "solved": status in ("solved", "solved inaccurate"),
                               "iter": int(res.info.iter),
                               "run_time": float(res.info.run_time),
                               "obj": float(res.info.obj_val),
                               "dual_res": float(res.info.dual_res),
                               "prim_res": float(res.info.prim_res)}


# ------------------------------------------------------------------ controller
class ScheduledLTVMPC:
    """C1 / C2: scheduled model (M4 = A(c)+B0, M5 = A(c)+B(x)) + frozen LTV-MPC."""

    def __init__(self, model, N=10, Q=None, P_term=None, R=None, S=None,
                 u_min=-100.0, u_max=100.0, tail_fill="repeat", device="cpu",
                 n_state=None, m=None):
        self.model = model
        self.N = int(N)
        self.n_state = int(n_state) if n_state is not None else _dev_n_state()
        self.m = int(m) if m is not None else _model_n_ctrl(model)
        n, mm = self.n_state, self.m
        self.Q = np.eye(n) if Q is None else np.asarray(Q, dtype=float)
        self.P_term = self.Q.copy() if P_term is None else np.asarray(P_term, dtype=float)
        self.R = 1e-3 * np.eye(mm) if R is None else np.asarray(R, dtype=float)
        self.S = 1e-2 * np.eye(mm) if S is None else np.asarray(S, dtype=float)
        # NOTE: the +-100 default is a deliberately loose fallback kept for
        # backwards compatibility with the Gate-3 unit tests.  Every scenario run
        # passes the device's own normalised box explicitly.
        self.u_min = np.asarray(u_min, dtype=float)
        self.u_max = np.asarray(u_max, dtype=float)
        self.tail_fill = tail_fill
        self.device = device
        self.last_U = None
        self.stats = []

    # ---- warm start
    def warm_start(self, u_prev):
        m = self.m if self.m else _dev_n_ctrl()
        if self.last_U is None:
            U = np.tile(np.asarray(u_prev, dtype=float), (self.N, 1))
        else:
            U = np.vstack([self.last_U[1:], self.last_U[-1:]])
        if self.tail_fill == "zero":
            U[-1] = 0.0
        return U

    # ---- one MPC step
    def step(self, xh, uin, u_prev, x_ref, u_ref=None):
        """xh: (1,P,n), uin: (1,P-1,m), u_prev: (m,), x_ref: (N+1,n).

        Returns (u0, U, info).  Nothing here reads future true measurements.
        """
        import torch
        N = self.N
        x_ref = np.asarray(x_ref, dtype=float)
        if x_ref.shape[0] < N + 1:
            raise ValueError("x_ref must have N+1 rows")
        u_ref = np.zeros((N, self.m)) if u_ref is None else np.asarray(u_ref, dtype=float)

        Ubar = self.warm_start(u_prev)
        with torch.no_grad():
            xh_t = torch.as_tensor(xh, dtype=torch.float32, device=self.device)
            uin_t = torch.as_tensor(uin, dtype=torch.float32, device=self.device)
            ub_t = torch.as_tensor(Ubar[None], dtype=torch.float32, device=self.device)
            zb, Ab, Bb = self.model.nominal_rollout(xh_t, uin_t, ub_t)
        z0 = zb[0, 0].cpu().numpy()
        A_bar = Ab[0].cpu().numpy()
        B_bar = Bb[0].cpu().numpy()

        F, G = prediction_matrices(A_bar, B_bar, z0)
        M, f, const = cost_matrices(F, G, x_ref, u_ref, self.Q, self.P_term, self.R,
                                    self.S, np.asarray(u_prev, dtype=float))
        U, qp = solve_qp(M, f, self.u_min, self.u_max, N, B_bar.shape[2])
        self.last_U = U.reshape(N, -1)
        info = dict(qp)
        info["J_quad"] = cost_value_quadratic(U, M, f, const)
        info["J_direct"] = cost_value(U, F, G, x_ref, u_ref, self.Q, self.P_term,
                                      self.R, self.S, np.asarray(u_prev, dtype=float))
        info["U_norm"] = float(np.linalg.norm(U - Ubar.reshape(-1)))
        info["schedule_dev"] = float(np.linalg.norm(A_bar - A_bar.mean(axis=0)))
        self.stats.append(info)
        return U.reshape(N, -1)[0], U.reshape(N, -1), info


class LTIMPC(ScheduledLTVMPC):
    """C0: fixed linear model (M0's A,B lifted to the latent dim) + LTI-MPC.

    Implemented by freezing A_bar = A0, B_bar = B0 for every step, i.e. the same
    QP with a constant schedule -- the honest 'same solver, different model'
    control baseline.
    """

    def step(self, xh, uin, u_prev, x_ref, u_ref=None):
        import torch
        N = self.N
        x_ref = np.asarray(x_ref, dtype=float)
        u_ref = np.zeros((N, self.m)) if u_ref is None else np.asarray(u_ref, dtype=float)
        Ubar = self.warm_start(u_prev)
        with torch.no_grad():
            xh_t = torch.as_tensor(xh, dtype=torch.float32, device=self.device)
            z0 = self.model.encoder(xh_t)[0].cpu().numpy()
            A0 = self.model.A0.detach().cpu().numpy()
            B0 = self.model.B0.detach().cpu().numpy()
        A_bar = np.tile(A0, (N, 1, 1))
        B_bar = np.tile(B0, (N, 1, 1))
        F, G = prediction_matrices(A_bar, B_bar, z0)
        M, f, const = cost_matrices(F, G, x_ref, u_ref, self.Q, self.P_term, self.R,
                                    self.S, np.asarray(u_prev, dtype=float))
        U, qp = solve_qp(M, f, self.u_min, self.u_max, N, B_bar.shape[2])
        self.last_U = U.reshape(N, -1)
        info = dict(qp)
        info["J_quad"] = cost_value_quadratic(U, M, f, const)
        info["J_direct"] = cost_value(U, F, G, x_ref, u_ref, self.Q, self.P_term,
                                      self.R, self.S, np.asarray(u_prev, dtype=float))
        self.stats.append(info)
        return U.reshape(N, -1)[0], U.reshape(N, -1), info


# ------------------------------------------------------------------ reference
def cvxpy_reference(F, G, x_ref, u_ref, Q, P_term, R, S, u_prev, u_min, u_max,
                    n_state=None):
    """Independent cvxpy model of the SAME frozen problem (unit-test reference)."""
    import cvxpy as cp
    N, d, Nm = G.shape
    m = Nm // N
    if n_state is None:
        n_state = int(x_ref.shape[1])
    U = cp.Variable(Nm)
    obj = 0
    for i in range(N):
        Zi = F[i] + G[i].reshape(d, Nm) @ U          # (d,)
        W = Q if i < N - 1 else P_term
        obj += cp.quad_form(Zi[:n_state] - x_ref[i + 1], W)
    for i in range(N):
        obj += cp.quad_form(U[i * m:(i + 1) * m] - u_ref[i], R)
        prev = u_prev if i == 0 else U[(i - 1) * m:i * m]
        obj += cp.quad_form(U[i * m:(i + 1) * m] - prev, S)
    prob = cp.Problem(cp.Minimize(obj), [U <= u_max, U >= u_min])
    prob.solve(solver=cp.OSQP, eps_abs=1e-9, eps_rel=1e-9, max_iter=40000)
    return np.asarray(U.value).reshape(-1), float(prob.value), str(prob.status)
