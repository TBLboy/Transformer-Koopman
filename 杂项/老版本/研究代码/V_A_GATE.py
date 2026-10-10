from pathlib import Path
import json
import numpy as np

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
P2D = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\V_A_GATE.json")

L = 4  # history length for context

def build(split):
    z = np.load(P2D / f"{split}.npz")
    x = z["x"].astype(float); u = z["u"].astype(float); tid = z["trajectory_id"]
    D, U, PHI, Xc, TID = [], [], [], [], []
    for t in np.unique(tid):
        m = np.where(tid == t)[0]
        if len(m) < L + 3: continue
        xx = x[m]; uu = u[m]
        for k in range(L, len(xx) - 1):
            D.append(xx[k + 1] - xx[k]); U.append(uu[k]); Xc.append(xx[k])
            ctx = [xx[k - j] for j in range(L)] + [uu[k - j] for j in range(1, L + 1) if k - j >= 0]
            PHI.append(np.concatenate(ctx)); TID.append(t)
    return np.array(PHI), np.array(U), np.array(D), np.array(Xc), np.array(TID), x, u, tid

def fit_lin(A, Y):
    th, *_ = np.linalg.lstsq(A, Y, rcond=None)
    return th

def rollout_rmse(pred_fn, Xc, U, PHI, x_list, tid_list, H):
    # group by trajectory, build index
    return None

def eval_rollout(pred_fn, samples, H):
    # samples: list of dicts per trajectory with ordered arrays
    pass

# simpler: per-trajectory ordered arrays
def per_traj(split):
    z = np.load(P2D / f"{split}.npz")
    x = z["x"].astype(float); u = z["u"].astype(float); tid = z["trajectory_id"]
    trajs = []
    for t in np.unique(tid):
        m = np.where(tid == t)[0]
        xx = x[m]; uu = u[m]
        if len(xx) < L + H_MAX + 2: continue
        trajs.append((xx, uu))
    return trajs

H_MAX = 20

def rollout_error(pred_d, trajs):
    errs = {h: [] for h in (1, 5, 10, 20)}
    for xx, uu in trajs:
        for k in range(L, len(xx) - H_MAX):
            xh = xx[k].copy()
            for i in range(1, H_MAX + 1):
                ctx = np.concatenate([xh - xx[k]] if False else
                                     ([xx[k + i - 1 - j] for j in range(L)] +
                                      [uu[k + i - 1 - j] for j in range(1, L + 1) if k + i - 1 - j >= 0]))
                dh = pred_d(ctx, uu[k + i - 1])
                xh = xh + dh
                if i in errs:
                    errs[i].append(np.linalg.norm(xh - xx[k + i]))
    return {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in errs.items()}

tr = build("train"); va = build("val")
PHIt, Ut, Dt = tr[0], tr[1], tr[2]
PHIv, Uv, Dv = va[0], va[1], va[2]

# --- FIXED: d = J0 u + b0 ---
Af = np.hstack([Ut, np.ones((len(Ut), 1))]); thf = fit_lin(Af, Dt)
J0, b0 = thf[:-1].T, thf[-1]
def pred_fixed(ctx, u): return J0 @ u + b0

# --- CTX-LINEAR: d = J0 u + b0 + W ctx ---
Ac = np.hstack([Ut, np.ones((len(Ut), 1)), PHIt]); thc = fit_lin(Ac, Dt)
Wc = thc[3:].T
def pred_ctxlin(ctx, u): return J0 @ u + b0 + Wc @ ctx

# --- CTX-LOWRANK (torch): d = (J0 + U diag(g(ctx)) V^T) u + b0 ---
import torch
torch.manual_seed(0)
d_z, d_c = Dt.shape[1], PHIt.shape[1]
r = 3
Xc_t = torch.tensor(PHIt, dtype=torch.float32); U_t = torch.tensor(Ut, dtype=torch.float32)
D_t = torch.tensor(Dt, dtype=torch.float32)
Xc_v = torch.tensor(PHIv, dtype=torch.float32); U_v = torch.tensor(Uv, dtype=torch.float32)
J0t = torch.tensor(J0, dtype=torch.float32); b0t = torch.tensor(b0, dtype=torch.float32)

class Mod(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.g = torch.nn.Sequential(torch.nn.Linear(d_c, 32), torch.nn.Tanh(), torch.nn.Linear(32, r))
        self.U = torch.nn.Parameter(0.01 * torch.randn(d_z, r))
        self.V = torch.nn.Parameter(0.01 * torch.randn(d_z, r))
    def J(self, ctx):
        gg = self.g(ctx)                    # (N,r)
        dA = self.U @ torch.diag_embed(gg) @ self.V.transpose(0, 1) if False else None
        # avoid diag_embed; compute (U * g) @ V^T
        Ug = self.U.unsqueeze(0) * gg.unsqueeze(1)   # (N,dz,r)
        dA = Ug @ self.V.transpose(0, 1)             # (N,dz,dz)
        return J0t.unsqueeze(0) + dA
    def forward(self, ctx, u):
        J = self.J(ctx)
        return torch.einsum('nij,nj->ni', J, u) + b0t

m = Mod(); opt = torch.optim.Adam(m.parameters(), lr=2e-3)
for it in range(4000):
    opt.zero_grad()
    pred = m(Xc_t, U_t)
    loss = ((pred - D_t) ** 2).mean()
    loss.backward(); opt.step()
m.eval()
with torch.no_grad():
    def pred_lr(ctx, u):
        c = torch.tensor(ctx, dtype=torch.float32).unsqueeze(0)
        uu = torch.tensor(u, dtype=torch.float32).unsqueeze(0)
        return m(c, uu).squeeze(0).detach().numpy()

# --- CTX-kNN (local linear, full context) ---
from scipy.spatial import cKDTree
tree = cKDTree(PHIt); kk = 200
def pred_knn(ctx, u):
    _, nb = tree.query(ctx, k=kk)
    A = np.hstack([Ut[nb], np.ones((kk, 1))])
    th, *_ = np.linalg.lstsq(A, Dt[nb], rcond=None)
    return th[:-1].T @ u + th[-1]

trajs_val = per_traj("val")
oneshot = {}
for name, fn in (("fixed", pred_fixed), ("ctxlin", pred_ctxlin), ("ctx_lowrank", pred_lr), ("ctx_knn", pred_knn)):
    # one-step val rmse
    pv = np.array([fn(PHIv[i], Uv[i]) for i in range(0, len(PHIv), 20)])
    dv = Dv[::20]
    oneshot[name] = float(np.sqrt(np.mean((pv - dv) ** 2)))
    globals()["_" + name] = fn

res = {"one_step_val_rmse": oneshot}
res["rollout_val_rmse"] = {}
for name in ("fixed", "ctxlin", "ctx_lowrank", "ctx_knn"):
    res["rollout_val_rmse"][name] = rollout_error(globals()["_" + name], trajs_val)

print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
