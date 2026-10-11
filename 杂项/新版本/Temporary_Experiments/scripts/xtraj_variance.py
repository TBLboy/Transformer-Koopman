# -*- coding: utf-8 -*-
"""Supplementary auxiliary metric required by plan section 2.3: cross-trajectory
variance of the H=25 rollout error.

Why a separate script: the Gate-1 ledger stores horizon curves and quantiles but
not the per-trajectory breakdown, and re-deriving it needs the trained models.
To keep the cost bounded this runs **one seed per model (seed 0)** and says so
explicitly -- it is a distributional diagnostic, NOT a replacement for the
multi-seed main table.

Statistical unit = one independent test trajectory (10 of them), which is the
plan's requirement (avoid pseudo-replication from overlapping windows).

Run:  python scripts/xtraj_variance.py
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "models"))
sys.path.insert(0, HERE)

import protocol as proto                     # noqa: E402
import run_gate1 as g1                       # noqa: E402

RES = os.path.join(EXP, "results", "modeling")
SPECS = ["M0", "M1", "M2", "M3", "M4", "M5", "M6"]


def main():
    led = json.load(open(os.path.join(RES, "gate1_ledger.json"), encoding="utf-8"))
    out = {"metric": "per-trajectory RMSE at H=25 (normalised), test split",
           "seeds": [0], "note": ("single-seed supplementary diagnostic; the main "
                                  "table uses 3 seeds"),
           "statistical_unit": "one independent test trajectory",
           "models": {}}

    w, _ = g1.tensors("test", 25, frozen_eval=True)
    traj = w["traj"]

    for spec in SPECS:
        best = led.get("best", {}).get(spec)
        if not best:
            print("  %s: no selected config" % spec)
            continue
        model, _ = g1.make_train_rollout(spec, best["cfg"], seed=0)
        idx = np.arange(len(w["k"]))
        xh, uin, uf = (g1.batchify(w, k, idx) for k in ("Xh", "Uin", "UF"))
        tgt = g1.batchify(w, "XF", idx)
        with torch.no_grad():
            pred = model.rollout(xh, uin, uf).cpu().numpy()
        tgt_np = tgt.cpu().numpy()
        per = {}
        for t in np.unique(traj):
            m = traj == t
            per[int(t)] = float(np.sqrt(np.mean((pred[m] - tgt_np[m]) ** 2)))
        vals = np.array(list(per.values()))
        entry = {"per_trajectory_rmse": per,
                 "mean": float(vals.mean()), "std": float(vals.std(ddof=0)),
                 "var": float(vals.var()), "min": float(vals.min()),
                 "max": float(vals.max()),
                 "worst_traj": int(vals.argmax()), "best_traj": int(vals.argmin()),
                 "params": g1.n_params(model)}
        out["models"][spec] = entry
        print("  %-3s per-traj RMSE mean=%.4f var=%.5f min=%.4f max=%.4f (worst traj %d)"
              % (spec, entry["mean"], entry["var"], entry["min"], entry["max"],
                 entry["worst_traj"]))
        g1.free()

    with io.open(os.path.join(RES, "xtraj_variance.json"), "w", encoding="utf-8",
                 newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("written -> results/modeling/xtraj_variance.json")


if __name__ == "__main__":
    main()
