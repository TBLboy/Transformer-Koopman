import sys
from pathlib import Path

import numpy as np
from scipy.io import loadmat

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

NEW = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\数据备份")


def describe(v, depth=0, maxdepth=4, name="?"):
    pad = "  " * depth
    if isinstance(v, np.ndarray) and v.dtype.names:
        print(f"{pad}{name}: struct{v.shape} fields={v.dtype.names}")
        if depth < maxdepth:
            item = v.reshape(-1)[0] if v.size else None
            if item is not None:
                for f in v.dtype.names:
                    describe(item[f], depth + 1, maxdepth, f)
        return
    if isinstance(v, np.ndarray):
        if v.dtype == object:
            print(f"{pad}{name}: ndarray{v.shape} dtype=object")
            if depth < maxdepth and v.size:
                describe(v.reshape(-1)[0], depth + 1, maxdepth, name + "[0]")
            return
        extra = ""
        if v.size and v.dtype.kind in "fiu":
            flat = v.reshape(-1)
            extra = f" min={np.nanmin(flat):.6g} max={np.nanmax(flat):.6g} head={np.asarray(flat[:4]).tolist()}"
        print(f"{pad}{name}: {v.shape} {v.dtype}{extra}")
        return
    print(f"{pad}{name}: {type(v).__name__} = {repr(v)[:120]}")


print("=== CURRENT STATE: 处理后的数据 (both platforms) ===")
for sub in ("机械臂数据", "软体平台数据"):
    p = NEW / sub / "处理后的数据"
    print(f"\n-- {sub}/处理后的数据 --")
    if p.exists():
        for f in sorted(p.iterdir()):
            print(f"   {f.stat().st_size:>10} B  {f.name}")
    else:
        print("   MISSING")

print("\n=== P1 机械臂: 处理后的数据 .mat structures ===")
for fn in ("train_data.mat", "val_data.mat", "test_data.mat"):
    p = NEW / "机械臂数据" / "处理后的数据" / fn
    print(f"\n-- {fn} --")
    if not p.exists():
        print("   MISSING")
        continue
    try:
        d = loadmat(p)
        for k, v in d.items():
            if k.startswith("__"):
                continue
            describe(v, 1, 4, k)
    except Exception as e:
        print(f"   ERROR {type(e).__name__}: {e}")

print("\n=== P1 机械臂: 原始数据 (first 2 files) ===")
raw = NEW / "机械臂数据" / "原始数据"
files = sorted(raw.glob("*.mat"))
print(f"   count={len(files)}  names={[f.name for f in files[:3]]} ... {[f.name for f in files[-2:]]}")
for p in files[:2]:
    print(f"\n-- {p.name} --")
    try:
        d = loadmat(p)
        for k, v in d.items():
            if k.startswith("__"):
                continue
            describe(v, 1, 4, k)
    except Exception as e:
        print(f"   ERROR {type(e).__name__}: {e}")

print("\n=== P2 软体平台: 处理后的数据 npz ===")
p2 = NEW / "软体平台数据" / "处理后的数据"
for f in sorted(p2.iterdir()) if p2.exists() else []:
    if f.suffix != ".npz":
        continue
    print(f"\n-- {f.name} --")
    try:
        with np.load(f, allow_pickle=True) as d:
            for k in d.files:
                a = d[k]
                extra = ""
                if a.dtype.kind in "fiu" and a.size:
                    extra = f" min={np.nanmin(a):.6g} max={np.nanmax(a):.6g}"
                    if a.ndim == 1:
                        extra += f" head={a[:5].tolist()}"
                print(f"   {k}: {a.shape} {a.dtype}{extra}")
            if "trajectory_id" in d.files and "step_index" in d.files:
                tid, si = d["trajectory_id"], d["step_index"]
                print(f"   unique trajectory_id ({len(np.unique(tid))}): {np.unique(tid)[:8].tolist()} ...")
                print(f"   step_index monotonic within first 30? {bool(np.all(np.diff(si[:30])==1))}")
    except Exception as e:
        print(f"   ERROR {type(e).__name__}: {e}")
