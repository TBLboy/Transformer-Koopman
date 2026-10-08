from pathlib import Path
import json
import numpy as np

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
DATA = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"

def features(x, u, kind):
    # affine: [1, x, u]; bilinear: [1, x, u, vec(x outer u)]
    n = len(x)
    base = [np.ones((n, 1)), x, u]
    if kind == "bilinear":
        base.append(np.einsum("ni,nj->nij", x, u).reshape(n, -1))
    return np.concatenate(base, axis=1)

def fit_eval(kind):
    tr = np.load(DATA / "train.npz")
    va = np.load(DATA / "val.npz")
    # Avoid cross-trajectory transitions.
    def pairs(z):
        x, u, tid = z["x"], z["u"], z["trajectory_id"]
        good = tid[:-1] == tid[1:]
        return x[:-1][good], u[:-1][good], x[1:][good]
    xt, ut, yt = pairs(tr)
    xv, uv, yv = pairs(va)
    Phi = features(xt, ut, kind)
    # fixed ridge for conditioning
    lam = 1e-5
    W = np.linalg.solve(Phi.T @ Phi + lam * np.eye(Phi.shape[1]), Phi.T @ yt)
    pred_t = features(xt, ut, kind) @ W
    pred_v = features(xv, uv, kind) @ W
    return {
        "kind": kind,
        "n_features": int(Phi.shape[1]),
        "train_rmse": float(np.sqrt(np.mean((pred_t - yt) ** 2))),
        "val_rmse": float(np.sqrt(np.mean((pred_v - yv) ** 2))),
        "val_mae": float(np.mean(np.abs(pred_v - yv))),
    }

out = [fit_eval("affine"), fit_eval("bilinear")]
print(json.dumps(out, indent=2))
Path(r"C:\Users\12187\AppData\Local\Temp\opencode\spike_p2_bilinear.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
