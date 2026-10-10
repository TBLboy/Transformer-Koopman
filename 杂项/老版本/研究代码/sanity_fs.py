# -*- coding: utf-8 -*-
"""Sanity-check FS-KOOPMAN on the OLD project's own test split (reproduce its numbers)."""
import os, sys
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MC = r"D:\Project\my_lunwen\建模代码"
sys.path.insert(0, MC)
from modeling.trainers.fs_edmd import OursKoopmanTrainer  # noqa: E402

OLD = r"D:\Project\my_lunwen\结果备份\软体平台训练结果"
OD = r"D:\Project\my_lunwen\数据备份\软体平台\处理后的数据"
meta = np.load(os.path.join(OD, "meta.npz"), allow_pickle=True)
oxm, oxs, oum, ous = meta["x_mean"], meta["x_scale"], meta["u_mean"], meta["u_scale"]

fs = OursKoopmanTrainer(verbose=False).load(os.path.join(OLD, "fs_edmd.pkl"))

d = np.load(os.path.join(OD, "test.npz"), allow_pickle=True)
X, U, Y, tid, sid = d["X"], d["U"], d["Y"], d["trajectory_id"], d["step_index"]
print("old test: X", X.shape, "traj ids", np.unique(tid))

# one-step (model predicts Y from X,U)
e1 = []
for i in range(len(X)):
    p = fs.predict(X[i], [U[i]], steps=1)[0]
    e1.append(np.linalg.norm(p - Y[i]))
print("one-step RMSE (old test, normalized):", float(np.sqrt(np.mean(np.square(e1)))))

# multi-step rollout on a few windows of trajectory 93
H = 20
errs = {h: [] for h in range(1, H + 1)}
for t in np.unique(tid):
    idx = np.where(tid == t)[0]
    Xt, Ut, Yt = X[idx], U[idx], Y[idx]
    # ground truth physical for this trajectory
    for k in range(0, len(Xt) - H - 1, 20):
        x0 = Xt[k]
        us = [Ut[k + h] for h in range(H)]
        pred = fs.predict(x0, us, steps=H)
        gt = Yt[k:k + H]
        for h in range(1, H + 1):
            errs[h].append(np.linalg.norm(pred[h - 1] - gt[h - 1]))
print("multi-step RMSE (old test, normalized):")
for h in [1, 5, 10, 20]:
    print(f"   H={h}: {float(np.sqrt(np.mean(np.square(errs[h])))):.5f}")

# trajectory 93 specifically
if 93 in np.unique(tid):
    idx = np.where(tid == 93)[0]
    print(f"\ntraj 93: n={len(idx)}  X range x1=[{X[idx,0].min():.2f},{X[idx,0].max():.2f}]")
    e = []
    for k in range(0, len(idx) - H - 1, 20):
        p = fs.predict(X[idx][k], [U[idx][k + h] for h in range(H)], steps=H)
        gt = Y[idx][k:k + H]
        for h in range(1, H + 1):
            e.append(np.linalg.norm(p[h - 1] - gt[h - 1]))
    print("   traj93 multi-step RMSE:", float(np.sqrt(np.mean(np.square(e)))))
