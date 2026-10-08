from pathlib import Path
import json
import numpy as np

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
DATA = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\D_P1.json")

def load(f):
    z = np.load(DATA / f)
    return (z["x"].astype(float), z["u"].astype(float),
            z["t"].astype(float), z["trajectory_id"])

def pairs(x, u, tid):
    X, U, Y, TID = [], [], [], []
    for tr in np.unique(tid):
        mask = tid == tr
        xi, ui = x[mask], u[mask]
        if len(xi) < 2: continue
        X.append(xi[:-1]); U.append(ui[:-1]); Y.append(xi[1:]); TID.append(np.full(len(xi) - 1, tr))
    return np.concatenate(X), np.concatenate(U), np.concatenate(Y), np.concatenate(TID)

def fit_lti(X, U, Y, lam=1e-8):
    Phi = np.concatenate([X, U], axis=1)
    W = np.linalg.solve(Phi.T @ Phi + lam * np.eye(Phi.shape[1]), Phi.T @ Y)
    return W[:X.shape[1], :].T, W[X.shape[1]:, :].T

def rmse(a, b): return float(np.sqrt(np.mean((a - b) ** 2)))

def acf_within(x, tid, maxlag=5):
    num = np.zeros(maxlag); den = 0.0
    for tr in np.unique(tid):
        xi = x[tid == tr].ravel(); xi = xi - xi.mean()
        den += float(np.dot(xi, xi))
        for lag in range(1, maxlag + 1):
            num[lag - 1] += float(np.dot(xi[:-lag], xi[lag:]))
    return (num / (den + 1e-30)).tolist()

def ar_improvement(x, tid, p):
    Xl, yl = [], []
    for tr in np.unique(tid):
        xi = x[tid == tr].ravel()
        if len(xi) < p + 1: continue
        for i in range(p, len(xi)):
            Xl.append(xi[i - p:i][::-1]); yl.append(xi[i])
    Xl = np.array(Xl); yl = np.array(yl)
    coef, *_ = np.linalg.lstsq(Xl, yl, rcond=None)
    pred = Xl @ coef
    return float(1 - rmse(pred, yl) / (rmse(np.zeros_like(yl), yl) + 1e-30))

xt, ut, tt, tidt = load("train.npz")
xv, uv, tv, tidv = load("val.npz")
Xtr, Utr, Ytr, TIDtr = pairs(xt, ut, tidt)
Xva, Uva, Yva, TIDva = pairs(xv, uv, tidv)

A, B = fit_lti(Xtr, Utr, Ytr)
Rva = Yva - Xva @ A.T - Uva @ B.T          # state residual (N,6)
Bp = np.linalg.pinv(B)
du = Rva @ Bp.T                             # matched virtual input (N,3)
rec = du @ B.T
recon_err = float(np.linalg.norm(Rva - rec) / (np.linalg.norm(Rva) + 1e-30))

out = {
    "matched_virtual_input_dim": int(du.shape[1]),
    "reconstruction_error_rel": recon_err,
    "raw_residual_std_per_dim": [float(v) for v in Rva.std(axis=0)],
    "du_std_per_joint": [float(v) for v in du.std(axis=0)],
    "du_cross_joint_corr": np.corrcoef(du.T).round(4).tolist(),
    "predictability": {},
}
for j in range(3):
    out["predictability"][f"joint_{j+1}"] = {
        "raw_res_ACF_lag1_5": acf_within(Rva[:, j], TIDva, 5),
        "du_ACF_lag1_5": acf_within(du[:, j], TIDva, 5),
        "raw_res_AR1_impr": ar_improvement(Rva[:, j], TIDva, 1),
        "raw_res_AR4_impr": ar_improvement(Rva[:, j], TIDva, 4),
        "du_AR1_impr": ar_improvement(du[:, j], TIDva, 1),
        "du_AR4_impr": ar_improvement(du[:, j], TIDva, 4),
    }
out["verdict"] = ("P1 residual is matched (im B) with rel recon error ~0; compare du predictability vs raw residual. "
                  "If du is low-dim/more predictable, M7 could serve as P1 mechanism; otherwise graveyard.")
print(json.dumps(out, indent=2))
OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
