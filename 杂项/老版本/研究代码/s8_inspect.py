"""S8 inspection: processed npz data keys/shapes and the deploy platform2 checkpoint.
Read-only. Uses project interpreter (edmddl2). No code/data modification.
"""
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")

DATA = {
    "P1_arm": ROOT / "数据备份" / "机械臂数据" / "处理后的数据",
    "P2_soft": ROOT / "数据备份" / "软体平台数据" / "处理后的数据",
}
for name, d in DATA.items():
    print("=" * 70)
    print(f"[{name}] {d}")
    for fn in ["train.npz", "val.npz", "test.npz"]:
        p = d / fn
        if not p.is_file():
            print(f"  {fn}: MISSING")
            continue
        z = np.load(str(p), allow_pickle=True)
        print(f"  {fn}: {p.stat().st_size/1e6:.2f} MB")
        for k in z.files:
            a = z[k]
            if a.dtype == object:
                print(f"    {k}: object {a.shape}")
            else:
                print(f"    {k}: {a.dtype} {a.shape} "
                      f"min={np.min(a):.4g} max={np.max(a):.4g} mean={np.mean(a):.4g}")

print("=" * 70)
print("[raw P2 sample] 01.npz")
p = ROOT / "数据备份" / "软体平台数据" / "原始数据" / "01.npz"
z = np.load(str(p), allow_pickle=True)
for k in z.files:
    a = z[k]
    if a.dtype == object:
        print(f"  {k}: object {a.shape}")
    else:
        print(f"  {k}: {a.dtype} {a.shape} min={np.min(a):.4g} max={np.max(a):.4g}")

print("=" * 70)
print("[deploy checkpoint] platform2_full_model.pth")
import torch
pth = ROOT / "训练代码" / "deploy" / "algorithms" / "tk_assets" / "model_assets" / "platform2_full_model.pth"
ck = torch.load(str(pth), map_location="cpu", weights_only=False)
if isinstance(ck, dict):
    for k, v in ck.items():
        if isinstance(v, (np.ndarray,)):
            print(f"  {k}: ndarray {v.shape}")
        elif isinstance(v, torch.Tensor):
            print(f"  {k}: tensor {tuple(v.shape)}")
        elif isinstance(v, dict):
            print(f"  {k}: dict keys={list(v.keys())[:15]}")
        elif isinstance(v, (int, float, str, bool)):
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: {type(v).__name__}")
else:
    print("  checkpoint type:", type(ck).__name__)
print("DONE")
