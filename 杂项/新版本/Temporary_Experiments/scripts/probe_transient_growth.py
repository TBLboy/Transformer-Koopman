# -*- coding: utf-8 -*-
"""Probe: is the long-horizon blow-up of the A(c)-scheduled models explained by
``rho(A) > 1`` alone, or by non-normal transient amplification?

For each scheduled variant we walk the model's OWN rollout (true future inputs) and
record A(c_k) at every step, then compare three quantities as a function of h:

  * ``rho_max^h``          -- what a single spectral radius predicts
  * ``||A_{h-1} ... A_0||_2`` -- the actual worst-case linear gain (transient included)
  * the observed rollout RMSE growth

If ``||prod||`` grows much faster than ``rho^h`` the mechanism is transient
amplification of a non-normal product, not merely an eigenvalue above one.

Run:
  python scripts/probe_transient_growth.py --device arm_3link
  python scripts/probe_transient_growth.py            # soft platform (default)
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


def rollout_collect_A(model, xh, uin, uf):
    """Free rollout with the true future inputs, collecting A(c_k) at every step."""
    H = uf.shape[1]
    with torch.no_grad():
        z = model.encoder(xh)
        xbuf, ubuf = xh.clone(), uin.clone()
        As = []
        for i in range(H):
            c = model.ctx(xbuf, ubuf)
            A = model.A_of(c)
            B = model.B_of(z[:, :N_STATE])
            As.append(A)
            u = uf[:, i, :]
            z = torch.bmm(A, z.unsqueeze(-1)).squeeze(-1) + \
                torch.bmm(B, u.unsqueeze(-1)).squeeze(-1)
            xbuf = torch.cat([xbuf[:, 1:, :], z[:, :N_STATE].unsqueeze(1)], dim=1)
            ubuf = torch.cat([ubuf[:, 1:, :], u.unsqueeze(1)], dim=1)
    return torch.stack(As, dim=1).detach()   # (B, H, d, d)


def product_norms(A_all):
    """mean / max over batch of ||A_{h-1} ... A_0||_2 for every h (transient envelope)."""
    B, H, d, _ = A_all.shape
    mean_n = np.zeros(H)
    max_n = np.zeros(H)
    for b in range(B):
        P = np.eye(d)
        for h in range(H):
            P = A_all[b, h].cpu().numpy() @ P
            s = float(np.linalg.svd(P, compute_uv=False)[0])
            mean_n[h] += s / B
            max_n[h] = max(max_n[h], s)
    return mean_n, max_n


def per_step_stats(A_all):
    A = A_all.cpu().numpy()
    rho = np.abs(np.linalg.eigvals(A)).max(axis=2)                 # (B,H)
    sig = np.linalg.svd(A, compute_uv=False)[..., 0]               # (B,H) sigma_max
    absc = np.linalg.eigvalsh((A + np.transpose(A, (0, 1, 3, 2))) / 2).max(axis=2)
    return rho, sig, absc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", "-d", default=None)
    ap.add_argument("--n-batch", type=int, default=30)
    args = ap.parse_args()

    ledger = json.load(io.open(os.path.join(RESULTS, "gate1_ledger.json"), encoding="utf-8"))
    cfg = g2.paired_cfg(ledger["best"]["M5"]["cfg"])
    H = proto.HORIZONS["long"]
    w, _ = g1.tensors("test", H, frozen_eval=True)
    idx = np.arange(min(args.n_batch, len(w["k"])))
    xh = g1.batchify(w, "Xh", idx)
    uin = g1.batchify(w, "Uin", idx)
    uf = g1.batchify(w, "UF", idx)

    dname = dev.current()["name"]
    out = {"device": dname, "horizon": H, "n_batch": int(len(idx)),
           "paired_cfg": cfg, "variants": {}}

    for variant, spec in (("A0B0", "M_base"), ("AcB0", "M4"), ("AcBx", "M5")):
        model, info = g1.load_or_train(spec, cfg, seed=0)
        A_all = rollout_collect_A(model, xh, uin, uf)
        mean_n, max_n = product_norms(A_all)
        rho, sig, absc = per_step_stats(A_all)

        rec = {
            "spec": spec, "load_info": info,
            "rho_A_mean": float(rho.mean()), "rho_A_max": float(rho.max()),
            "sigma_max_mean": float(sig.mean()), "sigma_max_max": float(sig.max()),
            "abscissa_mean": float(absc.mean()), "abscissa_max": float(absc.max()),
            "prod_norm_mean": {h: float(mean_n[h - 1]) for h in SAMPLE},
            "prod_norm_max": {h: float(max_n[h - 1]) for h in SAMPLE},
            "rho_pow_max": {h: float(rho.max() ** h) for h in SAMPLE},
            "nonnormality_max": float(sig.max() / max(rho.max(), 1e-12)),
        }
        # effective growth of the true linear gain over h in [25,100]
        hh = np.arange(25, 101)
        rec["prod_slope_25_100"] = float(np.polyfit(hh, np.log(np.maximum(mean_n[24:100], 1e-12)), 1)[0])
        rec["rho_slope_25_100"] = float(np.log(max(rec["rho_A_max"], 1e-12)))
        out["variants"][variant] = rec

        print("=" * 92)
        print("%s (%s)  device=%s" % (variant, spec, dname))
        print("=" * 92)
        print("  per-step A(c): rho max=%.5f mean=%.5f | sigma_max max=%.5f mean=%.5f "
              "| abscissa max=%.5f" % (rec["rho_A_max"], rec["rho_A_mean"],
                                       rec["sigma_max_max"], rec["sigma_max_mean"],
                                       rec["abscissa_max"]))
        print("  non-normality sigma_max/rho = %.3f" % rec["nonnormality_max"])
        print("  %-8s %14s %16s %16s" % ("h", "rho_max^h", "mean||prod||", "max||prod||"))
        for h in SAMPLE:
            print("  %-8d %14.4f %16.4f %16.4f"
                  % (h, rec["rho_pow_max"][h], rec["prod_norm_mean"][h], rec["prod_norm_max"][h]))
        print("  effective growth rate of mean||prod|| over h in [25,100]: %.5f "
              "(per-step %.4fx)" % (rec["prod_slope_25_100"], np.exp(rec["prod_slope_25_100"])))
        print("  spectral-radius growth rate ln rho_max             : %.5f (per-step %.4fx)"
              % (rec["rho_slope_25_100"], np.exp(rec["rho_slope_25_100"])))
        print()
        g1.free()

    path = os.path.join(RESULTS, "transient_growth_%s.json" % dname)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("written -> %s" % path)


if __name__ == "__main__":
    main()
