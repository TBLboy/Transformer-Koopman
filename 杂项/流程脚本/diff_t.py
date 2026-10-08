import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman\data\experiment_001")
NEW = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\数据备份\机械臂数据\处理后的数据")

for split in ("train", "val", "test"):
    o = np.load(OLD / f"{split}.npz")["t"]
    n = np.load(NEW / f"{split}.npz")["t"]
    print(f"--- {split} ---")
    print(f"  old t: dtype={o.dtype} shape={o.shape} first8={np.array2string(o[:8], precision=6)}")
    print(f"  new t: dtype={n.dtype} shape={n.shape} first8={np.array2string(n[:8], precision=6)}")
    print(f"  old range=({o.min():.6g},{o.max():.6g})  new range=({n.min():.6g},{n.max():.6g})")
    print(f"  old diffs first6={np.array2string(np.diff(o[:6]), precision=6)}")
    print(f"  new diffs first6={np.array2string(np.diff(n[:6]), precision=6)}")
    for label, cand in (
        ("equal", o),
        ("n[:len(o)]", n[:len(o)]),
        ("old==new[:len(o)]", None),
    ):
        if cand is None:
            continue
        print(f"  {label}: equal={np.array_equal(o, cand)}")
    # is old t == new t rebased per trajectory?  old t starts near 0?
    print(f"  old t[0]={o[0]!r}  new t[0]={n[0]!r}  old t[-1]={o[-1]!r} new t[-1]={n[-1]!r}")
    # constant step?
    print(f"  old step unique (first traj region)={np.unique(np.round(np.diff(o[:50]), 9))[:5]}")
    print()

print("=== is old t == new t shifted by a constant? ===")
o = np.load(OLD / "train.npz")["t"]
n = np.load(NEW / "train.npz")["t"]
d = o - n
print(f"  (old - new) unique (first 20): {np.unique(np.round(d[:20], 9))}")
print(f"  (old - new) overall unique count: {len(np.unique(np.round(d, 9)))}")
print(f"  (old - new) min/max: {d.min():.6g} / {d.max():.6g}")

print("\n=== is old t a per-trajectory elapsed time (t - t_of_traj_start)? ===")
tid = np.load(OLD / "train.npz")["trajectory_id"]
starts = np.searchsorted(tid, np.arange(tid.max() + 2))
for k in range(3):
    a, b = starts[k], starts[k + 1]
    print(f"  traj {k}: old t[0]={o[a]:.6g} old t[-1]={o[b-1]:.6g} "
          f"new t[0]={n[a]:.6g} new t[-1]={n[b - 1]:.6g} span_old={o[b-1]-o[a]:.6g}")

print("\n=== does the training code actually use t? ===")
CODE = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\src")
import re
for p in sorted(CODE.rglob("*.py")):
    txt = p.read_text(encoding="utf-8")
    for i, line in enumerate(txt.split("\n"), 1):
        if re.search(r'\["t"\]|\bt\b\s*=.*\["t"\]|data\[.t.\]|\.t\b', line) and "torch" not in line:
            s = line.strip()
            if s and ("t" in s) and ("tensor" not in s) and len(s) < 140:
                pass
    hits = [f"{i}:{l.strip()}" for i, l in enumerate(txt.split("\n"), 1)
            if '["t"]' in l or "data['t']" in l or '["t"]' in l]
    if hits:
        print(f"  {p.relative_to(CODE)}: {hits}")
