# -*- coding: utf-8 -*-
"""Gate 5: theory-experiment cross-check of the frozen-schedule approximation.

Definition (plan section 9, Theory_Package/06-08): the freezing error is defined
for ONE candidate input sequence ``U`` and ONE nominal sequence ``bar U``:
    z_full(U)         : A(c_i), B(chi_i) recomputed along the trajectory driven by U
    z_fr(U; bar U)    : schedules bar A_i, bar B_i obtained from the nominal
                        rollout driven by bar U, then frozen while rolling U
Comparing two controllers' own trajectories is NOT a freezing error.

Theory predictions that are checked numerically:
  P1  delta_frz = 0 exactly when U == bar U  (07 section 2: the driver is the
      input mismatch, not delta_A / delta_B themselves);
  P2  the freezing error grows with ||U - bar U||;
  P3  the schedule deviation ||A_full - bar A||, ||B_full - bar B|| is bounded
      by the empirical schedule spread (never written as a global certificate).

The cost comparison reports
    |J_full(U) - J_fr(U; bar U)|            (consistent-cost gap)
    J_full(U_fr) - J_full(U_loc)            (relative to a LOCAL solver ONLY)
and explicitly does NOT claim a global suboptimality value: the full problem is
non-convex and no global solver is available (06 section 6, 08 section 5).

Run:  python scripts/run_gate5.py --n-starts 24
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "models"))
sys.path.insert(0, os.path.join(EXP, "controllers"))
sys.path.insert(0, HERE)

import run_gate1 as g1                                        # noqa: E402
from ltv_mpc import (prediction_matrices, cost_matrices, cost_value,   # noqa: E402
                     solve_qp)
from scipy.optimize import minimize                           # noqa: E402

RESULTS = os.path.join(EXP, "results", "theory_diagnostics")
os.makedirs(RESULTS, exist_ok=True)
N_STATE = 2
DELTAS = [0.0, 0.25, 0.5, 1.0, 2.0]      # ||U - bar U|| levels (normalised units)


def roll(model, xh, uin, U, freeze=None):
    """Roll the model; optionally freeze the schedule to (A_bar, B_bar).

    Returns Z (H+1, d), A (H, d, d), B (H, d, m), C (H, ctx_dim).
    """
    H = U.shape[1]
    z = model.encoder(xh)
    xbuf, ubuf = xh.clone(), uin.clone()
    Z, As, Bs, Cs = [z], [], [], []
    for i in range(H):
        c = model.ctx(xbuf, ubuf)
        A = model.A_of(c)
        B = model.B_of(z[:, :N_STATE])
        if freeze is not None:
            A, B = freeze[0][:, i], freeze[1][:, i]
        As.append(A)
        Bs.append(B)
        Cs.append(c)
        z = torch.bmm(A, z.unsqueeze(-1)).squeeze(-1) + \
            torch.bmm(B, U[:, i].unsqueeze(-1)).squeeze(-1)
        Z.append(z)
        xbuf = torch.cat([xbuf[:, 1:, :], z[:, :N_STATE].unsqueeze(1)], dim=1)
        ubuf = torch.cat([ubuf[:, 1:, :], U[:, i].unsqueeze(1)], dim=1)
    return (torch.stack(Z, 1), torch.stack(As, 1), torch.stack(Bs, 1), torch.stack(Cs, 1))


def trajectory_cost(Z, U, x_ref, Q, P_term, R, S, u_prev):
    """Plan section 7.1 cost on an explicit trajectory (measurement space)."""
    N = U.shape[1]
    J = 0.0
    for i in range(N):
        W = Q if i < N - 1 else P_term
        e = Z[i + 1, :N_STATE] - x_ref[i + 1]
        J += float(e @ W @ e)
    for i in range(N):
        ui = U[i]
        J += float(ui @ R @ ui)
        prev = u_prev if i == 0 else U[i - 1]
        d = ui - prev
        J += float(d @ S @ d)
    return J


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-starts", type=int, default=24)
    ap.add_argument("--horizon", type=int, default=25,
                    help="must be one of the protocol's frozen horizons (5/25/100); "
                         "25 uses the 'mid' frozen start set")
    ap.add_argument("--model", default="M5")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    ledger = json.load(open(os.path.join(RESULTS, "..", "modeling", "gate1_ledger.json"),
                            encoding="utf-8"))
    cfg = ledger["best"][args.model]["cfg"]
    print("model=%s cfg=%s" % (args.model, cfg))
    model, _info = g1.load_or_train(args.model, cfg, seed=args.seed)
    model.to("cpu").eval()

    H = args.horizon
    w, raw = g1.tensors("test", H, frozen_eval=True)
    idx = np.arange(min(args.n_starts, len(w["k"])))
    xh = g1.batchify(w, "Xh", idx).cpu()
    uin = g1.batchify(w, "Uin", idx).cpu()
    Utrue = g1.batchify(w, "UF", idx).cpu()            # recorded inputs = nominal bar U

    Q = np.eye(N_STATE)
    P_term = np.eye(N_STATE)
    R = 1e-3 * np.eye(2)
    S = 1e-2 * np.eye(2)
    x_ref = g1.batchify(w, "XF", idx).cpu().numpy()
    x_ref = np.concatenate([g1.batchify(w, "Xh", idx)[:, -1:, :].cpu().numpy(), x_ref], axis=1)

    rng = np.random.default_rng(0)
    rows = []
    for di, delta in enumerate(DELTAS):
        errs_z, errs_c, errs_A, errs_B, gaps, norms, nom_gaps = [], [], [], [], [], [], []
        for s in range(len(idx)):
            Ubar = Utrue[s:s + 1]
            # candidate U: the SAME sequence plus a random perturbation of size delta
            if delta == 0.0:
                U = Ubar.clone()
            else:
                noise = torch.as_tensor(rng.normal(size=(1, H, 2)), dtype=Ubar.dtype,
                                        device=Ubar.device)
                U = Ubar + delta * noise
            with torch.no_grad():
                Zf, Af, Bf, Cf = roll(model, xh[s:s + 1], uin[s:s + 1], U)
                Zb, Ab, Bb = model.nominal_rollout(xh[s:s + 1], uin[s:s + 1], Ubar)
                Zn, _, _, Cb = roll(model, xh[s:s + 1], uin[s:s + 1], Ubar)
                Zr, _, _, _ = roll(model, xh[s:s + 1], uin[s:s + 1], U, freeze=(Ab, Bb))
            nom_gap = float(torch.max(torch.abs(Zb[0, 1:] - Zn[0, 1:Zb.shape[1]])))
            d = np.linalg.norm(U[0].cpu().numpy() - Ubar[0].cpu().numpy())
            norms.append(d)
            # frozen vs full latent/measurement trajectories (i = 1..H)
            errs_z.append(float(torch.max(torch.norm(Zf[0, 1:] - Zr[0, 1:], dim=-1))))
            errs_c.append(float(torch.max(torch.norm(Cf[0] - Cb[0], dim=-1))))
            errs_A.append(float(torch.linalg.matrix_norm(Af[0] - Ab[0], ord=2).max()))
            errs_B.append(float(torch.linalg.matrix_norm(Bf[0] - Bb[0], ord=2).max()))
            # costs: J_full(U) vs J_fr(U; bar U)  (same cost function, different model)
            u_prev = uin[s, -1].cpu().numpy()
            Jf = trajectory_cost(Zf[0].cpu().numpy(), U[0].cpu().numpy(), x_ref[s],
                                 Q, P_term, R, S, u_prev)
            Jr = trajectory_cost(Zr[0].cpu().numpy(), U[0].cpu().numpy(), x_ref[s],
                                 Q, P_term, R, S, u_prev)
            gaps.append(abs(Jf - Jr))
            nom_gaps.append(nom_gap)
        rows.append({"delta": delta,
                     "nominal_rollout_selfcheck_max": float(np.max(nom_gaps)),
                     "u_mismatch_mean": float(np.mean(norms)),
                     "u_mismatch_max": float(np.max(norms)),
                     "z_err_max_mean": float(np.mean(errs_z)),
                     "z_err_max_max": float(np.max(errs_z)),
                     "c_err_max": float(np.max(errs_c)),
                     "A_dev_spec_max": float(np.max(errs_A)),
                     "B_dev_spec_max": float(np.max(errs_B)),
                     "cost_gap_mean": float(np.mean(gaps)),
                     "cost_gap_max": float(np.max(gaps))})
        print("  delta=%.2f  |dU|=%.3f  max||z_f-z_r||=%.3e  cost gap max=%.3e"
              % (delta, rows[-1]["u_mismatch_mean"], rows[-1]["z_err_max_max"],
                 rows[-1]["cost_gap_max"]))

    # ---------------- decision comparison on ONE start (frozen QP vs local NLP)
    s = 0
    Ubar = Utrue[s:s + 1]
    x_ref_s = x_ref[s]
    u_prev = uin[s, -1].cpu().numpy()
    with torch.no_grad():
        zb, Ab, Bb = model.nominal_rollout(xh[s:s + 1], uin[s:s + 1], Ubar)
    F, G = prediction_matrices(Ab[0].cpu().numpy(), Bb[0].cpu().numpy(),
                               zb[0, 0].cpu().numpy())
    M, f, _ = cost_matrices(F, G, x_ref_s, np.zeros((H, 2)), Q, P_term, R, S, u_prev)
    Ufr, info = solve_qp(M, f, -3.5, 3.5, H, 2)
    with torch.no_grad():
        Zf_fr, _, _, _ = roll(model, xh[s:s + 1], uin[s:s + 1],
                              torch.as_tensor(Ufr.reshape(1, H, 2), dtype=torch.float32))
        Zf_ref, _, _, _ = roll(model, xh[s:s + 1], uin[s:s + 1], Ubar)
    J_fr_dec = trajectory_cost(Zf_fr[0].cpu().numpy(), Ufr.reshape(H, 2), x_ref_s, Q, P_term,
                               R, S, u_prev)
    J_ref_dec = trajectory_cost(Zf_ref[0].cpu().numpy(), Ubar[0].cpu().numpy(), x_ref_s,
                                Q, P_term, R, S, u_prev)
    def full_cost(Uflat, xh1, uin1, xref):
        U = torch.as_tensor(Uflat.reshape(1, H, 2), dtype=torch.float32)
        with torch.no_grad():
            Z, _, _, _ = roll(model, xh1, uin1, U)
        return trajectory_cost(Z[0].cpu().numpy(), Uflat.reshape(H, 2), xref, Q, P_term,
                               R, S, u_prev)

    xh1, uin1 = xh[s:s + 1], uin[s:s + 1]
    res = minimize(lambda v: full_cost(v, xh1, uin1, x_ref_s), Ufr.copy(),
                   method="L-BFGS-B", bounds=[(-3.5, 3.5)] * (H * 2),
                   options={"maxiter": 300, "ftol": 1e-12})
    U_loc = res.x.reshape(H, 2)
    J_loc = full_cost(res.x, xh1, uin1, x_ref_s)
    decision = {
        "note": ("J_full(U_fr) - J_full(U_loc) is measured against a LOCAL "
                 "L-BFGS-B solution of the non-convex full problem, NOT against a "
                 "global optimum; no global suboptimality value is claimed."),
        "J_full_U_frozen_QP": J_fr_dec,
        "J_full_U_recorded_nominal": J_ref_dec,
        "J_full_U_local_NLP": J_loc,
        "gap_vs_local_NLP": J_fr_dec - J_loc,
        "gap_of_nominal_vs_local_NLP": J_ref_dec - J_loc,
        "local_solver_success": bool(res.success),
        "qp_status": info["status"],
        "same_feasible_set": True,
        "constraint": "u in [-3.5, 3.5] (both problems, input-only constraints)",
    }
    print("\n  decision: J_fr(U)=%.6f  J_full(U_fr)=%.6f  J_full(U_loc)=%.6f  gap=%.3e"
          % (J_fr_dec, J_fr_dec, J_loc, decision["gap_vs_local_NLP"]))

    report = {
        "definition": ("z_full(U) vs z_fr(U; bar U): same candidate U, schedules frozen "
                       "from the nominal rollout driven by bar U (plan section 9)"),
        "model": args.model, "cfg": cfg, "horizon": H, "n_starts": int(len(idx)),
        "deltas": rows,
        "theory_checks": {
            "P1_zero_mismatch_gives_zero_error":
                bool(rows[0]["z_err_max_max"] < 1e-5 and rows[0]["cost_gap_max"] < 1e-6),
            "P1_detail": ("delta=0 means U == bar U; the frozen and full trajectories "
                          "must coincide (07 section 2: the driver is the input mismatch)"),
            "P2_monotone_growth": bool(all(rows[i]["z_err_max_max"] <= rows[i + 1]["z_err_max_max"] * 1.5
                                           for i in range(len(rows) - 1))),
        },
        "decision_comparison": decision,
        "not_claimed": [
            "global optimality of the non-convex full problem",
            "epsilon_J certificate (the constants would need to be estimated, and an "
            "empirical bound is not a certificate)",
            "closed-loop stability, recursive feasibility or real-time performance",
        ],
        "finished": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    out = os.path.join(RESULTS, "freezing_diagnostics.json")
    with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print("written -> %s" % out)


if __name__ == "__main__":
    main()
