from pathlib import Path
import json
import numpy as np

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
DATA = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\testC_residual_ar.json")

PAIRS = [(0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)]

def load(f):
    z = np.load(DATA / f)
    return z["x"].astype(float), z["u"].astype(float), z["t"].astype(float), z["trajectory_id"]

def prepare(x, t):
    q = x[:, [0, 2, 4]]; dq = x[:, [1, 3, 5]]
    acc = np.stack([np.gradient(dq[:, j], t) for j in range(3)], axis=1)
    return q, dq, acc

def build(q, dq, acc):
    n = len(q); blocks = []
    def add(col, j):
        c = np.zeros((n, 3)); c[:, j] = col; blocks.append(c)
    for (i, j) in PAIRS:
        base = np.zeros((n, 3)); base[:, i] += acc[:, j]
        if i != j: base[:, j] += acc[:, i]
        for qk in [np.ones(n), q[:, 0], q[:, 1], q[:, 2]]:
            blocks.append(base * qk[:, None])
    for i in range(3):
        for a in range(3):
            for b in range(a, 3):
                add(dq[:, a] * dq[:, b], i)
    for i in range(3):
        add(np.sign(dq[:, i]), i)
    for i in range(3):
        for g in [np.ones(n), q[:, 0], q[:, 1], q[:, 2],
                  np.sin(q[:, 0]), np.sin(q[:, 1]), np.sin(q[:, 2]),
                  np.cos(q[:, 0]), np.cos(q[:, 1]), np.cos(q[:, 2])]:
            add(g, i)
    K = len(blocks)
    return np.stack(blocks, axis=1).reshape(n, K * 3)

def fit(Phi, y, lam=1e-6):
    return np.linalg.solve(Phi.T @ Phi + lam * np.eye(Phi.shape[1]), Phi.T @ y)

def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))

xt, ut, tt, tidt = load("train.npz")
xv, uv, tv, tidv = load("val.npz")
qt, dqt, acct = prepare(xt, tt)
qv, dqv, accv = prepare(xv, tv)
W = fit(build(qt, dqt, acct), ut)
res_v = uv - build(qv, dqv, accv) @ W  # (n,3)

out = {"per_joint": {}, "method": "AR(p) fit on train residual, evaluated on val residual; baseline predicts 0 (white)"}
# add small ridge for AR; use train residual for fitting AR coefficients
res_t = ut - build(qt, dqt, acct) @ W

for j in range(3):
    rtr = res_t[:, j]; rva = res_v[:, j]
    jout = {"residual_std_val": float(rva.std())}
    # ACF on train (within-trajectory pairs)
    acf = []
    rr = rtr - rtr.mean()
    denom = float(np.dot(rr, rr))
    for lag in range(1, 6):
        acf.append(float(np.dot(rr[:-lag], rr[lag:]) / denom))
    jout["acf_lag1..5"] = acf
    # AR(p) least squares: r_k = a1 r_{k-1}+...+ap r_{k-p}
    for p in [1, 2, 4]:
        Xtr = np.stack([res_t[p - i - 1:len(res_t) - i - 1, j] for i in range(p)], axis=1)
        ytr = res_t[p:, j]
        coef, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
        # eval one-step on val
        Xva = np.stack([res_v[p - i - 1:len(res_v) - i - 1, j] for i in range(p)], axis=1)
        yva = res_v[p:, j]
        pred = Xva @ coef
        base = rmse(np.zeros_like(yva), yva)
        jout["AR%d_one_step_val_rmse" % p] = rmse(pred, yva)
        jout["AR%d_improvement_over_white" % p] = float(1 - rmse(pred, yva) / base)
    out["per_joint"]["joint_%d" % (j + 1)] = jout

out["verdict"] = "If AR improvements are substantial, residual has predictable dynamics (R3 supported)."
print(json.dumps(out, indent=2))
OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
