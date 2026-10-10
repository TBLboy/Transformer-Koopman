from pathlib import Path
import json
import numpy as np

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
DATA = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\p1_residual_structure.json")

PAIRS = [(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)]

def load(f):
    z = np.load(DATA / f)
    return z["x"].astype(float), z["u"].astype(float), z["t"].astype(float), z["trajectory_id"]

def prepare(x, t):
    q = x[:, [0, 2, 4]]
    dq = x[:, [1, 3, 5]]
    acc = np.stack([np.gradient(dq[:, j], t) for j in range(3)], axis=1)
    return q, dq, acc

def build(q, dq, acc):
    n = len(q)
    blocks = []

    def add(col, j):
        c = np.zeros((n, 3))
        c[:, j] = col
        blocks.append(c)

    for (i, j) in PAIRS:
        base = np.zeros((n, 3))
        base[:, i] += acc[:, j]
        if i != j:
            base[:, j] += acc[:, i]
        for qk in [np.ones(n), q[:, 0], q[:, 1], q[:, 2]]:
            blocks.append(base * qk[:, None])
    for i in range(3):
        for a in range(3):
            for b in range(a, 3):
                add(dq[:, a] * dq[:, b], i)
    for i in range(3):
        add(np.sign(dq[:, i]), i)
    gbasis = [np.ones(n), q[:, 0], q[:, 1], q[:, 2],
              np.sin(q[:, 0]), np.sin(q[:, 1]), np.sin(q[:, 2]),
              np.cos(q[:, 0]), np.cos(q[:, 1]), np.cos(q[:, 2])]
    for i in range(3):
        for g in gbasis:
            add(g, i)
    K = len(blocks)
    return np.stack(blocks, axis=1).reshape(n, K * 3)

def fit(Phi, y, lam=1e-6):
    return np.linalg.solve(Phi.T @ Phi + lam * np.eye(Phi.shape[1]), Phi.T @ y)

xt, ut, tt, tidt = load("train.npz")
xv, uv, tv, tidv = load("val.npz")
qt, dqt, acct = prepare(xt, tt)
qv, dqv, accv = prepare(xv, tv)

W = fit(build(qt, dqt, acct), ut)
pred = build(qv, dqv, accv) @ W
res = uv - pred  # (n,3)

out = {}
for j in range(3):
    r = res[:, j]
    out["joint_%d" % (j + 1)] = {
        "residual_std": float(r.std()),
        "residual_mean": float(r.mean()),
        "lag1_autocorr": float(np.corrcoef(r[:-1], r[1:])[0, 1]),
        "corr_with_acc": float(np.corrcoef(r, accv[:, j])[0, 1]),
        "corr_with_dq": float(np.corrcoef(r, dqv[:, j])[0, 1]),
        "corr_with_sign_dq": float(np.corrcoef(r, np.sign(dqv[:, j]))[0, 1]),
        "corr_with_pred": float(np.corrcoef(r, pred[:, j])[0, 1]),
    }

out["warning"] = "Residual structure diagnostics; high lag-1 autocorrelation or correlation with states indicates unmodeled dynamics rather than white measurement noise."
print(json.dumps(out, indent=2))
OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
