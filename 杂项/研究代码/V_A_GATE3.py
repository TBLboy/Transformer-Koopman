from pathlib import Path
import json
import numpy as np
import torch

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
P2D = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\V_A_GATE3.json")
L = 4
H_MAX = 20

def load(split):
    z = np.load(P2D / f"{split}.npz")
    x = z["x"].astype(float); u = z["u"].astype(float); tid = z["trajectory_id"]
    return [(x[np.where(tid == t)[0]], u[np.where(tid == t)[0]]) for t in np.unique(tid)]

def samples(trajs):
    Xk, U, D, P = [], [], [], []
    for xx, uu in trajs:
        for k in range(L, len(xx) - 1):
            Xk.append(xx[k]); U.append(uu[k]); D.append(xx[k + 1] - xx[k])
            P.append(np.concatenate([xx[k - j] for j in range(L)] + [uu[k - j] for j in range(1, L + 1) if k - j >= 0]))
    return map(np.array, (Xk, U, D, P))

tr = load("train"); va = load("val")
Xtr, Utr, Dtr, Ptr = samples(tr)
Xva, Uva, Dva, Pva = samples(va)

def lin(A, Y):
    th, *_ = np.linalg.lstsq(A, Y, rcond=None); return th
thn = lin(np.hstack([Utr, Xtr, np.ones((len(Utr), 1))]), Dtr)
thc = lin(np.hstack([Utr, Xtr, Ptr, np.ones((len(Utr), 1))]), Dtr)
J0 = thc[:Utr.shape[1]].T

d_z, d_c, r = Dtr.shape[1], Ptr.shape[1], 3
P_t = torch.tensor(Ptr, dtype=torch.float32); U_t = torch.tensor(Utr, dtype=torch.float32)
X_t = torch.tensor(Xtr, dtype=torch.float32); D_t = torch.tensor(Dtr, dtype=torch.float32)

class Mult(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.g = torch.nn.Sequential(torch.nn.Linear(d_c, 32), torch.nn.Tanh(), torch.nn.Linear(32, r))
        self.U = torch.nn.Parameter(0.01 * torch.randn(d_z, r)); self.V = torch.nn.Parameter(0.01 * torch.randn(d_z, r))
        self.J0 = torch.nn.Parameter(torch.tensor(J0, dtype=torch.float32))
        self.W = torch.nn.Parameter(torch.tensor(thc[Utr.shape[1]+Xtr.shape[1]:Utr.shape[1]+Xtr.shape[1]+Ptr.shape[1]].T, dtype=torch.float32))
        self.Wx = torch.nn.Parameter(torch.tensor(thc[Utr.shape[1]:Utr.shape[1]+Xtr.shape[1]].T, dtype=torch.float32))
        self.b = torch.nn.Parameter(torch.tensor(thc[-1], dtype=torch.float32))
    def forward(self, x, u, phi):
        gg = self.g(phi); Ug = self.U.unsqueeze(0) * gg.unsqueeze(1)
        J = self.J0.unsqueeze(0) + Ug @ self.V.transpose(0, 1)
        return torch.einsum('nij,nj->ni', J, u) + x @ self.Wx.transpose(0, 1) + phi @ self.W.transpose(0, 1) + self.b

torch.manual_seed(0)
m = Mult(); opt = torch.optim.Adam(m.parameters(), lr=2e-3)
for _ in range(5000):
    opt.zero_grad(); ((m(X_t, U_t, P_t) - D_t) ** 2).mean().backward(); opt.step()
m.eval()

def pred_noctx(x, u): return (npx_thn_J := None) or (thn[:Utr.shape[1]].T @ u + thn[Utr.shape[1]:Utr.shape[1]+Xtr.shape[1]].T @ x + thn[-1])
def pred_add(x, u, phi): return thc[:Utr.shape[1]].T @ u + thc[Utr.shape[1]:Utr.shape[1]+Xtr.shape[1]].T @ x + thc[Utr.shape[1]+Xtr.shape[1]:Utr.shape[1]+Xtr.shape[1]+Ptr.shape[1]].T @ phi + thc[-1]
def pred_mult(x, u, phi):
    with torch.no_grad():
        return m(torch.tensor(x, dtype=torch.float32).unsqueeze(0), torch.tensor(u, dtype=torch.float32).unsqueeze(0),
                 torch.tensor(phi, dtype=torch.float32).unsqueeze(0)).squeeze(0).numpy()

def rollout_consistent(pred, trajs, mode):
    errs = {h: [] for h in (1, 5, 10, 20)}
    for xx, uu in trajs:
        for k in range(L, len(xx) - H_MAX):
            buf = [xx[k - j] for j in range(L)][::-1]  # oldest..newest of past L true states
            xh = xx[k].copy(); buf = buf + [xh]
            for i in range(1, H_MAX + 1):
                kk = k + i - 1
                past = buf[-(L + 1):-1][::-1]  # x_{kk}, x_{kk-1}, ...
                phi = np.concatenate(past + [uu[kk - j] for j in range(1, L + 1) if kk - j >= 0])
                dh = pred(xh, uu[kk]) if mode == "noctx" else pred(xh, uu[kk], phi)
                xh = xh + dh; buf.append(xh)
                if i in errs: errs[i].append(np.linalg.norm(xh - xx[k + i]))
    return {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in errs.items()}

res = {"consistent_rollout_val_rmse": {}}
for name, fn, mode in (("noctx", pred_noctx, "noctx"), ("add", pred_add, "ctx"), ("mult", pred_mult, "ctx")):
    res["consistent_rollout_val_rmse"][name] = rollout_consistent(fn, va, mode)
b = res["consistent_rollout_val_rmse"]
res["mult_vs_noctx_pct"] = {str(h): round(100*(b["noctx"][h]-b["mult"][h])/b["noctx"][h], 1) for h in (1,5,10,20)}
res["mult_vs_add_pct"] = {str(h): round(100*(b["add"][h]-b["mult"][h])/b["add"][h], 1) for h in (1,5,10,20)}
print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
