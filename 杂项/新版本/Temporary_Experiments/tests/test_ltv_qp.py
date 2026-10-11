# -*- coding: utf-8 -*-
"""Gate 3 unit tests: frozen LTV-QP constraints, prediction matrices, objective
and solver status must all pass numerical tests (plan section 11, Gate 3).

Run:  python tests/test_ltv_qp.py
Exit code 0 == all tests passed.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "models"))
sys.path.insert(0, os.path.join(EXP, "controllers"))

from library import build_model                      # noqa: E402
from ltv_mpc import (prediction_matrices, cost_matrices, cost_value,          # noqa: E402
                     cost_value_quadratic, solve_qp, cvxpy_reference,
                     ScheduledLTVMPC)

RESULTS = []
rng = np.random.default_rng(0)


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print("%-58s %s  %s" % (name, "PASS" if ok else "FAIL", detail))


# ---------------------------------------------------------------- 1. affine map
def t1_prediction_matrices():
    N, d, m = 6, 4, 2
    A = rng.normal(size=(N, d, d)) * 0.2 + np.eye(d) * 0.8
    B = rng.normal(size=(N, d, m)) * 0.3
    z0 = rng.normal(size=d)
    U = rng.normal(size=(N, m))
    F, G = prediction_matrices(A, B, z0)
    # explicit frozen rollout
    z, Zs = z0.copy(), []
    for i in range(N):
        z = A[i] @ z + B[i] @ U[i]
        Zs.append(z.copy())
    Zs = np.asarray(Zs)
    Z_aff = F + np.tensordot(G.reshape(N, d, N * m), U.reshape(-1), axes=([2], [0]))
    err = float(np.max(np.abs(Z_aff - Zs)))
    check("T1 prediction matrices Z=F+GU match explicit frozen rollout",
          err < 1e-12, "max|err|=%.3e" % err)
    # F is the zero-input response
    F2, _ = prediction_matrices(A, B, z0)
    z, Zs0 = z0.copy(), []
    for i in range(N):
        z = A[i] @ z
        Zs0.append(z.copy())
    check("T1b F equals zero-input response", float(np.max(np.abs(F2 - np.asarray(Zs0)))) < 1e-12)
    # single-step block: G[r, r] == B_r  (theory 06: G_{i,i-1} = B_{i-1}, 0-based row r = i-1)
    ok = True
    for i in range(N):
        blk = G[i, :, i * m:(i + 1) * m]
        ok &= float(np.max(np.abs(blk - B[i]))) < 1e-12
    check("T1c G[r,r] == B_r (theory G_{i,i-1}=B_{i-1})", ok)
    # blocks with t > r must vanish
    zblk = float(np.max(np.abs(G[0, :, m:])))
    check("T1d G[r, t>r] is zero", zblk < 1e-12, "max|blk|=%.3e" % zblk)


# ---------------------------------------------------------------- 2. objective
def t2_objective():
    N, d, m, n = 8, 5, 2, 2
    A = rng.normal(size=(N, d, d)) * 0.1 + np.eye(d)
    B = rng.normal(size=(N, d, m)) * 0.2
    z0 = rng.normal(size=d)
    F, G = prediction_matrices(A, B, z0)
    Q = np.diag([1.0, 2.0]); Pt = np.diag([3.0, 1.0])
    R = 0.1 * np.eye(m); S = 0.05 * np.eye(m)
    x_ref = rng.normal(size=(N + 1, n))
    u_ref = rng.normal(size=(N, m))
    u_prev = rng.normal(size=m)
    U = rng.normal(size=(N, m)).reshape(-1)
    M, f, const = cost_matrices(F, G, x_ref, u_ref, Q, Pt, R, S, u_prev)
    a = cost_value(U, F, G, x_ref, u_ref, Q, Pt, R, S, u_prev)
    b = cost_value_quadratic(U, M, f, const)
    check("T2 U^T M U + 2 f^T U + const equals direct cost summation",
          abs(a - b) < 1e-9 * max(1.0, abs(a)), "direct=%.10f quad=%.10f" % (a, b))
    # gradient check of f: dJ/dU = 2 M U + 2 f
    g = 2 * M @ U + 2 * f
    h = 1e-6
    gn = np.zeros_like(U)
    for i in range(len(U)):
        e = np.zeros_like(U); e[i] = h
        gn[i] = (cost_value(U + e, F, G, x_ref, u_ref, Q, Pt, R, S, u_prev)
                 - cost_value(U - e, F, G, x_ref, u_ref, Q, Pt, R, S, u_prev)) / (2 * h)
    err = float(np.max(np.abs(g - gn)) / max(1.0, np.max(np.abs(gn))))
    check("T2b analytic gradient matches finite differences", err < 1e-5,
          "rel err=%.3e" % err)
    check("T2c M is symmetric", float(np.max(np.abs(M - M.T))) < 1e-12)


# ---------------------------------------------------------------- 3. QP vs cvxpy
def t3_solver():
    N, d, m, n = 10, 6, 2, 2
    A = rng.normal(size=(N, d, d)) * 0.05 + np.eye(d) * 0.95
    B = rng.normal(size=(N, d, m)) * 0.2
    z0 = rng.normal(size=d)
    F, G = prediction_matrices(A, B, z0)
    Q = np.diag([1.0, 1.0]); Pt = Q.copy()
    R = 0.01 * np.eye(m); S = 0.1 * np.eye(m)
    x_ref = rng.normal(size=(N + 1, n))
    u_ref = np.zeros((N, m))
    u_prev = np.zeros(m)
    u_min, u_max = -3.0, 3.0
    M, f, const = cost_matrices(F, G, x_ref, u_ref, Q, Pt, R, S, u_prev)
    Uo, info = solve_qp(M, f, u_min, u_max, N, m)
    Uc, Jc, st = cvxpy_reference(F, G, x_ref, u_ref, Q, Pt, R, S, u_prev, u_min, u_max)
    Jo = cost_value(Uo, F, G, x_ref, u_ref, Q, Pt, R, S, u_prev)
    Jc_direct = cost_value(Uc, F, G, x_ref, u_ref, Q, Pt, R, S, u_prev)
    check("T3 OSQP reports solved", info["solved"], info["status"])
    check("T3b OSQP and cvxpy objectives agree",
          abs(Jo - Jc_direct) < 1e-6 * max(1.0, abs(Jc_direct)),
          "osqp=%.10f cvxpy=%.10f" % (Jo, Jc_direct))
    check("T3c OSQP and cvxpy solutions agree",
          float(np.max(np.abs(Uo - Uc))) < 1e-4, "max|dU|=%.3e" % float(np.max(np.abs(Uo - Uc))))
    check("T3d box constraints satisfied",
          Uo.min() >= u_min - 1e-8 and Uo.max() <= u_max + 1e-8,
          "[%.6f, %.6f]" % (Uo.min(), Uo.max()))
    # active constraint case: tight box must be saturated
    M2, f2, _ = cost_matrices(F, G, x_ref, u_ref, Q, Pt, R, S, u_prev)
    U2, info2 = solve_qp(M2, f2, -0.01, 0.01, N, m)
    check("T3e tight box saturates", abs(np.abs(U2).max() - 0.01) < 1e-6,
          "max|u|=%.8f" % float(np.abs(U2).max()))


# ---------------------------------------------------------------- 4. nominal rollout
def t4_nominal_rollout():
    torch.manual_seed(3)
    model = build_model("M5", seed=3, r_A=2, r_B=2, g_A=0.1, g_B=0.1)
    model.eval()
    P = 8
    xh = torch.randn(1, P, 2)
    uin = torch.randn(1, P - 1, 2)
    N = 5
    Ubar = torch.randn(1, N, 2)
    with torch.no_grad():
        zb, Ab, Bb = model.nominal_rollout(xh, uin, Ubar)
    # consistency of the returned schedule with the returned states
    ok = True
    worst = 0.0
    for i in range(N - 1):
        zn = Ab[0, i] @ zb[0, i] + Bb[0, i] @ Ubar[0, i]
        e = float(torch.max(torch.abs(zn - zb[0, i + 1])))
        worst = max(worst, e)
        ok &= e < 1e-4
    # compare frozen affine map against the frozen rollout
    F, G = prediction_matrices(Ab[0].numpy(), Bb[0].numpy(), zb[0, 0].numpy())
    z, Zs = zb[0, 0].numpy().copy(), []
    for i in range(N):
        z = Ab[0, i].numpy() @ z + Bb[0, i].numpy() @ Ubar[0, i].numpy()
        Zs.append(z.copy())
    err = float(np.max(np.abs(F + G.reshape(N, 10, N * 2) @ Ubar[0].numpy().reshape(-1)
                                - np.asarray(Zs))))
    check("T4 nominal_rollout schedule consistent with states", ok,
          "max|err|=%.3e" % worst)
    check("T4b frozen affine map reproduces the frozen rollout", err < 1e-4,
          "max|err|=%.3e" % err)
    # schedule really depends on the measurement (chi = x_k) for M5
    with torch.no_grad():
        d1 = model.B_of(torch.tensor([[0.0, 0.0]]))
        d2 = model.B_of(torch.tensor([[5.0, -3.0]]))
    check("T4c M5 input map depends on the measurement state",
          float(torch.max(torch.abs(d1 - d2))) > 1e-6,
          "max|dB|=%.3e" % float(torch.max(torch.abs(d1 - d2))))
    # column norms of U_A, V_A, U_B, V_B are <= 1
    uA, vA = model.mod_A.columns()
    uB, vB = model.mod_B.columns()
    check("T4d low-rank column norms <= 1",
          float(max(uA.norm(dim=0).max(), vA.norm(dim=0).max(),
                    uB.norm(dim=0).max(), vB.norm(dim=0).max())) <= 1.0 + 1e-6)


# ---------------------------------------------------------------- 5. LTI degeneracy
def t5_lti_degeneracy():
    torch.manual_seed(5)
    m_base = build_model("M_base", seed=5)      # A0B0 variant
    m_base.eval()
    N = 4
    xh = torch.randn(1, 8, 2)
    uin = torch.randn(1, 7, 2)
    Ubar = torch.randn(1, N, 2)
    with torch.no_grad():
        zb, Ab, Bb = m_base.nominal_rollout(xh, uin, Ubar)
    # A0B0: schedule must be constant
    check("T5 A0B0 schedule is constant across the horizon",
          float(torch.max(torch.abs(Ab - Ab[:, :1]))) < 1e-9)
    # a truly LTI model: frozen map == full rollout exactly
    F, G = prediction_matrices(Ab[0].numpy(), Bb[0].numpy(), zb[0, 0].numpy())
    Z = F + G.reshape(N, 10, N * 2) @ Ubar[0].numpy().reshape(-1)
    # full rollout of the same LTI model (schedule recomputed each step -> same)
    # full (unfrozen) rollout of the same LTI model must equal the frozen LTV model
    with torch.no_grad():
        out = m_base.rollout(xh, uin, Ubar)
    err = float(np.max(np.abs(Z[:, :2] - out[0].numpy())))
    check("T5b LTI: frozen LTV model equals the full rollout", err < 1e-4,
          "max|err|=%.3e" % err)


# ---------------------------------------------------------------- 6. controller end-to-end
def t6_controller():
    torch.manual_seed(7)
    model = build_model("M5", seed=7, r_A=2, r_B=2, g_A=0.1, g_B=0.1)
    model.eval()
    mpc = ScheduledLTVMPC(model, N=6, Q=np.eye(2), P_term=np.eye(2),
                          R=1e-3 * np.eye(2), S=1e-2 * np.eye(2),
                          u_min=-100.0, u_max=100.0)
    P = 8
    xh = rng.normal(scale=0.5, size=(1, P, 2)).astype(np.float32)
    uin = rng.normal(scale=5.0, size=(1, P - 1, 2)).astype(np.float32)
    u_prev = np.zeros(2)
    x_ref = np.tile(np.array([[1.0, -0.5]]), (7, 1))
    u0, U, info = mpc.step(xh, uin, u_prev, x_ref)
    check("T6 controller returns a finite first input",
          np.all(np.isfinite(u0)), "u0=%s" % np.round(u0, 4))
    check("T6b QP solved inside the controller", info["solved"], info["status"])
    check("T6c cost consistency inside the controller",
          abs(info["J_quad"] - info["J_direct"]) < 1e-6 * max(1.0, abs(info["J_direct"])),
          "quad=%.8f direct=%.8f" % (info["J_quad"], info["J_direct"]))
    check("T6d inputs within the box",
          float(np.max(np.abs(U))) <= 100.0 + 1e-6)
    # determinism
    mpc2 = ScheduledLTVMPC(model, N=6, Q=np.eye(2), P_term=np.eye(2),
                           R=1e-3 * np.eye(2), S=1e-2 * np.eye(2))
    u0b, _, _ = mpc2.step(xh, uin, u_prev, x_ref)
    check("T6e deterministic for identical inputs",
          float(np.max(np.abs(u0 - u0b))) < 1e-10)
    # warm start: the shift/tail-fill policy is deterministic and IS used
    mpc3 = ScheduledLTVMPC(model, N=6, Q=np.eye(2), P_term=np.eye(2),
                           R=1e-3 * np.eye(2), S=1e-2 * np.eye(2))
    mpc3.last_U = U
    W = mpc3.warm_start(u_prev)
    check("T6f warm start shifts the previous solution and repeats the tail",
          np.allclose(W[:-1], U[1:]) and np.allclose(W[-1], U[-1]),
          "tail=%s" % np.round(W[-1], 4))
    u0c, Uc, _ = mpc3.step(xh, uin, u_prev, x_ref)
    check("T6g warm start changes the frozen schedule (hence the optimum)",
          float(np.max(np.abs(U - Uc))) > 1e-9 and np.all(np.isfinite(Uc)),
          "max|dU|=%.3e" % float(np.max(np.abs(U - Uc))))


def t7_latent_propagation():
    """The scheduled model must PROPAGATE the latent state, not re-encode it."""
    torch.manual_seed(11)
    model = build_model("M5", seed=11, r_A=2, r_B=2, g_A=0.1, g_B=0.1)
    model.eval()
    calls = {"n": 0}

    def hook(*_a):
        calls["n"] += 1

    h = model.encoder.register_forward_hook(hook)
    xh = torch.randn(2, 8, 2)
    uin = torch.randn(2, 7, 2)
    uf = torch.randn(2, 12, 2)
    with torch.no_grad():
        out = model.rollout(xh, uin, uf)
    h.remove()
    check("T7 encoder is applied exactly once per rollout (latent propagation)",
          calls["n"] == 1, "encoder calls=%d" % calls["n"])
    with torch.no_grad():
        first = model.predict(xh, uin, uf[:, 0, :])
    check("T7b rollout step 0 equals the one-step prediction",
          float(torch.max(torch.abs(out[:, 0] - first))) < 1e-6)
    # the rollout must depend on the future control inputs
    with torch.no_grad():
        out2 = model.rollout(xh, uin, uf + 1.0)
    check("T7c rollout depends on the future control inputs",
          float(torch.max(torch.abs(out - out2))) > 1e-6)


def t8_gate5_helper_consistency():
    """The Gate-5 helper ``roll(..., freeze=None)`` must reproduce the model's own
    rollout exactly -- otherwise the freezing statistics would not be comparable
    with the Gate-1 numbers."""
    torch.manual_seed(13)
    sys.path.insert(0, os.path.join(EXP, "scripts"))
    from run_gate5 import roll as g5_roll
    for spec in ("M5", "M4", "M_base"):
        model = build_model(spec, seed=13, r_A=2, r_B=2, g_A=0.1, g_B=0.1)
        model.eval()
        xh = torch.randn(3, 8, 2)
        uin = torch.randn(3, 7, 2)
        U = torch.randn(3, 6, 2)
        with torch.no_grad():
            a = model.rollout(xh, uin, U)
            Z, _, _, _ = g5_roll(model, xh, uin, U)
        err = float(torch.max(torch.abs(a - Z[:, 1:, :2])))
        check("T8 %s: Gate-5 helper matches the model rollout" % spec, err < 1e-6,
              "max|err|=%.3e" % err)


def main():
    for fn in (t1_prediction_matrices, t2_objective, t3_solver, t4_nominal_rollout,
               t5_lti_degeneracy, t6_controller, t7_latent_propagation,
               t8_gate5_helper_consistency):
        try:
            fn()
        except Exception as exc:                      # noqa: BLE001
            check("%s raised %r" % (fn.__name__, exc), False)
    n = len(RESULTS)
    npass = sum(1 for _, ok, _ in RESULTS if ok)
    print("\n%d/%d tests passed" % (npass, n))
    return 0 if npass == n else 1


if __name__ == "__main__":
    sys.exit(main())
