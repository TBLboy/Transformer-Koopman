# -*- coding: utf-8 -*-
"""Exact error decomposition with a numerical closure check (no retraining).

Implements the decomposition in the GPT review (sections 2.1-2.3, 4):

    e_i      = z_i^prop - z_i^enc
    r_i      = A(c_i^enc) z_i^enc + B(x_i) u_i - z_{i+1}^enc        (full latent residual)
    q_i      = r_i + [A(c_i^prop) - A(c_i^enc)] z_i^enc + [B(chi_i^prop) - B(chi_i^enc)] u_i
    e_{i+1}  = A(c_i^prop) e_i + q_i                                (exact, no linearisation)
    e_H      = sum_{i<H} Phi(H,i+1) q_i ,  Phi(H,j) = A_{H-1}...A_j ,  Phi(H,H)=I

Output error split by the measurement / hidden block of q_i:

    C e_H = sum_i C Phi(H,i+1) P_x q_i  +  sum_i C Phi(H,i+1) P_psi q_i
          = (observed-channel injection) + (cross-coupling-mediated leakage)

Gates (GPT section 4 acceptance criterion): if the reconstruction does not close to
floating-point precision, no claim of "quantitatively verified accumulated leakage"
may be made.  Both the SUM OF NORMS and the NORM OF THE VECTOR SUM are reported so
that conservative bounds are not confused with actual coherent accumulation.

Run:
  python scripts/probe_error_closure.py                # GPU (default)
  python scripts/probe_error_closure.py --cpu          # if the GPU is busy
  python scripts/probe_error_closure.py --device arm_3link
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "models"))
sys.path.insert(0, os.path.join(EXP, "controllers"))
sys.path.insert(0, HERE)

import device as dev                      # noqa: E402
dev.bootstrap_from_argv()

import protocol as proto                    # noqa: E402
import run_gate1 as g1                      # noqa: E402
import run_gate2 as g2                      # noqa: E402
from library import N_STATE                 # noqa: E402

RESULTS = dev.results_dir("modeling")
SAMPLE = [1, 5, 25, 40, 60, 100]


def true_windows(S, Ufull, P, i):
    return S[:, i:i + P, :], Ufull[:, i:i + P - 1, :]


def collect(model, Xh, Uin, XF, UF):
    """Walk the free rollout and record everything the decomposition needs."""
    H = UF.shape[1]
    P = Xh.shape[1]
    S, Ufull = true_sequences(Xh, Uin, XF, UF)
    with torch.no_grad():
        zp = model.encoder(Xh)
        ze = model.encoder(S[:, 0:P, :])
        xbuf, ubuf = Xh.clone(), Uin.clone()
        A_p, A_e, B_p, B_e, R, U, ZE, E = [], [], [], [], [], [], [], []
        for i in range(H):
            xh_t, ui_t = true_windows(S, Ufull, P, i)
            cp, ce = model.ctx(xbuf, ubuf), model.ctx(xh_t, ui_t)
            Ap, Ae = model.A_of(cp), model.A_of(ce)
            Bp = model.B_of(zp[:, :N_STATE])
            Be = model.B_of(ze[:, :N_STATE])
            u = UF[:, i, :]
            ze_next = model.encoder(S[:, i + 1:i + 1 + P, :])
            ri = (torch.bmm(Ae, ze.unsqueeze(-1)).squeeze(-1)
                  + torch.bmm(Be, u.unsqueeze(-1)).squeeze(-1) - ze_next)
            A_p.append(Ap); A_e.append(Ae); B_p.append(Bp); B_e.append(Be)
            R.append(ri); U.append(u); ZE.append(ze); E.append(zp - ze)
            zp = (torch.bmm(Ap, zp.unsqueeze(-1)).squeeze(-1)
                  + torch.bmm(Bp, u.unsqueeze(-1)).squeeze(-1))
            ze = ze_next
            xbuf = torch.cat([xbuf[:, 1:, :], zp[:, :N_STATE].unsqueeze(1)], dim=1)
            ubuf = torch.cat([ubuf[:, 1:, :], u.unsqueeze(1)], dim=1)
        E.append(zp - ze)                      # e_H
    return {"A_p": A_p, "A_e": A_e, "B_p": B_p, "B_e": B_e, "R": R, "U": U,
            "ZE": ZE, "E": E, "H": H, "d": zp.shape[1]}


def true_sequences(Xh, Uin, XF, UF):
    return torch.cat([Xh, XF], dim=1), torch.cat([Uin, UF], dim=1)


def q_terms(rec, i):
    """q_i split into its three exact sub-contributions."""
    dA = rec["A_p"][i] - rec["A_e"][i]
    dB = rec["B_p"][i] - rec["B_e"][i]
    ze = rec["ZE"][i]
    u = rec["U"][i]
    t_res = rec["R"][i]
    t_A = torch.bmm(dA, ze.unsqueeze(-1)).squeeze(-1)
    t_B = torch.bmm(dB, u.unsqueeze(-1)).squeeze(-1)
    return t_res, t_A, t_B


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", "-d", default=None)
    ap.add_argument("--n-batch", type=int, default=30)
    ap.add_argument("--cpu", action="store_true")
    ap.add_argument("--seeds", default=None,
                    help="comma-separated seeds; default = auto-detect from the "
                         "checkpoints of M4 (soft has only seed 0; the arm has 0,1,2)")
    args = ap.parse_args()
    if args.cpu:
        g1.DEV = "cpu"
        print("[cpu] run_gate1.DEV forced to 'cpu'")

    ledger = json.load(io.open(os.path.join(RESULTS, "gate1_ledger.json"), encoding="utf-8"))
    cfg = g2.paired_cfg(ledger["best"]["M5"]["cfg"])
    H = proto.HORIZONS["long"]
    w, _ = g1.tensors("test", H, frozen_eval=True)
    idx = np.arange(min(args.n_batch, len(w["k"])))
    Xh, Uin = g1.batchify(w, "Xh", idx), g1.batchify(w, "Uin", idx)
    XF, UF = g1.batchify(w, "XF", idx), g1.batchify(w, "UF", idx)

    dname = dev.current()["name"]
    ck = dev.checkpoints_dir()
    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(",")]
    else:
        seeds = [0] + [s for s in (1, 2) if os.path.exists(os.path.join(ck, "M4_seed%d.pt" % s))]
    print("seeds = %s   (checkpoint dir: %s)" % (seeds, ck))
    n = N_STATE

    def analyse(model, Xh, Uin, XF, UF):
        """Everything for one (variant, seed). Returns a plain dict."""
        rec = collect(model, Xh, Uin, XF, UF)
        Hh, d = rec["H"], rec["d"]
        err_rec = max(
            float((rec["E"][i + 1]
                   - (torch.bmm(rec["A_p"][i], rec["E"][i].unsqueeze(-1)).squeeze(-1)
                      + sum(q_terms(rec, i)))).abs().max())
            for i in range(Hh))
        scale = float(torch.linalg.vector_norm(rec["E"][Hh], dim=1).mean())
        dev_ = rec["E"][Hh].device
        Px = torch.zeros(d, d, device=dev_)
        Ppsi = torch.zeros(d, d, device=dev_)
        for k in range(n):
            Px[k, k] = 1.0
        for k in range(n, d):
            Ppsi[k, k] = 1.0
        Px_b = Px.unsqueeze(0).repeat(Xh.shape[0], 1, 1)
        Ppsi_b = Ppsi.unsqueeze(0).repeat(Xh.shape[0], 1, 1)

        Phi = torch.eye(d, device=dev_).unsqueeze(0).repeat(Xh.shape[0], 1, 1)
        vecx = torch.zeros_like(rec["E"][Hh])
        vecp = torch.zeros_like(rec["E"][Hh])
        sumx = 0.0
        sump = 0.0
        for i in range(Hh - 1, -1, -1):
            q = sum(q_terms(rec, i))
            cx = torch.bmm(Phi, (Px @ q.unsqueeze(-1))).squeeze(-1)
            cp = torch.bmm(Phi, (Ppsi @ q.unsqueeze(-1))).squeeze(-1)
            vecx += cx
            vecp += cp
            sumx += float(torch.linalg.vector_norm(cx, dim=1).mean())
            sump += float(torch.linalg.vector_norm(cp, dim=1).mean())
            Phi = torch.bmm(Phi, rec["A_p"][i])      # Phi(H,i) = Phi(H,i+1) A_i
        conv_err = float((vecx + vecp - rec["E"][Hh]).abs().max()) / max(scale, 1e-12)

        per_h = {"h": [], "obs": [], "leak": [], "G_x": [], "G_psi": []}
        for h in range(1, Hh + 1):
            Phi = torch.eye(d, device=dev_).unsqueeze(0).repeat(Xh.shape[0], 1, 1)
            acc_x = torch.zeros_like(rec["E"][Hh])
            acc_p = torch.zeros_like(rec["E"][Hh])
            Gx = 0.0
            Gp = 0.0
            for i in range(h - 1, -1, -1):
                q = sum(q_terms(rec, i))
                acc_x += torch.bmm(Phi, (Px @ q.unsqueeze(-1))).squeeze(-1)
                acc_p += torch.bmm(Phi, (Ppsi @ q.unsqueeze(-1))).squeeze(-1)
                # ||C Phi P_*||_2: C selects the first n rows, so use the spectral
                # norm of the n x d submatrix, not of the full d x d product.
                Gx += float(torch.linalg.matrix_norm(torch.bmm(Phi, Px_b)[:, :n, :], ord=2).mean())
                Gp += float(torch.linalg.matrix_norm(torch.bmm(Phi, Ppsi_b)[:, :n, :], ord=2).mean())
                Phi = torch.bmm(Phi, rec["A_p"][i])
            per_h["h"].append(h)
            per_h["obs"].append(float(torch.linalg.vector_norm(acc_x, dim=1).mean()))
            per_h["leak"].append(float(torch.linalg.vector_norm(acc_p, dim=1).mean()))
            per_h["G_x"].append(Gx)
            per_h["G_psi"].append(Gp)

        sub = {"residual": [], "schedA": [], "schedB": []}
        for i in range(Hh):
            t_res, t_A, t_B = q_terms(rec, i)
            sub["residual"].append(float(torch.linalg.vector_norm(t_res, dim=1).mean()))
            sub["schedA"].append(float(torch.linalg.vector_norm(t_A, dim=1).mean()))
            sub["schedB"].append(float(torch.linalg.vector_norm(t_B, dim=1).mean()))
        return {
            "closure_recursion_max_abs": err_rec,
            "closure_convolution_rel_err": conv_err,
            "e_H_norm_mean": scale,
            "e_H_observed_norm_mean": float(
                torch.linalg.vector_norm(rec["E"][Hh][:, :n], dim=1).mean()),
            "sum_of_norms": {"x": sumx, "psi": sump},
            "norm_of_vector_sum": {"x": float(torch.linalg.vector_norm(vecx, dim=1).mean()),
                                   "psi": float(torch.linalg.vector_norm(vecp, dim=1).mean())},
            "per_horizon": per_h,
            "q_subcontrib_means": {k: float(np.mean(v)) for k, v in sub.items()},
        }

    out = {"device": dname, "horizon": H, "n_batch": int(len(idx)),
           "paired_cfg": cfg, "seeds": seeds, "variants": {}}

    for variant, spec in (("AcB0", "M4"), ("AcBx", "M5")):
        per_seed, infos = {}, {}
        for seed in seeds:
            model, info = g1.load_or_train(spec, cfg, seed=seed)
            infos[str(seed)] = info
            per_seed[str(seed)] = analyse(model, Xh, Uin, XF, UF)
            g1.free()

        def arr(key):
            return {h: {"mean": float(np.mean([per_seed[str(s)]["per_horizon"][key][h - 1]
                                               for s in seeds])),
                        "std": float(np.std([per_seed[str(s)]["per_horizon"][key][h - 1]
                                             for s in seeds]))} for h in SAMPLE}

        out["variants"][variant] = {
            "spec": spec, "load_info": infos, "per_seed": per_seed,
            "closure_recursion_max_abs_max": max(per_seed[str(s)]["closure_recursion_max_abs"]
                                                 for s in seeds),
            "closure_convolution_rel_err_max": max(per_seed[str(s)]["closure_convolution_rel_err"]
                                                   for s in seeds),
            "aggregate": {k: {"mean": float(np.mean([per_seed[str(s)][k] for s in seeds])),
                              "std": float(np.std([per_seed[str(s)][k] for s in seeds]))}
                          for k in ("e_H_norm_mean", "e_H_observed_norm_mean")},
            "sum_of_norms": {k: {"mean": float(np.mean([per_seed[str(s)]["sum_of_norms"][k]
                                                        for s in seeds])),
                                 "std": float(np.std([per_seed[str(s)]["sum_of_norms"][k]
                                                      for s in seeds]))}
                             for k in ("x", "psi")},
            "norm_of_vector_sum": {k: {"mean": float(np.mean([per_seed[str(s)]["norm_of_vector_sum"][k]
                                                              for s in seeds])),
                                       "std": float(np.std([per_seed[str(s)]["norm_of_vector_sum"][k]
                                                            for s in seeds]))}
                                   for k in ("x", "psi")},
            "per_horizon": {k: arr(k) for k in ("obs", "leak", "G_x", "G_psi")},
        }

        V = out["variants"][variant]
        print("=" * 96)
        print("%s (%s)  device=%s  seeds=%s" % (variant, spec, dname, seeds))
        print("=" * 96)
        print("  CLOSURE  recursion  max over seeds = %.3e" % V["closure_recursion_max_abs_max"])
        print("  CLOSURE  convolution rel err      = %.3e" % V["closure_convolution_rel_err_max"])
        print("  gate: both must be at floating-point level (<=1e-5 rel) before any")
        print("        'quantitatively verified leakage' claim.")
        print()
        print("  ||e_H|| all d = %.4f+-%.4f ; ||C e_H|| observed = %.4f+-%.4f"
              % (V["aggregate"]["e_H_norm_mean"]["mean"], V["aggregate"]["e_H_norm_mean"]["std"],
                 V["aggregate"]["e_H_observed_norm_mean"]["mean"],
                 V["aggregate"]["e_H_observed_norm_mean"]["std"]))
        print("  decomposition of C e_H at h=%d (mean over seeds):" % H)
        print("    sum of norms      : observed=%.4f  leakage=%.4f  total=%.4f"
              % (V["sum_of_norms"]["x"]["mean"], V["sum_of_norms"]["psi"]["mean"],
                 V["sum_of_norms"]["x"]["mean"] + V["sum_of_norms"]["psi"]["mean"]))
        print("    norm of vector sum: observed=%.4f  leakage=%.4f  total=%.4f"
              % (V["norm_of_vector_sum"]["x"]["mean"], V["norm_of_vector_sum"]["psi"]["mean"],
                 V["norm_of_vector_sum"]["x"]["mean"] + V["norm_of_vector_sum"]["psi"]["mean"]))
        print()
        print("  %-6s %20s %20s %14s %14s"
              % ("h", "obs-inject", "leakage", "G_x,H", "G_psi,H"))
        for h in SAMPLE:
            print("  %-6d %20s %20s %14.4f %14.4f"
                  % (h,
                     "%.4f±%.4f" % (V["per_horizon"]["obs"][h]["mean"],
                                    V["per_horizon"]["obs"][h]["std"]),
                     "%.4f±%.4f" % (V["per_horizon"]["leak"][h]["mean"],
                                    V["per_horizon"]["leak"][h]["std"]),
                     V["per_horizon"]["G_x"][h]["mean"],
                     V["per_horizon"]["G_psi"][h]["mean"]))
        print()
        print("  mean ||q_i|| sub-contributions (seed 0):")
        print("    residual r_i = %.5f | schedule dA = %.5f | schedule dB = %.5f"
              % (per_seed[str(seeds[0])]["q_subcontrib_means"]["residual"],
                 per_seed[str(seeds[0])]["q_subcontrib_means"]["schedA"],
                 per_seed[str(seeds[0])]["q_subcontrib_means"]["schedB"]))
        print()

    path = os.path.join(RESULTS, "error_closure_%s.json" % dname)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("written -> %s" % path)


if __name__ == "__main__":
    main()
