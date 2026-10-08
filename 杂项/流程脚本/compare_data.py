import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman")
NEW = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")


def npz_info(p):
    try:
        with np.load(p, allow_pickle=True) as d:
            return {k: (d[k].shape, str(d[k].dtype)) for k in d.files}
    except Exception as e:
        return f"ERROR {type(e).__name__}: {e}"


def mat_info(p):
    try:
        from scipy.io import loadmat
        d = loadmat(p)
        return {k: (v.shape, str(v.dtype)) for k, v in d.items()
                if not k.startswith("__") and hasattr(v, "shape")}
    except Exception as e:
        return f"ERROR {type(e).__name__}: {e}"


print("=== OLD repo data/ ===")
d = OLD / "data"
if d.exists():
    for p in sorted(d.rglob("*")):
        if p.is_dir():
            print(f"  D {p.relative_to(OLD)}")
        else:
            print(f"    {p.stat().st_size:>10} B  {p.relative_to(OLD)}")
else:
    print("  MISSING")

print("\n=== OLD data/experiment_001 npz keys (P1, robot/机械臂) ===")
e1 = OLD / "data" / "experiment_001"
if e1.exists():
    for p in sorted(e1.glob("*.npz")):
        print(f"  {p.name}: {npz_info(p)}")

print("\n=== OLD data/experiment_006 npz keys (P2, soft/软体) ===")
e6 = OLD / "data" / "experiment_006"
if e6.exists():
    for p in sorted(e6.glob("*.npz")):
        print(f"  {p.name}: {npz_info(p)}")

print("\n=== NEW 数据备份 处理后的数据 ===")
for sub in ("机械臂数据", "软体平台数据"):
    p = NEW / "数据备份" / sub / "处理后的数据"
    if not p.exists():
        print(f"  {sub} MISSING")
        continue
    for f in sorted(p.iterdir()):
        if f.suffix == ".npz":
            print(f"  {sub}/{f.name}: {npz_info(f)}")
        elif f.suffix == ".mat":
            print(f"  {sub}/{f.name}: {mat_info(f)}")
        else:
            print(f"  {sub}/{f.name}: ({f.stat().st_size} B, not inspected)")
