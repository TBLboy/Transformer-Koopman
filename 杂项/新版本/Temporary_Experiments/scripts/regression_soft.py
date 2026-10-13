# -*- coding: utf-8 -*-
"""Regression check (DEC-087 D9): after making the harness device-aware, the
soft-platform Gate-1 numbers must be UNCHANGED.

Re-loads each model exactly as run_gate1 does (checkpoint when present, closed-form
retrain otherwise), re-evaluates on the frozen test starts and diffs every stored
metric against results/modeling/gate1_ledger.json.

Run:  python scripts/regression_soft.py
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "models"))
sys.path.insert(0, HERE)

import device as dev                          # noqa: E402
dev.bootstrap_from_argv()

import run_gate1 as g1                        # noqa: E402

LEDGER = os.path.join(dev.results_dir("modeling"), "gate1_ledger.json")
OUT = os.path.join(dev.results_dir("modeling"), "regression_soft.json")

SPECS = ["M0", "M1", "M2", "M3", "M4", "M5", "M6"]


def flatten(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flatten(v, prefix + ("/" if prefix else "") + str(k)))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(flatten(v, prefix + "/%d" % i))
    else:
        out[prefix] = d
    return out


def main():
    assert dev.current()["name"] == "soft_platform", "run this without --device"
    led = json.load(io.open(LEDGER, encoding="utf-8"))
    report = {"device": dev.current()["name"], "ledger": os.path.relpath(LEDGER, EXP),
              "models": {}, "max_abs_diff": 0.0, "n_metrics": 0, "n_mismatch": 0}
    for spec in SPECS:
        best = led["best"][spec]
        model, info = g1.load_or_train(spec, best["cfg"], seed=0)
        ev = g1.eval_all(model, "test")
        old = led["test"][spec][0]["test"]
        a, b = flatten(ev), flatten(old)
        keys = sorted(set(a) | set(b))
        worst, wk, nmis = 0.0, None, 0
        for k in keys:
            if k not in a or k not in b:
                nmis += 1
                continue
            va, vb = a[k], b[k]
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                d = abs(float(va) - float(vb))
                if d > worst:
                    worst, wk = d, k
                if d > 1e-12:
                    nmis += 1
        report["models"][spec] = {"params": g1.n_params(model), "load": info,
                                  "max_abs_diff": worst, "worst_key": wk,
                                  "n_mismatch": nmis, "n_metrics": len(keys)}
        report["max_abs_diff"] = max(report["max_abs_diff"], worst)
        report["n_metrics"] += len(keys)
        report["n_mismatch"] += nmis
        print("  %-3s metrics=%-4d mismatch=%-3d max|d|=%.3e (%s)"
              % (spec, len(keys), nmis, worst, wk))
        g1.free()

    report["verdict"] = "IDENTICAL" if report["n_mismatch"] == 0 else "CHANGED"
    print("\nVERDICT: %s   (max|d|=%.3e over %d metrics)"
          % (report["verdict"], report["max_abs_diff"], report["n_metrics"]))
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print("written -> %s" % OUT)
    return 0 if report["n_mismatch"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
