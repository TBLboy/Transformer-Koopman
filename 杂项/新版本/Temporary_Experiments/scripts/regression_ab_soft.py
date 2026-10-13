# -*- coding: utf-8 -*-
"""Refactor regression check for the soft platform (DEC-087 D9) -- the A/B test.

The device-parameterisation touched models/protocol.py, models/library.py,
controllers/ltv_mpc.py and scripts/run_gate1.py.  To prove that the soft-platform
numbers did not move, the SAME saved checkpoints were evaluated twice:

  A) with the pre-refactor harness (restored from git HEAD into the working tree),
     -> results/modeling/eval_soft_oldcode.json
  B) with the refactored harness,
     -> results/modeling/eval_soft_newcode.json

Both runs use scripts/eval_ckpt_soft.py, which imports only run_gate1 and is
therefore runnable under either harness.  This script diffs A against B.

NOTE: a *checkpoint-vs-ledger* comparison is NOT a refactor regression test --
the ledger's test entries were produced by a fresh in-process retrain, and the
neural models are not training-reproducible on this box (AMP + TF32 + cuDNN
benchmark).  Only the same-checkpoint A/B isolates the refactor.

Run:  python scripts/regression_ab_soft.py
"""
from __future__ import annotations

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)

NEW = os.path.join(EXP, "results", "modeling", "eval_soft_newcode.json")
OLD = os.path.join(EXP, "results", "modeling", "eval_soft_oldcode.json")
OUT = os.path.join(EXP, "results", "modeling", "regression_ab_soft.json")

SPECS = ["M0", "M1", "M2", "M3", "M4", "M5", "M6"]


def flat(d, p=""):
    o = {}
    if isinstance(d, dict):
        for k, v in d.items():
            o.update(flat(v, p + "/" + str(k)))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            o.update(flat(v, p + "/%d" % i))
    else:
        o[p] = d
    return o


def main():
    if not (os.path.exists(NEW) and os.path.exists(OLD)):
        print("missing one of:\n  %s\n  %s" % (NEW, OLD))
        return 2
    new = json.load(io.open(NEW, encoding="utf-8"))
    old = json.load(io.open(OLD, encoding="utf-8"))
    report = {"device": "soft_platform",
              "what": ("same checkpoints evaluated by the pre-refactor and the "
                       "refactored harness; isolates the device-parameterisation"),
              "artifacts": {"new_code": os.path.relpath(NEW, EXP),
                            "old_code": os.path.relpath(OLD, EXP)},
              "models": {}, "total_metrics": 0, "total_differing": 0,
              "max_abs_diff": 0.0}
    for spec in SPECS:
        a, b = flat(new[spec]["eval"]), flat(old[spec]["eval"])
        keys = sorted(set(a) | set(b))
        worst, wk, nm = 0.0, None, 0
        for k in keys:
            if k not in a or k not in b:
                nm += 1
                continue
            if isinstance(a[k], (int, float)) and isinstance(b[k], (int, float)):
                d = abs(float(a[k]) - float(b[k]))
                if d > worst:
                    worst, wk = d, k
                if d > 0.0:
                    nm += 1
        report["models"][spec] = {"metrics": len(keys), "differing": nm,
                                  "max_abs_diff": worst, "worst_key": wk,
                                  "params_new": new[spec]["params"],
                                  "params_old": old[spec]["params"]}
        report["total_metrics"] += len(keys)
        report["total_differing"] += nm
        report["max_abs_diff"] = max(report["max_abs_diff"], worst)
        print("  %-3s metrics=%-4d differing=%-3d max|d|=%.3e  %s"
              % (spec, len(keys), nm, worst, wk))
    report["verdict"] = "IDENTICAL" if report["total_differing"] == 0 else "CHANGED"
    print("\nVERDICT: %s  (%d/%d metrics differ, max|d|=%.3e)"
          % (report["verdict"], report["total_differing"], report["total_metrics"],
             report["max_abs_diff"]))
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print("written -> %s" % OUT)
    return 0 if report["total_differing"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
