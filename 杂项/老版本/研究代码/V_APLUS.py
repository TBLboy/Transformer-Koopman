from pathlib import Path
import json
import numpy as np
import torch

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
P2D = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\V_APLUS.json")
L = 4; H_MAX = 20

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
dx, du, dc = Xtr.shape[1], Utr.shape[1], Ptr.shape[1]; r = 3

def lin(A, Y):
    th, *_ = np.linalg.lstsq(A, Y, rcond=None); return th

# linear warm starts
th_n = lin(np.hstack([Utr, Xtr, np.ones((len(Utr), 1))]), Dtr)          # noctx
th_b = lin(np.hstack([Utr, Xtr, Ptr, np.ones((len(Utr), 1))]), Dtr)
Wx_n = th_n[du:du+dx].T; Wu_n = th_n[:du].T; b_n = th_n[-1]
Wx_b = th_b[du:du+dx].T; Wu_b = th_b[:du].T; Wp_b = th_b[du+dx:du+dx+dc].T; b_b = th_b[-1]

tX = torch.tensor(Xtr, dtype=torch.float32); tU = torch.tensor(Utr, dtype=torch.float32)
tP = torch.tensor(Ptr, dtype=torch.float32); tD = torch.tensor(Dtr, dtype=torch.float32)

class Model(torch.nn.Module):
    def __init__(self, mode):
        super().__init__(); self.mode = mode
        self.Wx = torch.nn.Parameter(torch.tensor(Wx_b, dtype=torch.float32))
        self.Wu = torch.nn.Parameter(torch.tensor(Wu_b, dtype=torch.float32))
        self.Wp = torch.nn.Parameter(torch.tensor(Wp_b, dtype=torch.float32))
        self.b = torch.nn.Parameter(torch.tensor(b_b, dtype=torch.float32))
        self.A0 = torch.nn.Parameter(self.Wx.detach().clone())
        self.B0 = torch.nn.Parameter(self.Wu.detach().clone())
        if mode in ("A", "AB"):
            self.ga = torch.nn.Sequential(torch.nn.Linear(dc, 32), torch.nn.Tanh(), torch.nn.Linear(32, r))
            self.Ua = torch.nn.Parameter(0.01*torch.randn(dx, r)); self.Va = torch.nn.Parameter(0.01*torch.randn(dx, r))
        if mode in ("B", "AB"):
            self.gb = torch.nn.Sequential(torch.nn.Linear(dc, 32), torch.nn.Tanh(), torch.nn.Linear(32, r))
            self.Ub = torch.nn.Parameter(0.01*torch.randn(du, r)); self.Vb = torch.nn.Parameter(0.01*torch.randn(du, r))
    def forward(self, x, u, phi):
        d = x @ self.Wx.transpose(0, 1) + u @ self.Wu.transpose(0, 1) + phi @ self.Wp.transpose(0, 1) + self.b
        if self.mode == "noctx":
            return d
        if self.mode in ("B", "AB"):
            g = self.gb(phi); Ug = self.Ub.unsqueeze(0)*g.unsqueeze(1)
            B = self.B0.unsqueeze(0) + Ug @ self.Vb.transpose(0, 1)
            d = d + torch.einsum('nij,nj->ni', B, u) - u @ self.B0.transpose(0, 1)
        if self.mode in ("A", "AB"):
            g = self.ga(phi); Ug = self.Ua.unsqueeze(0)*g.unsqueeze(1)
            A = self.A0.unsqueeze(0) + Ug @ self.Va.transpose(0, 1)
            d = d + torch.einsum('nij,nj->ni', A, x) - x @ self.A0.transpose(0, 1)
        return d

def train(mode, iters=5000):
    torch.manual_seed(0)
    m = Model(mode); opt = torch.optim.Adam(m.parameters(), lr=2e-3)
    for _ in range(iters):
        opt.zero_grad(); ((m(tX, tU, tP) - tD)**2).mean().backward(); opt.step()
    m.eval(); return m

def rollout(m, trajs):
    errs = {h: [] for h in (1, 5, 10, 20)}
    for xx, uu in trajs:
        for k in range(L, len(xx) - H_MAX):
            buf = [xx[k - j] for j in range(L)][::-1] + [xx[k].copy()]
            xh = xx[k].copy()
            for i in range(1, H_MAX + 1):
                kk = k + i - 1
                past = buf[-(L + 1):-1][::-1]
                phi = np.concatenate(past + [uu[kk - j] for j in range(1, L + 1) if kk - j >= 0])
                with torch.no_grad():
                    dh = m(torch.tensor(xh, dtype=torch.float32).unsqueeze(0), torch.tensor(uu[kk], dtype=torch.float32).unsqueeze(0),
                           torch.tensor(phi, dtype=torch.float32).unsqueeze(0)).squeeze(0).numpy()
                xh = xh + dh; buf.append(xh)
                if i in errs: errs[i].append(np.linalg.norm(xh - xx[k + i]))
    return {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in errs.items()}

res = {"ablation_rollout_val_rmse": {}}
for mode in ("noctx", "A", "B", "AB"):
    m = train(mode)
    res["ablation_rollout_val_rmse"][mode] = rollout(m, va)
b = res["ablation_rollout_val_rmse"]
res["vs_noctx_pct"] = {mode: {str(h): round(100*(b["noctx"][h]-b[mode][h])/b["noctx"][h], 1) for h in (1,5,10,20)} for mode in ("A","B","AB")}
res["B_vs_AB_pct"] = {str(h): round(100*(b["B"][h]-b["AB"][h])/b["B"][h], 1) for h in (1,5,10,20)}

# ---- matched-state history test (on train+val) ----
Xa = np.vstack([Xtr, Xva]); Ua = np.vstack([Utr, Uva]); Da = np.vstack([Dtr, Dva]); Pa = np.vstack([Ptr, Pva])
rng = np.random.default_rng(0); N = len(Xa)
i = rng.integers(0, N, 200000); j = rng.integers(0, N, 200000)
m_ = i != j
dxij = np.linalg.norm(Xa[i]-Xa[j], axis=1); duij = np.linalg.norm(Ua[i]-Ua[j], axis=1)
dpij = np.linalg.norm(Pa[i]-Pa[j], axis=1); ddij = np.linalg.norm(Da[i]-Da[j], axis=1)
near = m_ & (dxij < np.quantile(dxij[m_], 0.02)) & (duij < np.quantile(duij[m_], 0.05))
sim_hist = near & (dpij < np.quantile(dpij[near], 0.25))
dif_hist = near & (dpij > np.quantile(dpij[near], 0.75))
res["matched_state_history_test"] = {
    "n_near_pairs": int(near.sum()),
    "mean_next_response_diff__similar_history": float(ddij[sim_hist].mean()),
    "mean_next_response_diff__different_history": float(ddij[dif_hist].mean()),
    "ratio": float(ddij[dif_hist].mean() / ddij[sim_hist].mean()),
}
print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
