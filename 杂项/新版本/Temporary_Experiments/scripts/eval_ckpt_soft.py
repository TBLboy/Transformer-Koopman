# -*- coding: utf-8 -*-
"""Evaluate the saved checkpoints and dump every metric (device-agnostic).

Works with BOTH the pre-refactor and post-refactor harness, so the same
checkpoints can be evaluated by both and the numbers diffed.  It therefore does
NOT import device.py or protocol.py directly -- only run_gate1, whose
load_or_train/eval_all API is unchanged.

Usage:  python scripts/eval_ckpt_soft.py <out.json> [seeds]
"""
from __future__ import annotations

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "models"))
sys.path.insert(0, HERE)

import run_gate1 as g1                        # noqa: E402

SPECS = ["M0", "M1", "M2", "M3", "M4", "M5", "M6"]


def main():
    out_path = sys.argv[1]
    ledger = json.load(io.open(os.path.join(EXP, "results", "modeling", "gate1_ledger.json"),
                               encoding="utf-8"))
    res = {}
    for spec in SPECS:
        model, info = g1.load_or_train(spec, ledger["best"][spec]["cfg"], seed=0)
        ev = g1.eval_all(model, "test")
        res[spec] = {"eval": ev, "params": g1.n_params(model), "load": info}
        print("  %-3s params=%d" % (spec, g1.n_params(model)))
        g1.free()
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print("written -> %s" % out_path)


if __name__ == "__main__":
    main()
