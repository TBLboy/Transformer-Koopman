"""Full-latent-pipeline structure gate for A+ (RSHC-TK) + falsification tests.

Trains latent Koopman models with fixed / A-only / B-only / AB low-rank context
modulation on P2 data; evaluates multi-step rollout RMSE (H=1/5/10/20) on
val/test; then runs modulation-off and history-nullification falsification.
"""
import os, sys, json, argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

REPO = r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码"
sys.path.insert(0, os.path.join(REPO, "src"))
from patchtst_koopman.models.patchtst_encoder import PatchTSTEncoder
from patchtst_koopman.models.linear_decoder import LinearDecoder
from patchtst_koopman.utils.config_loader import load_config

DEV = "cuda" if torch.cuda.is_available() else "cpu"
OUT = r"C:\Users\12187\AppData\Local\Temp\opencode\gate_result.json"
STATE = r"C:\Users\12187\AppData\Local\Temp\opencode\gate_states"
H_EVAL = [1, 5, 10, 20]
H_MAX = 20


def build_split(data_dir, split, cfg, norm=None):
    d = np.load(os.path.join(data_dir, f"{split}.npz"))
    x = d["x"].astype(np.float64); u = d["u"].astype(np.float64); tid = d["trajectory_id"]
    if norm is None:
        norm = {"x_mean": x.mean(0), "x_std": x.std(0) + 1e-8,
                "u_mean": u.mean(0), "u_std": u.std(0) + 1e-8}
    x = (x - norm["x_mean"]) / norm["x_std"]
    u = (u - norm["u_mean"]) / norm["u_std"]
    P = cfg["encoder"]["history_length"]
    XH, UH, UT, XN = [], [], [], []
    for t in np.unique(tid):
        idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
        for i in range(P - 1, len(xx) - H_MAX - 1):
            XH.append(xx[i - P + 1:i + 1]); UH.append(uu[i - P + 1:i])
            UT.append(uu[i]); XN.append(xx[i + 1])
    return (torch.tensor(np.array(XH), dtype=torch.float32), torch.tensor(np.array(UH), dtype=torch.float32),
            torch.tensor(np.array(UT), dtype=torch.float32), torch.tensor(np.array(XN), dtype=torch.float32), norm)


class CtxKoopman(nn.Module):
    def __init__(self, cfg, mode, r=3, c_dim=16, c_hidden=64):
        super().__init__()
        self.mode = mode; self._ablate = False
        self.encoder = PatchTSTEncoder(cfg); self.decoder = LinearDecoder(cfg)
        self.d = cfg["encoder"]["latent_dim"]; self.m = cfg["data"]["control_dim"]; self.n = cfg["data"]["state_dim"]
        P = cfg["encoder"]["history_length"]; in_ctx = P * self.n + (P - 1) * self.m
        self.ctx = nn.Sequential(nn.Linear(in_ctx, c_hidden), nn.Tanh(), nn.Linear(c_hidden, c_dim), nn.Tanh())
        self.A0 = nn.Parameter(torch.eye(self.d) + 0.01 * torch.randn(self.d, self.d))
        self.B0 = nn.Parameter(0.1 * torch.randn(self.d, self.m))
        self.r = r
        if mode in ("A", "AB"):
            self.ga = nn.Linear(c_dim, r); self.Ua = nn.Parameter(0.01 * torch.randn(self.d, r)); self.Va = nn.Parameter(0.01 * torch.randn(self.d, r))
        if mode in ("B", "AB"):
            self.gb = nn.Linear(c_dim, r); self.Ub = nn.Parameter(0.01 * torch.randn(self.d, r)); self.Vb = nn.Parameter(0.01 * torch.randn(self.m, r))

    def get_AB(self, xh, uh):
        B = xh.shape[0]
        A = self.A0.unsqueeze(0).expand(B, -1, -1).contiguous()
        Bm = self.B0.unsqueeze(0).expand(B, -1, -1).contiguous()
        if self.mode == "fixed" or self._ablate:
            return A, Bm
        c = self.ctx(torch.cat([xh.reshape(B, -1), uh.reshape(B, -1)], dim=1))
        if self.mode in ("A", "AB"):
            g = self.ga(c); Ug = self.Ua.unsqueeze(0) * g.unsqueeze(1); A = A + Ug @ self.Va.transpose(0, 1)
        if self.mode in ("B", "AB"):
            g = self.gb(c); Ug = self.Ub.unsqueeze(0) * g.unsqueeze(1); Bm = Bm + Ug @ self.Vb.transpose(0, 1)
        return A, Bm

    def forward(self, xh, uh, ut):
        z = self.encoder(xh); A, Bm = self.get_AB(xh, uh)
        z_next = torch.einsum('nij,nj->ni', A, z) + torch.einsum('nij,nj->ni', Bm, ut)
        return self.decoder(z_next)


def train_model(mode, cfg, data, epochs=100, lr=1e-3, init_state=None, seed=0, r=3):
    XH, UH, UT, XN = data
    torch.manual_seed(seed)
    model = CtxKoopman(cfg, mode, r=r).to(DEV)
    if init_state is not None:
        model.load_state_dict(init_state, strict=False)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    n = len(XH); bs = 256; best = (1e9, None)
    for ep in range(epochs):
        model.train(); perm = torch.randperm(n)
        for s in range(0, n, bs):
            b = perm[s:s + bs]; opt.zero_grad()
            loss = F.mse_loss(model(XH[b].to(DEV), UH[b].to(DEV), UT[b].to(DEV)), XN[b].to(DEV))
            loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            vl = F.mse_loss(model(XH.to(DEV), UH.to(DEV), UT.to(DEV)), XN.to(DEV)).item()
        if vl < best[0]:
            best = (vl, {k: v.clone() for k, v in model.state_dict().items()})
    model.load_state_dict(best[1])
    return model, best[0]


def eval_rollout(model, cfg, data_dir, split, norm, uh_zero=False, stride=8):
    d = np.load(os.path.join(data_dir, f"{split}.npz"))
    x = (d["x"].astype(np.float64) - norm["x_mean"]) / norm["x_std"]
    u = (d["u"].astype(np.float64) - norm["u_mean"]) / norm["u_std"]
    tid = d["trajectory_id"]; P = cfg["encoder"]["history_length"]; m = cfg["data"]["control_dim"]
    errs = {h: [] for h in H_EVAL}
    model.eval()
    with torch.no_grad():
        for t in np.unique(tid):
            idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
            for k in range(P - 1, len(xx) - H_MAX - 1, stride):
                xh = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                if uh_zero:
                    uh = torch.zeros(1, P - 1, m, dtype=torch.float32).to(DEV)
                else:
                    uh = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
                for h in range(1, H_MAX + 1):
                    ut = torch.tensor(uu[k + h - 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                    xn = model(xh, uh, ut)
                    xh = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
                    uh = torch.cat([uh[:, 1:, :], (torch.zeros_like(ut) if uh_zero else ut).unsqueeze(1)], dim=1)
                    if h in errs:
                        gt = torch.tensor(xx[k + h], dtype=torch.float32).to(DEV)
                        errs[h].append(torch.linalg.norm(xn.squeeze(0) - gt).item())
    return {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in errs.items()}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--modes", type=str, default="fixed,A,B,AB")
    ap.add_argument("--tag", type=str, default="")
    args = ap.parse_args()
    cfg = load_config(os.path.join(REPO, "configs", "platform2.yaml"))
    data_dir = os.path.abspath(os.path.join(REPO, cfg["data"]["data_dir"]))
    os.makedirs(STATE, exist_ok=True)
    print("data_dir:", data_dir, "device:", DEV, "seed:", args.seed)
    trXH, trUH, trUT, trXN, norm = build_split(data_dir, "train", cfg)
    print(f"train {trXH.shape}")

    modes = args.modes.split(",")
    res = {"config": {"r": 3, "epochs": args.epochs, "seed": args.seed, "P": cfg["encoder"]["history_length"], "d": cfg["encoder"]["latent_dim"]}, "modes": {}}
    fixed, fixed_val = train_model("fixed", cfg, (trXH, trUH, trUT, trXN), epochs=args.epochs, seed=args.seed)
    init = {k: v.clone() for k, v in fixed.state_dict().items()}
    torch.save(init, os.path.join(STATE, f"fixed{args.tag}.pt"))
    for mode in modes:
        if mode == "fixed":
            m, v = fixed, fixed_val
        else:
            m, v = train_model(mode, cfg, (trXH, trUH, trUT, trXN), epochs=args.epochs, lr=5e-4, init_state=init, seed=args.seed)
        torch.save({k: t.clone() for k, t in m.state_dict().items()}, os.path.join(STATE, f"{mode}{args.tag}.pt"))
        rv = eval_rollout(m, cfg, data_dir, "val", norm)
        rt = eval_rollout(m, cfg, data_dir, "test", norm)
        entry = {"val_1step_mse": v, "val_rollout": rv, "test_rollout": rt,
                 "params": sum(p.numel() for p in m.parameters())}
        if mode in ("A", "AB"):
            m._ablate = True
            entry["val_rollout_modOFF"] = eval_rollout(m, cfg, data_dir, "val", norm)
            m._ablate = False
            entry["val_rollout_uhZERO"] = eval_rollout(m, cfg, data_dir, "val", norm, uh_zero=True)
        res["modes"][mode] = entry
        print(mode, "val:", {k: round(x, 4) for k, x in rv.items()})
        if mode in ("A", "AB"):
            print("   modOFF:", {k: round(x, 4) for k, x in entry["val_rollout_modOFF"].items()},
                  " uhZERO:", {k: round(x, 4) for k, x in entry["val_rollout_uhZERO"].items()})
    base = res["modes"]["fixed"]["val_rollout"]
    res["val_improve_pct_vs_fixed"] = {mode: {str(h): round(100 * (base[h] - res["modes"][mode]["val_rollout"][h]) / base[h], 1) for h in H_EVAL} for mode in modes if mode != "fixed"}
    outp = OUT if not args.tag else OUT.replace(".json", f"{args.tag}.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(json.dumps(res["val_improve_pct_vs_fixed"], indent=2))


if __name__ == "__main__":
    main()
