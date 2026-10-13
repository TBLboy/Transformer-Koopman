# -*- coding: utf-8 -*-
"""Sequential, resumable driver for the whole ARM experiment (GOAL-004 / TASK-046).

Runs every step as its OWN process (host RAM is 16 GB; merging models in one
process OOMs) and logs each step separately.  Re-running skips steps that are
already complete according to the on-disk ledger, so an interrupted run resumes
instead of duplicating trials.

Steps
  gate1 formal : 7 models x 6 random-search trials (validation selection)
  gate1 final  : 7 models x 3 seeds, retrained, validation evaluation, checkpoints saved
  gate1 test   : 7 models x 3 seeds, frozen test evaluation
  gate2        : E-M3 paired ablation / E-M4 capacity matching / E-M5 diagnostics
  gate4 val    : control sensitivity search on validation scenarios
  gate4 test   : control evaluation on test scenarios
  gate5        : freezing-error cross-check
  reports      : reports/arm_*.md + figures

Run:  python scripts/run_arm_all.py
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
LOGS = os.path.join(EXP, "results", "arm", "logs")
LEDGER = os.path.join(EXP, "results", "arm", "modeling", "gate1_ledger.json")
os.makedirs(LOGS, exist_ok=True)

PY = sys.executable
SPECS = ["M0", "M1", "M2", "M3", "M4", "M5", "M6"]
TRIALS = 6
SEEDS = 3
EPOCHS = 50


def ledger():
    if os.path.exists(LEDGER):
        return json.load(io.open(LEDGER, encoding="utf-8"))
    return {}


def have(spec, stage):
    led = ledger()
    if stage == "formal":
        return len(led.get("trials", {}).get(spec, [])) >= TRIALS
    if stage == "final":
        return len(led.get("final", {}).get(spec, [])) >= SEEDS
    if stage == "test":
        return len(led.get("test", {}).get(spec, [])) >= SEEDS
    return False


def run(name, argv):
    """Run one step; returns True on rc == 0."""
    log = os.path.join(LOGS, name + ".log")
    t0 = time.time()
    print("\n" + "=" * 78)
    print("[%s] %s" % (time.strftime("%H:%M:%S"), name))
    print("  cmd: %s" % " ".join(argv))
    with io.open(log, "w", encoding="utf-8", newline="\n") as fh:
        p = subprocess.run(argv, stdout=fh, stderr=subprocess.STDOUT, cwd=EXP)
    dt = time.time() - t0
    tail = ""
    try:
        lines = io.open(log, encoding="utf-8", errors="replace").read().splitlines()
        tail = "\n".join("    | " + l for l in lines[-6:])
        # the Windows console code page is GBK; keep the driver's own output ASCII-safe
        tail = tail.encode("ascii", "replace").decode("ascii")
    except Exception:                                             # noqa: BLE001
        tail = ""
    print("  rc=%d  %.1fs  log=%s" % (p.returncode, dt, log))
    if tail:
        print(tail)
    return p.returncode == 0


def main():
    steps = []
    for spec in SPECS:
        for stage in ("formal", "final", "test"):
            steps.append(("%s_%s" % (spec, stage), stage, spec))

    failures = []
    for name, stage, spec in steps:
        if have(spec, stage):
            print("[skip] %s already complete" % name)
            continue
        argv = [PY, "-u", os.path.join(HERE, "run_gate1.py"), "--device", "arm_3link",
                "--stage", stage, "--models", spec, "--epochs", str(EPOCHS)]
        if stage == "formal":
            argv += ["--trials", str(TRIALS)]
        else:
            argv += ["--seeds", str(SEEDS)]
        if stage == "test":
            argv += ["--test-from-checkpoint"]
        if not run(name, argv):
            failures.append(name)

    for name, argv in (
        ("gate2", [PY, "-u", os.path.join(HERE, "run_gate2.py"), "--device", "arm_3link",
                   "--seeds", str(SEEDS)]),
        ("gate4_val", [PY, "-u", os.path.join(HERE, "run_gate4.py"), "--device", "arm_3link",
                       "--split", "val", "--search",
                       "--search-scenarios", "setpoint_0,slow_sinusoid"]),
        ("gate4_test", [PY, "-u", os.path.join(HERE, "run_gate4.py"), "--device", "arm_3link",
                        "--split", "test"]),
        ("gate5", [PY, "-u", os.path.join(HERE, "run_gate5.py"), "--device", "arm_3link"]),
        ("reports", [PY, "-u", os.path.join(HERE, "report_arm.py"), "--device", "arm_3link"]),
    ):
        if not run(name, argv):
            failures.append(name)

    print("\n" + "=" * 78)
    print("ARM PIPELINE DONE.  failures: %s" % (failures if failures else "none"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
