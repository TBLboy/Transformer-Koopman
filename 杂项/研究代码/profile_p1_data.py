from pathlib import Path
import json
import numpy as np

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
DATA = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\p1_data_profile.json")

profile = {}
for f in ["train.npz", "val.npz", "test.npz"]:
    z = np.load(DATA / f)
    x, u, tid = z["x"], z["u"], z["trajectory_id"]
    profile[f] = {
        "x_shape": list(x.shape),
        "u_shape": list(u.shape),
        "n_traj": int(len(np.unique(tid))),
        "x_min": x.min(axis=0).round(5).tolist(),
        "x_max": x.max(axis=0).round(5).tolist(),
        "x_std": x.std(axis=0).round(5).tolist(),
        "u_min": u.min(axis=0).round(5).tolist(),
        "u_max": u.max(axis=0).round(5).tolist(),
        "u_std": u.std(axis=0).round(5).tolist(),
        "u_absmean": np.abs(u).mean(axis=0).round(5).tolist(),
    }

# Sanity: does dq (columns 1,3,5) look like the time-derivative of q (columns 0,2,4)?
z = np.load(DATA / "train.npz")
x, t = z["x"], z["t"]
diffs = []
for i in [0, 2, 4]:
    dq = x[:, i + 1]
    dq_num = np.gradient(x[:, i], t) if t.ndim == 1 else np.gradient(x[:, i])
    scale = np.std(dq) + 1e-12
    diffs.append(float(np.std(dq - dq_num) / scale))
profile["velocity_consistency_relative_error"] = diffs
profile["p1_input_semantics_reported_by_user"] = "joint torque / current command"

print(json.dumps(profile, indent=2))
OUT.write_text(json.dumps(profile, indent=2), encoding="utf-8")
