from pathlib import Path
import json
import numpy as np
import torch

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
P2D = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\V_A_GATE2.json")
L = 4
H_MAX = 20

def load(split):
    z = np.load(P2D / f"{split}.npz")
    x = z["x"].astype(float); u = z["u"].astype(float); tid = z["trajectory_id"]
    trajs = []
    for t in np.unique(tid):
        m = np.where(tid == t)[0]
        trajs.append((x[m], u[m]))
    return trajs

def samples(trajs):
    Xk, U, D, PHI = [], [], [], []
    for xx, uu in trajs:
        for k in range(L, len(xx) - 1):
            Xk.append(xx[k]); U.append(uu[k]); D.append(xx[k + 1] - xx[k])
            ctx = [xx[k - j] for j in range(L)] + [uu[k - j] for j in range(1, L + 1) if k - j >= 0]
            PHI.append(np.concatenate(ctx))
    return map(np.array, (Xk, U, D, PHI))

tr = load("train"); va = load("val")
Xtr, Utr, Dtr, Ptr = samples(tr)
Xva, Uva, Dva, Pva = samples(va)

def lin(A, Y):
    th, *_ = np.linalg.lstsq(A, Y, rcond=None); return th

An = np.hstack([Utr, Xtr, np.ones((len(Utr), 1))]); thn = lin(An, Dtr)
thn_J = thn[:Utr.shape[1]].T; thn_W = thn[Utr.shape[1]:Utr.shape[1]+Xtr.shape[1]].T; thn_b = thn[-1]
Ac = np.hstack([Utr, Xtr, Ptr, np.ones((len(Utr), 1))]); thc = lin(Ac, Dtr)
thc_J = thc[:Utr.shape[1]].T; thc_Wx = thc[Utr.shape[1]:Utr.shape[1]+Xtr.shape[1]].T
thc_Wp = thc[Utr.shape[1]+Xtr.shape[1]:Utr.shape[1]+Xtr.shape[1]+Ptr.shape[1]].T; thc_b = thc[-1]

def pred_noctx(x, u): return thn_J @ u + thn_W @ x + thn_b
def pred_add(x, u, phi): return thc_J @ u + thc_Wx @ x + thc_Wp @ phi + thc_b

d_z = Dtr.shape[1]; d_c = Ptr.shape[1]; r = 3
P_t = torch.tensor(Ptr, dtype=torch.float32); U_t = torch.tensor(Utr, dtype=torch.float32)
X_t = torch.tensor(Xtr, dtype=torch.float32); D_t = torch.tensor(Dtr, dtype=torch.float32)

class Mult(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.g = torch.nn.Sequential(torch.nn.Linear(d_c, 32), torch.nn.Tanh(), torch.nn.Linear(32, r))
        self.U = torch.nn.Parameter(0.01 * torch.randn(d_z, r)); self.V = torch.nn.Parameter(0.01 * torch.randn(d_z, r))
        self.J0 = torch.nn.Parameter(torch.tensor(thc_J, dtype=torch.float32))
        self.W = torch.nn.Parameter(torch.tensor(np.hstack([thc_Wx, thc_Wp]), dtype=torch.float32))
        self.b = torch.nn.Parameter(torch.tensor(thc_b, dtype=torch.float32))
    def forward(self, x, u, phi):
        gg = self.g(phi); Ug = self.U.unsqueeze(0) * gg.unsqueeze(1)
        J = self.J0.unsqueeze(0) + Ug @ self.V.transpose(0, 1)
        d = torch.einsum('nij,nj->ni', J, u)
        feat = torch.cat([x, phi], 1)
        return d + feat @ self.W.transpose(0, 1) + self.b

m = Mult(); opt = torch.optim.Adam(m.parameters(), lr=2e-3)
for it in range(5000):
    opt.zero_grad(); loss = ((m(X_t, U_t, P_t) - D_t) ** 2).mean(); loss.backward(); opt.step()
m.eval()

def pred_mult(x, u, phi):
    with torch.no_grad():
        return m(torch.tensor(x, dtype=torch.float32).unsqueeze(0),
                 torch.tensor(u, dtype=torch.float32).unsqueeze(0),
                 torch.tensor(phi, dtype=torch.float32).unsqueeze(0)).squeeze(0).numpy()

def rollout(pred, trajs, mode):
    errs = {h: [] for h in (1, 5, 10, 20)}
    for xx, uu in trajs:
        for k in range(L, len(xx) - H_MAX):
            xh = xx[k].copy()
            for i in range(1, H_MAX + 1):
                kk = k + i - 1
                phi = np.concatenate([xx[kk - j] for j in range(L)] + [uu[kk - j] for j in range(1, L + 1) if kk - j >= 0])
                dh = pred(xh, uu[kk]) if mode == "noctx" else pred(xh, uu[kk], phi)
                xh = xh + dh
                if i in errs: errs[i].append(np.linalg.norm(xh - xx[k + i]))
    return {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in errs.items()}

res = {}
iv = np.linspace(0, len(Dva) - 1, 400).astype(int)
g1 = np.array([pred_noctx(Xva[i], Uva[i]) for i in iv])
g2 = np.array([pred_add(Xva[i], Uva[i], Pva[i]) for i in iv])
g3 = np.array([pred_mult(Xva[i], Uva[i], Pva[i]) for i in iv])
res["one_step_val_rmse"] = {
    "noctx(u,x)": float(np.sqrt(np.mean((g1 - Dva[iv]) ** 2))),
    "add(u,x,phi)": float(np.sqrt(np.mean((g2 - Dva[iv]) ** 2))),
    "mult_lowrank(u,x,phi)": float(np.sqrt(np.mean((g3 - Dva[iv]) ** 2))),
}
res["rollout_val_rmse"] = {
    "noctx(u,x)": rollout(pred_noctx, va, "noctx"),
    "add(u,x,phi)": rollout(pred_add, va, "add"),
    "mult_lowrank(u,x,phi)": rollout(pred_mult, va, "mult"),
}
res["mult_vs_noctx_pct"] = {str(h): round(100 * (res["rollout_val_rmse"]["noctx(u,x)"][h] - res["rollout_val_rmse"]["mult_lowrank(u,x,phi)"][h]) / res["rollout_val_rmse"]["noctx(u,x)"][h], 1) for h in (1, 5, 10, 20)}
res["add_vs_noctx_pct"] = {str(h): round(100 * (res["rollout_val_rmse"]["noctx(u,x)"][h] - res["rollout_val_rmse"]["add(u,x,phi)"][h]) / res["rollout_val_rmse"]["noctx(u,x)"][h], 1) for h in (1, 5, 10, 20)}
res["mult_vs_add_pct"] = {str(h): round(100 * (res["rollout_val_rmse"]["add(u,x,phi)"][h] - res["rollout_val_rmse"]["mult_lowrank(u,x,phi)"][h]) / res["rollout_val_rmse"]["add(u,x,phi)"][h], 1) for h in (1, 5, 10, 20)}
print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
