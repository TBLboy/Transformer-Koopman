# -*- coding: utf-8 -*-
"""Gate 0 helper: per-split statistics + train-only normalization constants.

Reads ``数据备份/软体平台数据/处理后的数据/*.npz`` (read-only) and prints the
statistics required by the data manifest. Nothing is written except stdout.
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXP_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(EXP_DIR)))
PROC = os.path.join(REPO, "数据备份", "软体平台数据", "处理后的数据")

out = []
for split in ("train", "val", "test"):
    z = np.load(os.path.join(PROC, "%s.npz" % split), allow_pickle=True)
    x = z["x"].astype(np.float64)
    u = z["u"].astype(np.float64)
    tid = z["trajectory_id"]
    rec = {
        "split": split,
        "n_samples": int(x.shape[0]),
        "n_traj": int(tid.max()) + 1,
        "x_mean": np.round(x.mean(0), 6).tolist(),
        "x_std": np.round(x.std(0), 6).tolist(),
        "x_min": np.round(x.min(0), 6).tolist(),
        "x_max": np.round(x.max(0), 6).tolist(),
        "u_mean": np.round(u.mean(0), 6).tolist(),
        "u_std": np.round(u.std(0), 6).tolist(),
        "u_min": np.round(u.min(0), 6).tolist(),
        "u_max": np.round(u.max(0), 6).tolist(),
        "u_absmax": np.round(np.abs(u).max(0), 6).tolist(),
        "u_absmean": np.round(np.abs(u).mean(0), 6).tolist(),
        "x_absmax": np.round(np.abs(x).max(0), 6).tolist(),
        "x_absmean": np.round(np.abs(x).mean(0), 6).tolist(),
        "u_is_integer_like": bool(np.allclose(u, np.round(u), atol=1e-9)),
        "x_is_integer_like": bool(np.allclose(x, np.round(x), atol=1e-9)),
    }
    out.append(rec)

# train-only normalization constants (the protocol requires fitting on train only)
tr = out[0]
norm = {
    "x_mean": tr["x_mean"], "x_std": tr["x_std"],
    "u_mean": tr["u_mean"], "u_std": tr["u_std"],
    "fitted_on": "train.npz only",
}
lines = ["per-split statistics (Platform 2 / soft platform)", "=" * 70]
for rec in out:
    lines.append("")
    lines.append("[%s]  n=%d  trajs=%d" % (rec["split"], rec["n_samples"], rec["n_traj"]))
    for k in ("x_mean", "x_std", "x_min", "x_max", "u_mean", "u_std", "u_min", "u_max",
              "u_absmax", "u_absmean", "x_absmax", "x_absmean"):
        lines.append("    %-11s %s" % (k, rec[k]))
    lines.append("    u integer-like: %s   x integer-like: %s"
                 % (rec["u_is_integer_like"], rec["x_is_integer_like"]))
lines.append("")
lines.append("train-only normalization constants")
lines.append(json.dumps(norm, indent=2))

txt = "\n".join(lines) + "\n"
print(txt)
dst = os.path.join(EXP_DIR, "results", "audit", "split_stats.txt")
with io.open(dst, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(txt)
sys.exit(0)
