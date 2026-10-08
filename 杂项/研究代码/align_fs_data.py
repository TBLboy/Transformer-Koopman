# -*- coding: utf-8 -*-
"""Align the FS-KOOPMAN (previous method) data split with our processed P2 data."""
import os, sys, json
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"D:\Project\Transformer-Koopman\Transformer-Koopman"
PROC = os.path.join(ROOT, "数据备份", "软体平台数据", "处理后的数据")
RAW = os.path.join(ROOT, "数据备份", "软体平台数据", "原始数据")
OLD = r"D:\Project\my_lunwen\结果备份\软体平台训练结果"
OLDDATA = r"D:\Project\my_lunwen\数据备份"

print("=== meta.npz (full) ===")
m = np.load(os.path.join(OLD, "meta.npz"), allow_pickle=True)
for k in m.files:
    v = m[k]
    print(f"  {k}: {repr(v)[:300]}")

print("\n=== our processed data ===")
for s in ["train", "val", "test"]:
    d = np.load(os.path.join(PROC, f"{s}.npz"))
    tid = d["trajectory_id"]; u, c = np.unique(tid, return_counts=True)
    print(f"  {s}: n_samples={len(tid)}  x={d['x'].shape}  u={d['u'].shape}  n_traj={len(u)}  ids={list(u)}  lens={list(c)}")

print("\n=== raw data ===")
files = sorted(os.listdir(RAW))
print("  n_files:", len(files), "first:", files[:6], "last:", files[-3:])
d0 = np.load(os.path.join(RAW, files[0]))
print("  sample file", files[0], "keys:", list(d0.keys()))
for k in d0.keys():
    print("    ", k, getattr(d0[k], "shape", None), d0[k].dtype)

print("\n=== old project data dir ===")
if os.path.exists(OLDDATA):
    for root, dirs, fs in os.walk(OLDDATA):
        for f in fs:
            if f.endswith((".npz", ".pkl", ".npy")):
                print("   ", os.path.join(root, f).replace(OLDDATA, ""))

print("\n=== old project 建模代码 data scripts ===")
MC = r"D:\Project\my_lunwen\建模代码"
for root, dirs, fs in os.walk(MC):
    for f in fs:
        if f.endswith(".py") and ("data" in f.lower() or "split" in f.lower() or "soft" in f.lower()):
            print("   ", os.path.join(root, f).replace(MC, ""))
