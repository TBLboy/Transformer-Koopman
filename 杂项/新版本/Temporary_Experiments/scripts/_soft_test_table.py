# -*- coding: utf-8 -*-
"""Soft-platform Gate-1 test table (mean over 3 seeds) for a direct comparison."""
import io
import json
import os

import numpy as np

P = (r"D:\Project\Transformer-Koopman\Transformer-Koopman\杂项\新版本"
     r"\Temporary_Experiments\results\modeling\gate1_ledger.json")
led = json.load(io.open(P, encoding="utf-8"))
test = led["test"]
NAMES = {"M0": "DMDc (linear)", "M1": "EDMDc (fixed dict)", "M2": "EDMD-DL (learnable dict)",
         "M3": "GRU controlled", "M4": "A(c)+B0 (old)", "M5": "A(c)+B(x) (new)",
         "M6": "Controlled Transformer"}

print("%-6s %-24s %10s %10s %10s %10s" % ("spec", "model", "one-step", "roll5", "roll25", "roll100"))
rows = []
for s in ("M0", "M1", "M2", "M3", "M4", "M5", "M6"):
    runs = test.get(s)
    if not runs:
        print("%-6s %-24s  (missing)" % (s, NAMES[s]))
        continue
    one = np.mean([r["test"]["one_step"]["short"] for r in runs])
    r5 = np.mean([r["test"]["rollout"]["short"] for r in runs])
    r25 = np.mean([r["test"]["rollout"]["mid"] for r in runs])
    r100 = np.mean([r["test"]["rollout"]["long"] for r in runs])
    sd = np.std([r["test"]["rollout"]["mid"] for r in runs])
    rows.append((s, one, r5, r25, r100, sd))
    print("%-6s %-24s %10.4f %10.4f %10.4f %10.4f   (roll25 sd=%.4f)"
          % (s, NAMES[s], one, r5, r25, r100, sd))

print()
best = min(rows, key=lambda r: r[3])          # r[3] is roll25
print("best roll25: %s %s = %.4f" % (best[0], NAMES[best[0]], best[3]))
for s, one, r5, r25, r100, sd in sorted(rows, key=lambda r: r[3]):
    print("  %-3s roll25 ratio to best = %.2fx   roll5=%.4f  roll100=%.4f" % (s, r25 / best[3], r5, r100))
b5 = min(rows, key=lambda r: r[2])
print("\nbest roll5: %s = %.4f ; best one-step: %s = %.4f ; best roll100: %s = %.4f"
      % (b5[0], b5[2], min(rows, key=lambda r: r[1])[0], min(rows, key=lambda r: r[1])[1],
         min(rows, key=lambda r: r[4])[0], min(rows, key=lambda r: r[4])[4]))
