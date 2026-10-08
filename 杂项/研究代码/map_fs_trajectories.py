# -*- coding: utf-8 -*-
"""Map our processed P2 test trajectories to the raw files / old-project split."""
import os, sys
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"D:\Project\Transformer-Koopman\Transformer-Koopman"
PROC = os.path.join(ROOT, "数据备份", "软体平台数据", "处理后的数据")
RAW = os.path.join(ROOT, "数据备份", "软体平台数据", "原始数据")
OLDDATA = r"D:\Project\my_lunwen\数据备份\软体平台"

# raw trajectories
raw = {}
for f in sorted(os.listdir(RAW)):
    if f.endswith(".npz"):
        d = np.load(os.path.join(RAW, f))
        raw[f] = (d["x"], d["u"])

ours = np.load(os.path.join(PROC, "test.npz"))
ours_tr = np.load(os.path.join(PROC, "train.npz"))

print("=== our processed data: raw or normalized? ===")
print("  our train x mean:", ours_tr["x"].mean(0), " std:", ours_tr["x"].std(0))
print("  our train u mean:", ours_tr["u"].mean(0), " std:", ours_tr["u"].std(0))
allx = np.vstack([raw[f][0] for f in raw])
print("  raw(all) x mean:", allx.mean(0), " std:", allx.std(0))

print("\n=== match our test trajectories to raw files ===")
tid = ours["trajectory_id"]
for t in np.unique(tid):
    idx = np.where(tid == t)[0]
    xx = ours["x"][idx]; uu = ours["u"][idx]
    best = None
    for f, (rx, ru) in raw.items():
        if rx.shape[0] != xx.shape[0]:
            continue
        # compare up to affine scaling (our data may be normalized)
        # correlation-based match
        c = 0.0
        for a in range(2):
            ca = np.corrcoef(xx[:, a], rx[:, a])[0, 1]
            c += ca
        c /= 2
        if best is None or c > best[1]:
            best = (f, c)
    print(f"  our test traj {t} (n={len(idx)}) -> raw {best[0]}  corr={best[1]:.5f}")

# old project processed test
print("\n=== old project processed data ===")
ot = np.load(os.path.join(OLDDATA, "处理后的数据", "test.npz"), allow_pickle=True)
print("  old test keys:", list(ot.keys()))
for k in ot.keys():
    print("   ", k, getattr(ot[k], "shape", None), getattr(ot[k], "dtype", None))
meta = np.load(os.path.join(OLDDATA, "处理后的数据", "meta.npz"), allow_pickle=True)
print("  old meta x_mean:", meta["x_mean"], " x_scale:", meta["x_scale"])
print("  old test ids:", meta["test_trajectory_ids"])
