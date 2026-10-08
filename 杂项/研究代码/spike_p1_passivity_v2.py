from pathlib import Path
import json
import numpy as np

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
DATA = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\spike_p1_passivity_v2.json")

PAIRS = [(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)]

def load(f):
    z = np.load(DATA / f)
    return z["x"].astype(float), z["u"].astype(float), z["t"].astype(float)

def prepare(x, t):
    q = x[:, [0, 2, 4]]
    dq = x[:, [1, 3, 5]]
    acc = np.stack([np.gradient(dq[:, j], t) for j in range(3)], axis=1)
    return q, dq, acc

def build(q, dq, acc):
    n = len(q)
    blocks = []

    def add(col, tag):
        c = np.zeros((n, 3))
        c[:, tag[0]] = col
        blocks.append(c)

    # M(q) qddot with M(q) = M0 + q1 M1 + q2 M2 + q3 M3 (symmetric)
    for (i, j) in PAIRS:
        base = np.zeros((n, 3))
        base[:, i] += acc[:, j]
        if i != j:
            base[:, j] += acc[:, i]
        for qk in [np.ones(n), q[:, 0], q[:, 1], q[:, 2]]:
            c = base * qk[:, None]
            blocks.append(c)

    # Coriolis/centrifugal: quadratic velocity terms per output
    for i in range(3):
        for a in range(3):
            for b in range(a, 3):
                add(dq[:, a] * dq[:, b], (i,))
    # Coulomb friction per joint
    for i in range(3):
        add(np.sign(dq[:, i]), (i,))
    # gravity basis per joint
    gbasis = [np.ones(n), q[:, 0], q[:, 1], q[:, 2],
              np.sin(q[:, 0]), np.sin(q[:, 1]), np.sin(q[:, 2]),
              np.cos(q[:, 0]), np.cos(q[:, 1]), np.cos(q[:, 2])]
    for i in range(3):
        for g in gbasis:
            add(g, (i,))

    K = len(blocks)
    Phi = np.stack(blocks, axis=1).reshape(n, K * 3)
    return Phi, K

def fit(Phi, y, lam=1e-6):
    return np.linalg.solve(Phi.T @ Phi + lam * np.eye(Phi.shape[1]), Phi.T @ y)

def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))

xt, ut, tt = load("train.npz")
xv, uv, tv = load("val.npz")
qt, dqt, acct = prepare(xt, tt)
qv, dqv, accv = prepare(xv, tv)

Pt, Kt = build(qt, dqt, acct)
Pv, _ = build(qv, dqv, accv)
W = fit(Pt, ut)

res = {
    "n_blocks": Kt,
    "train_rmse_overall": rmse(Pt @ W, ut),
    "val_rmse_per_joint": [float(x) for x in np.sqrt(np.mean((Pv @ W - uv) ** 2, axis=0))],
    "val_rmse_overall": rmse(Pv @ W, uv),
    "torque_std_per_joint": [float(x) for x in ut.std(axis=0)],
    "val_rmse_over_std": [float(a / b) for a, b in zip(np.sqrt(np.mean((Pv @ W - uv) ** 2, axis=0)), ut.std(axis=0))],
}
print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
