from pathlib import Path
import json
import numpy as np

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
DATA = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\p1_dt_noise_check.json")

z = np.load(DATA / "train.npz")
x, t, tid = z["x"].astype(float), z["t"].astype(float), z["trajectory_id"]

dt_all = np.diff(t)
res = {
    "dt_median": float(np.median(dt_all)),
    "dt_min": float(dt_all.min()),
    "dt_max": float(dt_all.max()),
    "t_range": [float(t.min()), float(t.max())],
}
# per-trajectory sampling
traj0 = tid == tid[0]
t0 = t[traj0]
res["n_samples_traj0"] = int(traj0.sum())
res["dt_traj0_median"] = float(np.median(np.diff(t0)))
res["dt_traj0_min"] = float(np.diff(t0).min())
res["dt_traj0_max"] = float(np.diff(t0).max())

# acceleration roughness: ratio of std of qddot to scale of velocity differences
dq = x[:, [1, 3, 5]]
acc = np.stack([np.gradient(dq[:, j], t) for j in range(3)], axis=1)
res["acc_std_per_joint"] = [float(a) for a in acc.std(axis=0)]
# second difference of position as alternative acceleration (uniform-ish)
q = x[:, [0, 2, 4]]
res["q_std_per_joint"] = [float(a) for a in q.std(axis=0)]
res["dq_std_per_joint"] = [float(a) for a in dq.std(axis=0)]

print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
