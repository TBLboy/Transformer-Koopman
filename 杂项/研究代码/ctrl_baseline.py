from pathlib import Path
import json
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
P1D = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
P2D = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\ctrl_baseline.json")

def build_P2(L=3):
    z = np.load(P2D / "train.npz")
    x = z["x"].astype(float); u = z["u"].astype(float); tid = z["trajectory_id"]
    D, U, PHI = [], [], []
    for t in np.unique(tid):
        m = np.where(tid == t)[0]
        if len(m) < L + 2: continue
        xx = x[m]; uu = u[m]
        for k in range(L, len(xx) - 1):
            D.append(xx[k + 1] - xx[k]); U.append(uu[k])
            ctx = [xx[k - j] for j in range(L)] + [uu[k - j] for j in range(1, L + 1) if k - j >= 0]
            PHI.append(np.concatenate(ctx))
    return np.array(PHI), np.array(U), np.array(D)

def build_P1():
    z = np.load(P1D / "train.npz")
    x = z["x"].astype(float); u = z["u"].astype(float); t = z["t"].astype(float); tid = z["trajectory_id"]
    D, U, PHI = [], [], []
    for tt in np.unique(tid):
        m = np.where(tid == tt)[0]
        if len(m) < 5: continue
        tt_v = t[m]; xx = x[m]; uu = u[m]
        o = np.argsort(tt_v); tt_v = tt_v[o]; xx = xx[o]; uu = uu[o]
        dt = np.diff(tt_v); pos = dt[dt > 0]
        if len(pos) == 0: continue
        dt = np.where(dt <= 0, np.median(pos), dt)
        acc = (xx[1:, 1:6:2] - xx[:-1, 1:6:2]) / dt[:, None]
        D.append(acc); U.append(uu[:-1]); PHI.append(np.hstack([xx[:-1, 0:6:2], xx[:-1, 1:6:2]]))
    return np.concatenate(PHI), np.concatenate(U), np.concatenate(D)

def run(name, PHI, U, D, epochs=3000, h=64):
    np.random.seed(0); torch.manual_seed(0)
    ctr = PHI.mean(0); csc = PHI.std(0) + 1e-8
    um = U.mean(0); us = U.std(0) + 1e-8; dscale = D.std(0) + 1e-8
    Pc = torch.tensor((PHI - ctr) / csc, dtype=torch.float32)
    Uc = torch.tensor((U - um) / us, dtype=torch.float32)
    Dc = torch.tensor(D / dscale, dtype=torch.float32)
    n = len(Pc); perm = torch.randperm(n); ntr = int(0.85 * n); tri, vai = perm[:ntr], perm[ntr:]
    du = U.shape[1]

    class Pot(nn.Module):
        def __init__(s):
            super().__init__(); s.f = nn.Sequential(nn.Linear(Pc.shape[1] + du, h), nn.Tanh(),
                                                    nn.Linear(h, h), nn.Tanh(), nn.Linear(h, 1))
        def forward(s, c, u): return s.f(torch.cat([c, u], 1)).squeeze(-1)
    class Vec(nn.Module):
        def __init__(s):
            super().__init__(); s.f = nn.Sequential(nn.Linear(Pc.shape[1] + du, h), nn.Tanh(),
                                                    nn.Linear(h, h), nn.Tanh(), nn.Linear(h, du))
        def forward(s, c, u): return s.f(torch.cat([c, u], 1))
    vec = Vec(); optv = torch.optim.Adam(vec.parameters(), lr=2e-3)
    for _ in range(epochs):
        optv.zero_grad(); F.mse_loss(vec(Pc[tri], Uc[tri]), Dc[tri]).backward(); optv.step()
    with torch.no_grad():
        rmse_vec = float(torch.sqrt(F.mse_loss(vec(Pc[vai], Uc[vai]), Dc[vai])))

    # context-only baseline: does u add predictive power?
    class VecC(nn.Module):
        def __init__(s):
            super().__init__(); s.f = nn.Sequential(nn.Linear(Pc.shape[1], h), nn.Tanh(),
                                                    nn.Linear(h, h), nn.Tanh(), nn.Linear(h, du))
        def forward(s, c): return s.f(c)
    vecc = VecC(); optc = torch.optim.Adam(vecc.parameters(), lr=2e-3)
    for _ in range(epochs):
        optc.zero_grad(); F.mse_loss(vecc(Pc[tri]), Dc[tri]).backward(); optc.step()
    with torch.no_grad():
        rmse_ctx_only = float(torch.sqrt(F.mse_loss(vecc(Pc[vai]), Dc[vai])))

    pot = Pot(); optp = torch.optim.Adam(pot.parameters(), lr=2e-3)
    for _ in range(epochs):
        optp.zero_grad()
        c = Pc[tri].clone().requires_grad_(True); u = Uc[tri].clone().requires_grad_(True)
        g = torch.autograd.grad(pot(c, u).sum(), u, create_graph=True)[0]
        F.mse_loss(g, Dc[tri]).backward(); optp.step()

    def grad_u(c, u, graph=False):
        return torch.autograd.grad(pot(c, u).sum(), u, create_graph=graph, retain_graph=True)[0]

    # validation forward rmse (potential)
    cv = Pc[vai]; uv = Uc[vai].clone().requires_grad_(True)
    with torch.no_grad():
        pass
    gv = grad_u(cv, uv)
    rmse_pot = float(torch.sqrt(F.mse_loss(gv, Dc[vai])))

    # Gauss-Newton inverse replay: solve grad_u Phi(c,u)=d_target
    dtar = Dc[vai]; ureal = Uc[vai]
    u = torch.zeros_like(ureal).requires_grad_(True)
    for _ in range(25):
        g = grad_u(cv, u, graph=True)
        rows = []
        for i in range(du):
            gi = g[:, i].sum()
            rows.append(torch.autograd.grad(gi, u, retain_graph=True)[0])
        J = torch.stack(rows, dim=1)  # (N, du_out, du_in)
        r = (g - dtar).detach()
        Jd = J.detach() + 1e-4 * torch.eye(du)
        step = torch.linalg.solve(Jd, r.unsqueeze(-1)).squeeze(-1)
        u = (u - step).detach().requires_grad_(True)
    gfin = grad_u(cv, u)
    # self-consistency at TRUE u, and model u-Jacobian at true u
    uT = ureal.clone().requires_grad_(True)
    gT = grad_u(cv, uT, graph=True)
    rowsT = []
    for i in range(du):
        rowsT.append(torch.autograd.grad(gT[:, i].sum(), uT, retain_graph=True)[0])
    JT = torch.stack(rowsT, dim=1).detach()  # (N, du_out, du_in)
    sv = torch.linalg.svdvals(JT)  # (N, min)
    with torch.no_grad():
        err = u - ureal
        med = float(err.abs().median())
        rel = float(err.norm(dim=1).median() / ureal.norm(dim=1).median())
        resid = float((gfin - dtar).norm(dim=1).median())
        resid_true = float((gT.detach() - dtar).norm(dim=1).median())
        sv_min_med = float(sv[:, -1].median()); sv_max_med = float(sv[:, 0].median())
        cond_med = float((sv[:, 0] / (sv[:, -1] + 1e-12)).median())
    return {"n": int(n), "val_rmse_unrestricted_vec": rmse_vec, "val_rmse_context_only": rmse_ctx_only,
            "val_rmse_potential": rmse_pot,
            "inverse_replay_median_abs_err": med, "inverse_replay_median_rel_err": rel,
            "inverse_replay_median_residual": resid,
            "model_residual_at_true_u": resid_true,
            "model_sv_min_at_true_u": sv_min_med, "model_sv_max_at_true_u": sv_max_med,
            "model_cond_at_true_u": cond_med}

res = {}
PHI1, U1, D1 = build_P1(); res["P1"] = run("P1", PHI1, U1, D1)
PHI2, U2, D2 = build_P2(); res["P2"] = run("P2", PHI2, U2, D2)
print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
