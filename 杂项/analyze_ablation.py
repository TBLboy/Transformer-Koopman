# -*- coding: utf-8 -*-
"""Analyze the Stage-0/Stage-1 ablation results."""
import json
from pathlib import Path

import numpy as np

P = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\杂项\ablation_stage01_result.json")
d = json.loads(P.read_text(encoding="utf-8"))
runs = d["runs"]
print("config:", json.dumps(d["config"], ensure_ascii=False))
print("runs:", len(runs))
STRATS = ["A", "B", "C", "D"]
HS = [1, 5, 10, 20]


def get(r, metric, h):
    return r["metrics"][metric][str(h)]


print("\n================ R_prop (scheduled propagation = deployment mode) ================")
print("%-4s %-8s %-8s %-8s %-8s | %-9s %-9s %-9s" % ("", "H1", "H5", "H10", "H20", "F_prop@20", "reenc@20", "valRollMSE"))
tab = {}
for s in STRATS:
    rs = [r for r in runs if r["strategy"] == s]
    row = {}
    for h in HS:
        v = [get(r, "R_prop", h) for r in rs]
        row[h] = (float(np.mean(v)), float(np.std(v)))
    fp = [get(r, "F_prop", 20) for r in rs]
    rc = [get(r, "R_reencode", 20) for r in rs]
    vr = [r["metrics"]["val_rollout_mse"] for r in rs]
    tab[s] = row
    print("%-4s %-8s %-8s %-8s %-8s | %-9s %-9s %-9s" % (
        s,
        "%.4f±%.4f" % row[1], "%.4f±%.4f" % row[5], "%.4f±%.4f" % row[10], "%.4f±%.4f" % row[20],
        "%.4f" % np.mean(fp), "%.4f" % np.mean(rc), "%.6f" % np.mean(vr)))

print("\n================ pairwise at H=20 (mean over seeds) ================")
for a, b in [("B", "C"), ("C", "D"), ("B", "D"), ("A", "B")]:
    ma, mb = tab[a][20][0], tab[b][20][0]
    print("%s vs %s : %.4f vs %.4f  -> %s better by %.1f%%" % (
        a, b, ma, mb, a if ma < mb else b, 100.0 * abs(ma - mb) / max(ma, mb)))

print("\n================ training stability and convergence (Stage 1) ================")
print("%-4s %-6s %-11s %-11s %-13s %-12s" % ("", "seed", "best_val", "ep_of_best", "last_val", "tail_std"))
for s in STRATS:
    for r in [r for r in runs if r["strategy"] == s]:
        c = r["stage1_curve"]
        vals = [x["val"] for x in c]
        tail = vals[-max(1, len(vals) // 4):]
        print("%-4s %-6d %-11.6f %-11d %-13.6f %-12.6f" % (
            s, r["seed"], min(vals), int(np.argmin(vals)) + 1, vals[-1], float(np.std(tail))))

print("\n================ convergence: mean val loss at checkpoints ================")
for s in STRATS:
    rs = [r for r in runs if r["strategy"] == s]
    for ep in (1, 5, 10, 25, 50, 100):
        v = [r["stage1_curve"][ep - 1]["val"] for r in rs]
        print("%-4s ep%-4d val=%.6f" % (s, ep, float(np.mean(v))))
    print()

print("================ trainable parameter counts ================")
for s in STRATS:
    rs = [r for r in runs if r["strategy"] == s]
    print("%s: stage1_trainable=%d frozen=%s stage0_trainable=%s" % (
        s, rs[0]["stage1_trainable"], rs[0]["stage1_frozen"], rs[0].get("stage0_trainable")))

print("\n================ wall clock (s, mean over seeds) ================")
for s in STRATS:
    rs = [r for r in runs if r["strategy"] == s]
    print("%s: stage0=%.1f stage1=%.1f total=%.1f" % (
        s, np.mean([r["stage0_seconds"] for r in rs]),
        np.mean([r["stage1_seconds"] for r in rs]), np.mean([r["total_seconds"] for r in rs])))
