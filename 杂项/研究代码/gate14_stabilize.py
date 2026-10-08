"""Gate-14: stabilization retraining of A-only (budgeted low-rank + rho<1 + open-loop training).

Tests whether open-loop propagation (F_prop / R_prop) recovers once the latent
is bounded (||dA||<=delta_A) and stabilized (rho(A(c))<=rho_max<1), optionally
with an open-loop (scheduled propagation) training objective.
"""
import sys, os, json, argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, r"C:\Users\12187\AppData\Local\Temp\opencode")
from gate_context_koopman import CtxKoopman, build_split, eval_rollout, H_EVAL, H_MAX, REPO
from patchtst_koopman.models.patchtst_encoder import PatchTSTEncoder
from patchtst_koopman.models.linear_decoder import LinearDecoder
from patchtst_koopman.utils.config_loader import load_config

DEV = "cuda" if torch.cuda.is_available() else "cpu"
STATE = r"C:\Users\12187\AppData\Local\Temp\opencode\gate_states"
OUT = r"C:\Users\12187\AppData\Local\Temp\opencode\gate14_result.json"


class BudgetedCtxKoopman(nn.Module):
    def __init__(self, cfg, r=2, delta_A=0.07, c_dim=16, c_hidden=64):
        super().__init__()
        self.r = r; self.delta_A = delta_A
        self.encoder = PatchTSTEncoder(cfg); self.decoder = LinearDecoder(cfg)
        self.d = cfg["encoder"]["latent_dim"]; self.m = cfg["data"]["control_dim"]; self.n = cfg["data"]["state_dim"]
        P = cfg["encoder"]["history_length"]; in_ctx = P * self.n + (P - 1) * self.m
        self.ctx = nn.Sequential(nn.Linear(in_ctx, c_hidden), nn.Tanh(), nn.Linear(c_hidden, c_dim), nn.Tanh())
        self.A0 = nn.Parameter(torch.eye(self.d) + 0.01 * torch.randn(self.d, self.d))
        self.B0 = nn.Parameter(0.1 * torch.randn(self.d, self.m))
        self.Uraw = nn.Parameter(0.1 * torch.randn(self.d, r)); self.Vraw = nn.Parameter(0.1 * torch.randn(self.d, r))
        self.s = nn.Parameter(torch.zeros(r)); self.g = nn.Linear(c_dim, r)

    def get_AB(self, xh, uh):
        B = xh.shape[0]
        c = self.ctx(torch.cat([xh.reshape(B, -1), uh.reshape(B, -1)], dim=1))
        pi = torch.softmax(self.s, 0)
        a = self.delta_A * pi.unsqueeze(0) * torch.tanh(self.g(c))          # (B,r), |a_i|<=delta*pi_i
        U = self.Uraw / (self.Uraw.norm(dim=0, keepdim=True) + 1e-8)
        V = self.Vraw / (self.Vraw.norm(dim=0, keepdim=True) + 1e-8)
        dA = torch.einsum('ir,br,jr->bij', U, a, V)                          # (B,d,d), ||dA||_2<=delta_A
        A = self.A0.unsqueeze(0) + dA
        Bm = self.B0.unsqueeze(0).expand(B, -1, -1)
        return A, Bm

    def forward(self, xh, uh, ut):
        z = self.encoder(xh); A, Bm = self.get_AB(xh, uh)
        z2 = torch.einsum('nij,nj->ni', A, z) + torch.einsum('nij,nj->ni', Bm, ut)
        return self.decoder(z2)

    def rho_penalty(self, A, rho_max):
        ev = torch.linalg.eigvals(A)
        rho = ev.abs().max(dim=1).values
        return F.relu(rho - rho_max).pow(2).mean()


def build_seq_split(data_dir, split, cfg, norm, H=20):
    d = np.load(os.path.join(data_dir, f"{split}.npz"))
    x = (d["x"].astype(np.float64) - norm["x_mean"]) / norm["x_std"]
    u = (d["u"].astype(np.float64) - norm["u_mean"]) / norm["u_std"]
    tid = d["trajectory_id"]; P = cfg["encoder"]["history_length"]
    XH0, UH0, UF, XF = [], [], [], []
    for t in np.unique(tid):
        idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
        for k in range(P - 1, len(xx) - H - 1):
            XH0.append(xx[k - P + 1:k + 1]); UH0.append(uu[k - P + 1:k])
            UF.append(uu[k:k + H]); XF.append(xx[k + 1:k + 1 + H])
    T = lambda a: torch.tensor(np.array(a), dtype=torch.float32)
    return T(XH0), T(UH0), T(UF), T(XF)


def openloop_forward(model, xh0, uh0, UF):
    z = model.encoder(xh0); xh = xh0.clone(); uh = uh0.clone(); preds = []
    for h in range(UF.shape[1]):
        ut = UF[:, h, :]
        A, Bm = model.get_AB(xh, uh)
        z = torch.einsum('bij,bj->bi', A, z) + torch.einsum('bij,bj->bi', Bm, ut)
        xn = model.decoder(z); preds.append(xn)
        xh = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
        uh = torch.cat([uh[:, 1:, :], ut.unsqueeze(1)], dim=1)
    return torch.stack(preds, 1)


def train(mode, init_state, trXH, trUH, trUT, trXN, seq, epochs=100, lr=5e-4, lam=10.0, rho_max=0.99, bs=256, seed=0, H=20):
    torch.manual_seed(seed)
    model = BudgetedCtxKoopman(CFG).to(DEV)
    if init_state is not None:
        model.load_state_dict(init_state, strict=False)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    XH0, UH0, UF, XF = seq
    n = len(trXH); best = (1e9, None)
    for ep in range(epochs):
        model.train(); perm = torch.randperm(n)
        for s in range(0, n, bs):
            b = perm[s:s + bs]; opt.zero_grad()
            if mode == "one_step":
                pred = model(trXH[b].to(DEV), trUH[b].to(DEV), trUT[b].to(DEV))
                loss = F.mse_loss(pred, trXN[b].to(DEV))
                A, _ = model.get_AB(trXH[b].to(DEV), trUH[b].to(DEV))
            else:  # openloop
                pred = openloop_forward(model, XH0[b].to(DEV), UH0[b].to(DEV), UF[b].to(DEV))
                loss = F.mse_loss(pred, XF[b].to(DEV))
                A, _ = model.get_AB(XH0[b].to(DEV), UH0[b].to(DEV))
            loss = loss + lam * model.rho_penalty(A, rho_max)
            loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            if mode == "one_step":
                vl = F.mse_loss(model(trXH.to(DEV), trUH.to(DEV), trUT.to(DEV)), trXN.to(DEV)).item()
            else:
                vl = F.mse_loss(openloop_forward(model, XH0.to(DEV), UH0.to(DEV), UF.to(DEV)), XF.to(DEV)).item()
        if vl < best[0]:
            best = (vl, {k: v.clone() for k, v in model.state_dict().items()})
    model.load_state_dict(best[1])
    return model, best[0]


def eval_prop(model, split, norm, sched=False, stride=8):
    d = np.load(os.path.join(DATA_DIR, f"{split}.npz"))
    x = (d["x"].astype(np.float64) - norm["x_mean"]) / norm["x_std"]
    u = (d["u"].astype(np.float64) - norm["u_mean"]) / norm["u_std"]
    tid = d["trajectory_id"]; P = CFG["encoder"]["history_length"]; m = CFG["data"]["control_dim"]
    errs = {h: [] for h in H_EVAL}
    with torch.no_grad():
        for t in np.unique(tid):
            idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
            for k in range(P - 1, len(xx) - H_MAX - 1, stride):
                xh0 = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                uh0 = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
                z = model.encoder(xh0)
                if not sched:
                    A_f, B_f = model.get_AB(xh0, uh0)
                xbuf = [xx[j] for j in range(k - P + 1, k + 1)]; ubuf = [uu[j] for j in range(k - P + 1, k)]
                for h in range(1, H_MAX + 1):
                    ut = torch.tensor(uu[k + h - 1], dtype=torch.float32).reshape(1, m).to(DEV)
                    if sched:
                        cx = torch.tensor(np.array(xbuf[-P:]), dtype=torch.float32).unsqueeze(0).to(DEV)
                        cu = torch.tensor(np.array(ubuf[-(P - 1):]), dtype=torch.float32).unsqueeze(0).to(DEV)
                        A, B = model.get_AB(cx, cu)
                    else:
                        A, B = A_f, B_f
                    z = torch.einsum('nij,nj->ni', A, z) + torch.einsum('nij,nj->ni', B, ut)
                    xn = model.decoder(z)
                    xbuf.append(xn[0].cpu().numpy()); ubuf.append(uu[k + h - 1])
                    if h in errs:
                        gt = torch.tensor(xx[k + h], dtype=torch.float32).to(DEV)
                        errs[h].append(torch.linalg.norm(xn.squeeze(0) - gt).item())
    return {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in errs.items()}


def rho_stats(model, split, norm):
    d = np.load(os.path.join(DATA_DIR, f"{split}.npz"))
    x = (d["x"].astype(np.float64) - norm["x_mean"]) / norm["x_std"]
    u = (d["u"].astype(np.float64) - norm["u_mean"]) / norm["u_std"]
    tid = d["trajectory_id"]; P = CFG["encoder"]["history_length"]
    rho, dA = [], []
    with torch.no_grad():
        for t in np.unique(tid):
            idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
            for k in range(P - 1, len(xx) - 1, 4):
                xh = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                uh = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
                A, _ = model.get_AB(xh, uh)
                An = A[0].cpu().numpy()
                rho.append(float(np.max(np.abs(np.linalg.eigvals(An)))))
                if hasattr(model, "A0"):
                    dA.append(float(np.linalg.norm(An - model.A0.detach().cpu().numpy(), 2)))
    return {"rho_median": float(np.median(rho)), "rho_max": float(np.max(rho)),
            "dA_median": float(np.median(dA)) if dA else None, "dA_max": float(np.max(dA)) if dA else None}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--H", type=int, default=20); ap.add_argument("--rho_max", type=float, default=0.99)
    ap.add_argument("--lam", type=float, default=10.0); ap.add_argument("--modes", type=str, default="one_step,openloop")
    ap.add_argument("--tag", type=str, default="")
    args = ap.parse_args()
    CFG = load_config(os.path.join(REPO, "configs", "platform2.yaml"))
    DATA_DIR = os.path.abspath(os.path.join(REPO, CFG["data"]["data_dir"]))
    trXH, trUH, trUT, trXN, NORM = build_split(DATA_DIR, "train", CFG)
    seq_tr = build_seq_split(DATA_DIR, "train", CFG, NORM, args.H)
    print("train", trXH.shape, "seq", seq_tr[0].shape, "device", DEV)
    init = torch.load(os.path.join(STATE, "fixed.pt"), map_location="cpu")

    out = {"config": {"H": args.H, "rho_max": args.rho_max, "lam": args.lam, "epochs": args.epochs, "delta_A": 0.07, "r": 2, "tag": args.tag}, "models": {}}

    # baseline A-only (round-12) for reference
    base = CtxKoopman(CFG, "A", r=2).to(DEV)
    base.load_state_dict(torch.load(os.path.join(STATE, "A_r2.pt"), map_location=DEV)); base.eval()
    out["models"]["A_baseline_r2"] = {
        "R_reencode": eval_rollout(base, CFG, DATA_DIR, "val", NORM),
        "F_prop": eval_prop(base, "val", NORM, sched=False),
        "R_prop": eval_prop(base, "val", NORM, sched=True)}
    print("A_baseline_r2", {k: {hh: round(vv, 4) for hh, vv in v.items()} for k, v in out["models"]["A_baseline_r2"].items()})

    fixedm = CtxKoopman(CFG, "fixed").to(DEV)
    fixedm.load_state_dict(torch.load(os.path.join(STATE, "fixed.pt"), map_location=DEV)); fixedm.eval()
    out["models"]["fixed"] = {"R_reencode": eval_rollout(fixedm, CFG, DATA_DIR, "val", NORM),
                              "F_prop": eval_prop(fixedm, "val", NORM, sched=False)}
    print("fixed", {k: {hh: round(vv, 4) for hh, vv in v.items()} for k, v in out["models"]["fixed"].items()})

    for mode in args.modes.split(","):
        m, v = train(mode, init, trXH, trUH, trUT, trXN, seq_tr, epochs=args.epochs, lam=args.lam, rho_max=args.rho_max)
        tag = f"{mode}_lam{args.lam}_rho{args.rho_max}"
        torch.save({k: t.clone() for k, t in m.state_dict().items()}, os.path.join(STATE, f"A_stab_{tag}.pt"))
        r = {"train_obj": v, "R_reencode": eval_rollout(m, CFG, DATA_DIR, "val", NORM),
             "F_prop": eval_prop(m, "val", NORM, sched=False), "R_prop": eval_prop(m, "val", NORM, sched=True),
             "rho_stats": rho_stats(m, "val", NORM)}
        out["models"][f"A_stab_{tag}"] = r
        print(f"A_stab_{tag}", "rho", r["rho_stats"])
        for kk in ("R_reencode", "F_prop", "R_prop"):
            print("   ", kk, {hh: round(vv, 4) for hh, vv in r[kk].items()})

    if os.path.exists(OUT):
        try:
            old = json.load(open(OUT, encoding="utf-8"))
            if isinstance(old.get("models"), dict):
                merged = dict(old); merged["models"] = {**old["models"], **out["models"]}
                merged["config"] = out["config"]; out = merged
        except Exception:
            pass
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print("saved", OUT)
