import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman\data\experiment_001")
NEW = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\数据备份\机械臂数据\处理后的数据")

print("=== P1: adapter output vs OLD experiment_001 (exact array equality) ===")
all_ok = True
for split in ("train", "val", "test"):
    o = np.load(OLD / f"{split}.npz")
    n = np.load(NEW / f"{split}.npz")
    row = []
    for key in ("x", "u", "t", "trajectory_id"):
        same = np.array_equal(o[key], n[key])
        all_ok &= same
        row.append(f"{key}={'OK' if same else 'DIFF'}")
    print(f"  {split}: old{o['x'].shape} vs new{n['x'].shape}  " + "  ".join(row))
    if not np.array_equal(o["x"], n["x"]):
        d = np.abs(o["x"] - n["x"])
        print(f"     x max abs diff = {d.max()!r}, differing elements = {(d > 0).sum()}")

print(f"\n  ALL FOUR ARRAYS IDENTICAL IN ALL SPLITS: {all_ok}")

print("\n=== P2: adapter output summary (no old reference available) ===")
P2 = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\数据备份\软体平台数据\处理后的数据")
for split in ("train", "val", "test"):
    d = np.load(P2 / f"{split}.npz")
    tid = d["trajectory_id"]
    print(f"  {split}: x={d['x'].shape} u={d['u'].shape} t={d['t'].shape} "
          f"trajectories={len(np.unique(tid))} tid range=({tid.min()},{tid.max()}) "
          f"per-traj rows={set(np.bincount(tid).tolist())}")

print("\n=== contract shape check (both platforms) ===")
for name, base in (("p1", NEW), ("p2", P2)):
    for split in ("train", "val", "test"):
        d = np.load(base / f"{split}.npz")
        keys = set(d.files)
        need = {"x", "u", "t", "trajectory_id"}
        assert keys == need, f"{name}/{split} keys={keys}"
        assert d["x"].shape[0] == d["u"].shape[0] == d["t"].shape[0] == d["trajectory_id"].shape[0]
    print(f"  {name}: x/u/t/trajectory_id present, consistent lengths, dtypes x={d['x'].dtype} tid={d['trajectory_id'].dtype}")
