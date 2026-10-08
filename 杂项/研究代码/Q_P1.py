from pathlib import Path
import json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
DATA = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\Q_P1.json")

z = np.load(DATA / "train.npz")
print("keys:", list(z.keys()))
x = z["x"].astype(float); u = z["u"].astype(float)
tid = z["trajectory_id"] if "trajectory_id" in z else np.zeros(len(x), int)
print("x", x.shape, "u", u.shape)

def norm_fit(a):
    return a.mean(0, keepdims=True), a.std(0, keepdims=True) + 1e-9
xm, xs = norm_fit(x); um, us = norm_fit(u)
xn = (x - xm) / xs; un = (u - um) / us

Z, U, Zp = [], [], []
for t in np.unique(tid):
    m = tid == t
    xi = xn[m]; ui = un[m]
    if len(xi) < 3: continue
    Z.append(xi[:-1]); U.append(ui[:-1]); Zp.append(xi[1:])
Z = np.concatenate(Z); U = np.concatenate(U); Zp = np.concatenate(Zp)
n, m = Z.shape[1], U.shape[1]
print("pairs", Z.shape)

X = np.hstack([Z, U])
th0, *_ = np.linalg.lstsq(X, Zp, rcond=None)
R0 = Zp - X @ th0
rmse0 = float(np.sqrt((R0**2).mean()))
A_hat = th0[:n].T; B_hat = th0[n:].T
ev0 = np.linalg.eigvalsh(np.cov(R0.T)); evn = np.sort(ev0)[::-1] / ev0.sum()
def effr(ev, th):
    e = np.sort(ev)[::-1]; e = e / e.sum(); return int(np.searchsorted(np.cumsum(e), th) + 1)
# residual energy in im(B)
Ub = np.linalg.svd(B_hat, full_matrices=False)[0][:, :m]
frac_imB = float(((R0 @ Ub)**2).sum() / (R0**2).sum())

torch.manual_seed(0)
Zt = torch.tensor(Z, dtype=torch.float32); Ut = torch.tensor(U, dtype=torch.float32); Zpt = torch.tensor(Zp, dtype=torch.float32)
th_init = torch.tensor(th0, dtype=torch.float32)

class MLP(nn.Module):
    def __init__(s, h=32): super().__init__(); s.f = nn.Sequential(nn.Linear(n, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, m))
    def forward(s, Z): return s.f(Z)

def fit_prefb(epochs=4000, lr=3e-3):
    A = nn.Parameter(th_init[:n].clone()); B = nn.Parameter(th_init[n:].clone())
    al = MLP()
    opt = torch.optim.Adam([A, B] + list(al.parameters()), lr=lr)
    for _ in range(epochs):
        opt.zero_grad()
        pred = Zt @ A + (Ut - al(Zt)) @ B
        F.mse_loss(pred, Zpt).backward(); opt.step()
    with torch.no_grad():
        R = (Zpt - (Zt @ A + (Ut - al(Zt)) @ B)).numpy()
    return R

def fit_fulldrift(epochs=4000, lr=3e-3):
    A = nn.Parameter(th_init[:n].clone()); B = nn.Parameter(th_init[n:].clone())
    f = nn.Sequential(nn.Linear(n, 32), nn.Tanh(), nn.Linear(32, 32), nn.Tanh(), nn.Linear(32, n))
    opt = torch.optim.Adam([A, B] + list(f.parameters()), lr=lr)
    for _ in range(epochs):
        opt.zero_grad()
        pred = Zt @ A + Ut @ B + f(Zt)
        F.mse_loss(pred, Zpt).backward(); opt.step()
    with torch.no_grad():
        R = (Zpt - (Zt @ A + Ut @ B + f(Zt))).numpy()
    return R

R_pre = fit_prefb(); R_full = fit_fulldrift()
def summ(R):
    ev = np.linalg.eigvalsh(np.cov(R.T))
    return {"rmse": round(float(np.sqrt((R**2).mean())), 6), "rank90": effr(ev, 0.9), "rank99": effr(ev, 0.99),
            "imB_frac": round(float(((R @ Ub)**2).sum() / (R**2).sum()), 4)}

res = {
    "baseline_rmse": round(rmse0, 6), "baseline_rank90": effr(ev0, 0.9), "baseline_rank99": effr(ev0, 0.99),
    "baseline_imB_frac": round(frac_imB, 4),
    "resid_eig_norm": [round(float(v), 5) for v in evn],
    "nonlinear_prefeedback_rank_m": summ(R_pre),
    "full_nonlinear_drift_rank_n": summ(R_full),
    "note": "P1 fully observed; z=x. If nonlinear alpha absorbs gravity (input-channel) the residual drops but this is standard nonlinear identification.",
}
print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
