from pathlib import Path
import json
import numpy as np

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
DATA = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\spike_p1_passivity.json")

def load(f):
    z = np.load(DATA / f)
    return z["x"].astype(float), z["u"].astype(float), z["t"].astype(float)

def prepare(x, t):
    q = x[:, [0, 2, 4]]
    dq = x[:, [1, 3, 5]]
    acc = np.stack([np.gradient(dq[:, j], t) for j in range(3)], axis=1)
    return q, dq, acc

PAIRS = [(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)]

def build(q, dq, acc):
    n = len(q)
    blocks = []
    tags = []
    # symmetric constant inertia M qddot
    for (i, j) in PAIRS:
        c = np.zeros((n, 3))
        c[:, i] += acc[:, j]
        if i != j:
            c[:, j] += acc[:, i]
        blocks.append(c)
        tags.append(("M", i, j))
    # constant viscous C qdot (full 3x3)
    for i in range(3):
        for j in range(3):
            c = np.zeros((n, 3))
            c[:, i] += dq[:, j]
            blocks.append(c)
            tags.append(("C", i, j))
    # gravity basis per joint: [1, q1, q2, q3, sin q1..3, cos q1..3]
    gbasis = [np.ones(n), q[:, 0], q[:, 1], q[:, 2],
              np.sin(q[:, 0]), np.sin(q[:, 1]), np.sin(q[:, 2]),
              np.cos(q[:, 0]), np.cos(q[:, 1]), np.cos(q[:, 2])]
    for i in range(3):
        for gi, g in enumerate(gbasis):
            c = np.zeros((n, 3))
            c[:, i] = g
            blocks.append(c)
            tags.append(("g", i, gi))
    Phi = np.stack(blocks, axis=1)  # (n, k, 3)
    k = Phi.shape[1]
    return Phi.reshape(n, k * 3), tags

def fit(Phi, y, lam=1e-6):
    return np.linalg.solve(Phi.T @ Phi + lam * np.eye(Phi.shape[1]), Phi.T @ y)

xt, ut, tt = load("train.npz")
xv, uv, tv = load("val.npz")
qt, dqt, acct = prepare(xt, tt)
qv, dqv, accv = prepare(xv, tv)

Pt, tags = build(qt, dqt, acct)
Pv, _ = build(qv, dqv, accv)
W = fit(Pt, ut)

# Recover M: pair block (i,j) occupies columns [idx*3, idx*3+3); coefficient for output row r = coil[idx*3+r].
M = np.zeros((3, 3))
for idx, (kind, i, j) in enumerate(tags):
    if kind != "M":
        continue
    M[i, j] = W[idx * 3 + i, i]
    if i != j:
        M[j, i] = W[idx * 3 + j, j]
M = 0.5 * (M + M.T)

results = {
    "el_model_val_rmse_per_joint": [float(x) for x in np.sqrt(np.mean((Pv @ W - uv) ** 2, axis=0))],
    "el_model_val_rmse_overall": float(np.sqrt(np.mean((Pv @ W - uv) ** 2))),
    "torque_std_per_joint": [float(x) for x in ut.std(axis=0)],
    "recovered_constant_M": M.tolist(),
    "recovered_M_eigenvalues": [float(x) for x in np.linalg.eigvalsh(M)],
    "M_positive_definite": bool(np.all(np.linalg.eigvalsh(M) > 0)),
    "recovered_M_condition_number": float(np.linalg.cond(M)),
}
print(json.dumps(results, indent=2))
OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
