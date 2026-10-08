# -*- coding: utf-8 -*-
"""Inspect the FS-KOOPMAN (previous method) artifacts on the soft platform."""
import os, sys, pickle
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

B = r"D:\Project\my_lunwen\结果备份\软体平台训练结果"

print("=== meta.npz ===")
m = np.load(os.path.join(B, "meta.npz"), allow_pickle=True)
for k in m.files:
    v = m[k]
    try:
        sh = v.shape
    except Exception:
        sh = None
    s = repr(v)
    print(f"  {k}: shape={sh} dtype={getattr(v,'dtype',None)}  value={s[:200]}")


def describe(obj, indent=2):
    pad = " " * indent
    print(f"{pad}type={type(obj)}")
    if isinstance(obj, dict):
        for k, v in obj.items():
            try:
                sh = getattr(v, "shape", None)
            except Exception:
                sh = None
            print(f"{pad}  [{k}] {type(v).__name__} shape={sh} value={repr(v)[:160]}")
    else:
        for a in dir(obj):
            if a.startswith("_"):
                continue
            try:
                v = getattr(obj, a)
            except Exception:
                continue
            if callable(v):
                continue
            sh = getattr(v, "shape", None)
            if sh is not None or isinstance(v, (int, float, str, bool, list, tuple, np.ndarray)):
                print(f"{pad}  .{a} = {type(v).__name__} {repr(v)[:160]}")


for fn in ["fs_edmd.pkl", "edmd.pkl", "edmd_dl.pkl"]:
    p = os.path.join(B, fn)
    print(f"\n=== {fn} ({os.path.getsize(p)} bytes) ===")
    try:
        with open(p, "rb") as f:
            obj = pickle.load(f)
        describe(obj)
    except Exception as ex:
        print("  LOAD FAILED:", type(ex).__name__, ex)
