from pathlib import Path
import json
import numpy as np

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
DATA = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\spike_p1_structured_lifting.json")

def pairs(horizon=1):
    out = []
    for f in ["train.npz", "val.npz"]:
        z = np.load(DATA / f)
        x, u, tid = z["x"].astype(float), z["u"].astype(float), z["trajectory_id"]
        good = tid[:-horizon] == tid[horizon:]
        out.append((x[:-horizon][good], u[:-horizon][good], x[horizon:][good]))
    return out

def ridge(Phi, Y, lam=1e-6):
    return np.linalg.solve(Phi.T @ Phi + lam * np.eye(Phi.shape[1]), Phi.T @ Y)

def rmse(P, Y):
    return float(np.sqrt(np.mean((P - Y) ** 2)))

def raw_features(x, u):
    return np.c_[np.ones(len(x)), x, u]

def structured_features(x, u):
    q, dq = x[:, [0, 2, 4]], x[:, [1, 3, 5]]
    return np.c_[np.ones(len(x)), x, np.sin(q), np.cos(q), dq ** 2, u]

(xt, ut, yt), (xv, uv, yv) = pairs(1)
results = {}
for name, feat in [("raw_affine", raw_features), ("structured_physics", structured_features)]:
    W = ridge(feat(xt, ut), yt)
    results[name] = {
        "n_features": int(feat(xt, ut).shape[1]),
        "train_rmse": rmse(feat(xt, ut) @ W, yt),
        "val_rmse": rmse(feat(xv, uv) @ W, yv),
    }

for h in [2, 3]:
    (xt, ut, yt), (xv, uv, yv) = pairs(h)
    W = ridge(structured_features(xt, ut), yt)
    results["structured_physics_h%d" % h] = {
        "n_features": int(structured_features(xt, ut).shape[1]),
        "val_rmse": rmse(structured_features(xv, uv) @ W, yv),
    }

results["p1_input_semantics"] = "joint torque/current command (user-confirmed); joint-2 torque has large gravity offset"
results["warning"] = "Offline regression diagnostics only; not a Koopman/EL theorem and not a control result."
print(json.dumps(results, indent=2))
OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
