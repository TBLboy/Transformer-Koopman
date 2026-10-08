from pathlib import Path
import numpy as np

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
for plat, sub in [("P1", "机械臂数据"), ("P2", "软体平台数据")]:
    d = ROOT / "数据备份" / sub / "处理后的数据"
    print("==", plat, d)
    for f in ["train.npz", "val.npz", "test.npz"]:
        p = d / f
        if not p.exists():
            print("  missing", f)
            continue
        z = np.load(p)
        x = z["x"]
        info = {k: (z[k].shape if hasattr(z[k], "shape") else None) for k in z.files}
        tid = z["trajectory_id"] if "trajectory_id" in z.files else None
        ntraj = int(len(np.unique(tid))) if tid is not None else None
        print(f"  {f}: x={x.shape} traj={ntraj} keys={z.files}")
