import re
import sys
from pathlib import Path

import numpy as np
from scipy.io import loadmat

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman")
NEW = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\数据备份")


def numkey(p):
    return int(re.search(r"data(\d+)\.mat$", p.name).group(1))


mats = sorted((NEW / "机械臂数据" / "原始数据").glob("*.mat"), key=numkey)
chunks = []
for p in mats:
    s = loadmat(p)[p.stem][0, 0]
    chunks.append((numkey(p), p.stem, np.asarray(s["q"], dtype=np.float64)))

old = OLD / "data" / "experiment_001"
splits = {name: np.load(old / f"{name}.npz")["x"] for name in ("train", "val", "test")}
for k, v in splits.items():
    print(f"  OLD {k}: {v.shape}")


def locate(chunk):
    """Return (split, start) if chunk appears contiguously in one split."""
    first = chunk[0]
    for name, arr in splits.items():
        cand = np.nonzero(np.all(arr == first, axis=1))[0]
        for c in cand:
            if c + len(chunk) <= len(arr) and np.array_equal(arr[c:c + len(chunk)], chunk):
                return name, int(c)
    return None, None


print("\n=== file -> split mapping (exact block match) ===")
mapping = {}
for idx, stem, chunk in chunks:
    name, start = locate(chunk)
    mapping[idx] = (name, start, len(chunk))
    print(f"  {stem:<10} rows={len(chunk):<6} -> {name:<6} start={start}")

print("\n=== do splits preserve file order? ===")
for name in ("train", "val", "test"):
    ids = [i for i, (n, s, c) in mapping.items() if n == name]
    starts = [s for i, (n, s, c) in mapping.items() if n == name]
    ids_sorted = sorted(ids, key=lambda i: mapping[i][1])
    print(f"  {name}: files={ids}  starts={starts}  in-file-order-by-start={ids_sorted}")
    print(f"    ascending file ids matches ascending starts? {ids == ids_sorted}")
    contig = all(mapping[a][1] + mapping[a][2] == mapping[b][1]
                 for a, b in zip(ids_sorted, ids_sorted[1:]))
    print(f"    blocks are contiguous in the split? {contig}")

print("\n=== verify full reconstruction of each split ===")
for name in ("train", "val", "test"):
    parts = [c for i, (n, s, c) in sorted(mapping.items(), key=lambda kv: kv[1][1]) if n == name]
    if not parts:
        continue
    rebuilt = np.concatenate(parts, 0)
    print(f"  {name}: rebuilt {rebuilt.shape} == stored {splits[name].shape} -> {np.array_equal(rebuilt, splits[name])}")

print("\n=== P2 raw sanity: all 100 files ===")
p2raw = NEW / "软体平台数据" / "原始数据"
npz = sorted(p2raw.glob("*.npz"), key=lambda p: int(p.stem))
shapes = set()
rows = []
for p in npz:
    with np.load(p, allow_pickle=True) as d:
        shapes.add((d["x"].shape, d["u"].shape, d["t"].shape))
        rows.append(len(d["x"]))
print(f"  files={len(npz)}  distinct shapes={shapes}  total rows={sum(rows)}  per-file={set(rows)}")
print(f"  expected rows if one row consumed per trajectory as target: {sum(rows) - len(npz)}")
