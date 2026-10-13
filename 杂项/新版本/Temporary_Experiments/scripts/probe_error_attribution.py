# -*- coding: utf-8 -*-
"""Probe: attribute the long-horizon blow-up of A(c)-scheduled models.

The transient-growth probe showed that the *homogeneous* linear gain
``||A(c_{h-1}) ... A(c_0)||_2`` is only ~3 after 100 steps, while the rollout error
grows ~22x. So the growth cannot come from error propagation. This probe isolates
the remaining two candidates by running three rollouts per model:

  free     : as trained -- context c from the model's own (drifting) window
  tf_ctx   : context c taken from the TRUE window at every step, latent state still
             propagated by the model  (removes context drift, keeps error propagation)
  tf_both  : context AND latent reset to the truth every step -> pure one-step
             residual accumulation, no propagation at all

Reading:
  free >> tf_ctx   -> context drift is the dominant driver
  free ~= tf_ctx   -> propagation/residual is the driver, not the schedule
  tf_both curve    -> how the raw one-step residual accumulates over 100 steps

Run:
  python scripts/probe_error_attribution.py --device arm_3link
  python scripts/probe_error_attribution.py
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
SAMPLE = [1, 2, 5, 10, 25, 40, 60, 80, 100]


def true_sequences(Xh, Uin, XF, UF):
    """Full true state/input sequences aligned to the rollout start.

    S[j]     = x_{k-P+1+j}   (so S[0:P] == Xh, S[P:P+H] == XF)
    Ufull[j] = u_{k-P+1+j}   (so Ufull[0:P-1] == Uin, Ufull[P-1:P-1+H] == UF)
    """
    S = torch.cat([Xh, XF], dim=1)
    Ufull = torch.cat([Uin, UF], dim=1)
    return S, Ufull


def true_windows(S, Ufull, P, i):
    """Window at rollout step i, taken from the true sequences."""
    return S[:, i:i + P, :], Ufull[:, i:i + P - 1, :]


def rollout_variant(model, Xh, Uin, XF, UF, mode):
    """Return (pred, A_list).

    mode:
      free            as trained -- context from the model's own drifting window
      tf_ctx          A-context from the TRUE window; B(chi) still sees the propagated state
      tf_ctx_chi      A-context from the TRUE window AND chi = x_true (both schedules frozen)
      tf_both         context AND latent reset to truth (pure one-step residual)
      no_leak         free, but the x<-psi coupling block A[:n, n:] is zeroed
      ctrl_no_reverse free, but the psi<-x coupling block A[n:, :n] is zeroed
                      (contrast, NOT a strict null control: changing A[psi,x] alters
                      psi, which still feeds back into x through A[x,psi])
    """
    H = UF.shape[1]
    P = Xh.shape[1]
    S, Ufull = true_sequences(Xh, Uin, XF, UF)
    block_x_psi = mode == "no_leak"
    block_psi_x = mode == "ctrl_no_reverse"
    with torch.no_grad():
        z = model.encoder(Xh)
        xbuf, ubuf = Xh.clone(), Uin.clone()
        outs, As = [], []
        for i in range(H):
            xh_t, ui_t = true_windows(S, Ufull, P, i)
            if mode in ("free", "no_leak", "ctrl_no_reverse"):
                c = model.ctx(xbuf, ubuf)
                chi = z[:, :N_STATE]
            elif mode == "tf_ctx":
                # only the A-context is frozen; B(chi) still sees the PROPAGATED
                # measurement (chi = C z_prop), so the B-schedule drift remains.
                c = model.ctx(xh_t, ui_t)
                chi = z[:, :N_STATE]
            elif mode == "tf_ctx_chi":
                # both schedules frozen: A-context from the true window AND
                # B's argument chi = C z_enc = x_true (exact, since z[:n] == x).
                c = model.ctx(xh_t, ui_t)
                chi = S[:, i + P - 1, :]
            else:  # tf_both: no propagation at all
                c = model.ctx(xh_t, ui_t)
                z = model.encoder(xh_t)
                chi = z[:, :N_STATE]
            A = model.A_of(c)
            if block_x_psi:
                A = A.clone()
                A[:, :N_STATE, N_STATE:] = 0.0
            if block_psi_x:
                A = A.clone()
                A[:, N_STATE:, :N_STATE] = 0.0
            Bm = model.B_of(chi)
            As.append(A)
            u = UF[:, i, :]
            z = torch.bmm(A, z.unsqueeze(-1)).squeeze(-1) + \
                torch.bmm(Bm, u.unsqueeze(-1)).squeeze(-1)
            outs.append(z[:, :N_STATE])
            xbuf = torch.cat([xbuf[:, 1:, :], z[:, :N_STATE].unsqueeze(1)], dim=1)
            ubuf = torch.cat([ubuf[:, 1:, :], u.unsqueeze(1)], dim=1)
    return torch.stack(outs, dim=1).detach(), torch.stack(As, dim=1).detach()


def curve(pred, tgt):
    """Per-step normalised RMSE, same convention as the ledger horizon curve."""
    d = (pred - tgt) ** 2
    return torch.sqrt(d.mean(dim=(0, 2))).cpu().numpy()


def latent_diagnostics(model, Xh, Uin, XF, UF):
    """Track where the error lives: full latent error vs the observed channels.

    zhat_j = latent of x_{k+j} produced by the model's own recursion
    zstar_j = encoder(true window ending at x_{k+j})
    Returns per-step: ||e_z|| (all d), ||e_z[:n]|| (observed), ||prod A||, encoder floor.
    """
    H = UF.shape[1]
    P = Xh.shape[1]
    S, Ufull = true_sequences(Xh, Uin, XF, UF)
    with torch.no_grad():
        zhat = model.encoder(Xh)
        zstar = model.encoder(S[:, 0:P, :])
        xbuf, ubuf = Xh.clone(), Uin.clone()
        err_full, err_obs, floor, prod = [], [], [], []
        Pmat = torch.eye(zhat.shape[1], device=zhat.device).unsqueeze(0).repeat(zhat.shape[0], 1, 1)
        for i in range(H):
            # current step: compare latent of x_{k+i}
            err_full.append(float(torch.linalg.vector_norm(zhat - zstar, dim=1).mean()))
            err_obs.append(float(torch.linalg.vector_norm((zhat - zstar)[:, :N_STATE], dim=1).mean()))
            xt = S[:, i + P - 1, :] if i + P - 1 < S.shape[1] else None
            floor.append(float(torch.linalg.vector_norm(zstar[:, :N_STATE] - xt, dim=1).mean())
                         if xt is not None else float("nan"))
            prod.append(float(torch.linalg.matrix_norm(Pmat, ord=2).mean()))
            # advance one step
            c = model.ctx(xbuf, ubuf)
            A = model.A_of(c)
            Bm = model.B_of(zhat[:, :N_STATE])
            u = UF[:, i, :]
            zhat = torch.bmm(A, zhat.unsqueeze(-1)).squeeze(-1) + \
                torch.bmm(Bm, u.unsqueeze(-1)).squeeze(-1)
            Pmat = A @ Pmat
            zstar = model.encoder(S[:, i + 1:i + 1 + P, :])
            xbuf = torch.cat([xbuf[:, 1:, :], zhat[:, :N_STATE].unsqueeze(1)], dim=1)
            ubuf = torch.cat([ubuf[:, 1:, :], u.unsqueeze(1)], dim=1)
    return err_full, err_obs, floor, prod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", "-d", default=None)
    ap.add_argument("--n-batch", type=int, default=30)
    ap.add_argument("--cpu", action="store_true",
                    help="force CPU (the GPU may be busy with a long training run)")
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
    Xh = g1.batchify(w, "Xh", idx)
    Uin = g1.batchify(w, "Uin", idx)
    XF = g1.batchify(w, "XF", idx)
    UF = g1.batchify(w, "UF", idx)

    dname = dev.current()["name"]
    ck = dev.checkpoints_dir()
    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(",")]
    else:
        seeds = [0] + [s for s in (1, 2) if os.path.exists(os.path.join(ck, "M4_seed%d.pt" % s))]
    print("seeds = %s   (checkpoint dir: %s)" % (seeds, ck))
    MODES = ("free", "tf_ctx", "tf_ctx_chi", "tf_both", "no_leak", "ctrl_no_reverse")

    out = {"device": dname, "horizon": H, "n_batch": int(len(idx)),
           "paired_cfg": cfg, "seeds": seeds, "variants": {}}
    curves = {}

    for variant, spec in (("A0B0", "M_base"), ("AcB0", "M4"), ("AcBx", "M5")):
        rec = {"spec": spec, "per_seed": {}, "load_info": {}}
        for seed in seeds:
            model, info = g1.load_or_train(spec, cfg, seed=seed)
            rec["load_info"][str(seed)] = info
            sd = {}
            for mode in MODES:
                pred, As = rollout_variant(model, Xh, Uin, XF, UF, mode)
                c = curve(pred, XF)
                sd[mode] = {h: float(c[h - 1]) for h in SAMPLE}
                curves[(variant, mode, seed)] = c
            ef, eo, fl, pr = latent_diagnostics(model, Xh, Uin, XF, UF)
            sd["latent"] = {"err_full": {h: ef[h - 1] for h in SAMPLE},
                            "err_obs": {h: eo[h - 1] for h in SAMPLE},
                            "encoder_floor": {h: fl[h - 1] for h in SAMPLE},
                            "prod_norm": {h: pr[h - 1] for h in SAMPLE}}
            rec["per_seed"][str(seed)] = sd
            g1.free()
        # aggregate: mean / std over seeds for every quantity
        agg = {}
        for mode in MODES:
            agg[mode] = {}
            for h in SAMPLE:
                v = [rec["per_seed"][str(s)][mode][h] for s in seeds]
                agg[mode][h] = {"mean": float(np.mean(v)), "std": float(np.std(v)),
                                "per_seed": {str(s): float(rec["per_seed"][str(s)][mode][h])
                                             for s in seeds}}
        for key in ("err_full", "err_obs", "prod_norm"):
            agg[key] = {}
            for h in SAMPLE:
                v = [rec["per_seed"][str(s)]["latent"][key][h] for s in seeds]
                agg[key][h] = {"mean": float(np.mean(v)), "std": float(np.std(v))}
        rec["aggregate"] = agg
        led = ledger["test"].get(spec)
        rec["ledger_check"] = (None if not led else
                               float(np.mean([r["test"]["curve"]["long"][99] for r in led])))
        out["variants"][variant] = rec

        print("=" * 96)
        print("%s (%s)  device=%s  seeds=%s" % (variant, spec, dname, seeds))
        print("=" * 96)
        print("  %-16s %s" % ("mode (mean+-sd)", "  ".join("h=%-5d" % h for h in SAMPLE)))
        for mode in MODES:
            cells = []
            for h in SAMPLE:
                a = agg[mode][h]
                cells.append("%-7.4f" % a["mean"] if a["std"] < 5e-5
                             else "%.4f±%.3f" % (a["mean"], a["std"]))
            print("  %-16s %s" % (mode, "  ".join(cells)))
        if len(seeds) > 1:
            print("  per-seed free h=100: %s"
                  % "  ".join("seed%d=%.4f" % (s, rec["per_seed"][str(s)]["free"][100])
                              for s in seeds))
        print("  ledger free h=100 (mean 3 seeds, per-step) = %s" % rec["ledger_check"])
        print("  %-14s %s" % ("latent diag", "  ".join("h=%-5d" % h for h in SAMPLE)))
        for key, lab in (("err_full", "||e_z|| all d"), ("err_obs", "||e_z[:n]|| obs"),
                         ("prod_norm", "||prod A||")):
            print("  %-14s %s" % (lab, "  ".join("%-7.4f" % agg[key][h]["mean"]
                                                 for h in SAMPLE)))
        print()

    path = os.path.join(RESULTS, "error_attribution_%s.json" % dname)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("written -> %s" % path)


if __name__ == "__main__":
    main()
