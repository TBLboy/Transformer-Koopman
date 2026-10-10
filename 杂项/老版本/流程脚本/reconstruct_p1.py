import re
import sys
from pathlib import Path

import numpy as np
from scipy.io import loadmat

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman")
NEW = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\数据备份")

print("=== P2 软体平台 原始数据: npz structure ===")
p2raw = NEW / "软体平台数据" / "原始数据"
files = sorted(p2raw.glob("*.npz"))
print(f"  count={len(files)}  first={[f.name for f in files[:3]]} last={[f.name for f in files[-2:]]}")
for p in files[:2]:
    print(f"\n-- {p.name} --")
    with np.load(p, allow_pickle=True) as d:
        for k in d.files:
            a = d[k]
            extra = ""
            if a.dtype.kind in "fiu" and a.size:
                extra = f" min={np.nanmin(a):.6g} max={np.nanmax(a):.6g}"
                if a.ndim == 1:
                    extra += f" head={a[:4].tolist()}"
            print(f"   {k}: {a.shape} {a.dtype}{extra}")

print("\n=== P1: reconstruct from 20 raw .mat and compare with OLD experiment_001 ===")


def numkey(p):
    m = re.search(r"data(\d+)\.mat$", p.name)
    return int(m.group(1))


mats = sorted((NEW / "机械臂数据" / "原始数据").glob("*.mat"), key=numkey)
qs, us, ts, counts = [], [], [], []
for p in mats:
    d = loadmat(p)
    s = d[p.stem][0, 0]
    q = np.asarray(s["q"], dtype=np.float64)
    tau = np.asarray(s["tau"], dtype=np.float64)
    t = np.asarray(s["t"], dtype=np.float64).reshape(-1)
    qs.append(q)
    us.append(tau)
    ts.append(t)
    counts.append(len(q))

print(f"  files={len(mats)}  rows per file={counts}")
Q = np.concatenate(qs, 0)
U = np.concatenate(us, 0)
T = np.concatenate(ts, 0)
print(f"  concatenated: x={Q.shape} u={U.shape} t={T.shape}  total={len(Q)}")

cum = np.cumsum(counts)
print(f"  cumulative row counts: {cum.tolist()}")

old = OLD / "data" / "experiment_001"
tr = np.load(old / "train.npz")
va = np.load(old / "val.npz")
te = np.load(old / "test.npz")
print(f"  OLD experiment_001: train={tr['x'].shape} val={va['x'].shape} test={te['x'].shape}")
print(f"  OLD trajectory_id unique: train={np.unique(tr['trajectory_id']).tolist()}")
print(f"                            val  ={np.unique(va['trajectory_id']).tolist()}")
print(f"                            test ={np.unique(te['trajectory_id']).tolist()}")

n_tr, n_va, n_te = len(tr["x"]), len(va["x"]), len(te["x"])
print(f"\n  hypothesis A: old splits are contiguous slices of the concatenation")
print(f"    Q[:n_tr] == train.x ?  {np.array_equal(Q[:n_tr], tr['x'])}")
print(f"    Q[n_tr:n_tr+n_va] == val.x ?  {np.array_equal(Q[n_tr:n_tr + n_va], va['x'])}")
print(f"    Q[n_tr+n_va:] == test.x ?  {np.array_equal(Q[n_tr + n_va:], te['x'])}")
print(f"    U slices match? {np.array_equal(U[:n_tr], tr['u'])}, "
      f"{np.array_equal(U[n_tr:n_tr+n_va], va['u'])}, {np.array_equal(U[n_tr+n_va:], te['u'])}")
print(f"    trajectory_id contiguous 1..20? train={np.unique(tr['trajectory_id'])[:3].tolist()}.."
      f"{np.unique(tr['trajectory_id'])[-1] if len(np.unique(tr['trajectory_id'])) else None}")

print(f"\n  where does cumulative cross the boundary?")
print(f"    n_tr={n_tr} -> files fully included: {int((cum < n_tr).sum())} (+1 partial={n_tr not in cum})")
print(f"    n_tr+n_va={n_tr + n_va} -> {int((cum < n_tr + n_va).sum())} files")
print(f"    total={len(Q)}  last cum={cum[-1]}  match_total={cum[-1] == len(Q)}")
print(f"    OLD total={n_tr + n_va + n_te}")
