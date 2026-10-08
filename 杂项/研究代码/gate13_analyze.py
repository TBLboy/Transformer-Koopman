"""Gate-13A (recontextualized vs frozen), 13C (A-family diagnostics), 13D (conditional shuffle).

Loads the saved A-only / fixed checkpoints from the round-12 structure gate.
"""
import sys, os, json, argparse
import numpy as np
import torch

sys.path.insert(0, r"C:\Users\12187\AppData\Local\Temp\opencode")
from gate_context_koopman import CtxKoopman, build_split, eval_rollout, H_EVAL, H_MAX, REPO
from patchtst_koopman.utils.config_loader import load_config

DEV = "cuda" if torch.cuda.is_available() else "cpu"
STATE = r"C:\Users\12187\AppData\Local\Temp\opencode\gate_states"
OUT = r"C:\Users\12187\AppData\Local\Temp\opencode\gate13_result.json"


def load(mode, tag=""):
    m = CtxKoopman(CFG, mode).to(DEV)
    m.load_state_dict(torch.load(os.path.join(STATE, f"{mode}{tag}.pt"), map_location=DEV))
    m.eval()
    return m


def eval_rollout_frozen(model, split, norm, stride=8):
    d = np.load(os.path.join(DATA_DIR, f"{split}.npz"))
    x = (d["x"].astype(np.float64) - norm["x_mean"]) / norm["x_std"]
    u = (d["u"].astype(np.float64) - norm["u_mean"]) / norm["u_std"]
    tid = d["trajectory_id"]; P = CFG["encoder"]["history_length"]
    errs = {h: [] for h in H_EVAL}
    with torch.no_grad():
        for t in np.unique(tid):
            idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
            for k in range(P - 1, len(xx) - H_MAX - 1, stride):
                xh = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                uh = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
                A_f, B_f = model.get_AB(xh, uh)      # frozen at k
                for h in range(1, H_MAX + 1):
                    ut = torch.tensor(uu[k + h - 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                    z = model.encoder(xh)
                    z2 = torch.einsum('nij,nj->ni', A_f, z) + torch.einsum('nij,nj->ni', B_f, ut)
                    xn = model.decoder(z2)
                    xh = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
                    uh = torch.cat([uh[:, 1:, :], ut.unsqueeze(1)], dim=1)
                    if h in errs:
                        gt = torch.tensor(xx[k + h], dtype=torch.float32).to(DEV)
                        errs[h].append(torch.linalg.norm(xn.squeeze(0) - gt).item())
    return {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in errs.items()}


def eval_rollout_prop(model, split, norm, sched=False, stride=8):
    """MPC-faithful: propagate latent z (no re-encoding). sched=False -> A frozen at k; True -> A recomputed from propagated history."""
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
                xbuf = [xx[j] for j in range(k - P + 1, k + 1)]
                ubuf = [uu[j] for j in range(k - P + 1, k)]
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


def part_13A():
    fixed = load("fixed"); A = load("A")
    res = {}
    for split in ("val", "test"):
        Ef = eval_rollout(fixed, CFG, DATA_DIR, split, NORM)
        ER = eval_rollout(A, CFG, DATA_DIR, split, NORM)
        EF_rec = eval_rollout_frozen(A, split, NORM)
        EF_prop = eval_rollout_prop(A, split, NORM, sched=False)
        ER_prop = eval_rollout_prop(A, split, NORM, sched=True)
        G = lambda E: {str(h): round(100 * (Ef[h] - E[h]) / Ef[h], 1) for h in H_EVAL}
        def eta(E):
            gR = G(ER); gE = G(E)
            return {str(h): (round(gE[str(h)] / gR[str(h)], 3) if abs(gR[str(h)]) > 1e-6 else None) for h in H_EVAL}
        res[split] = {"E_fixed": Ef, "E_R_reencode": ER, "E_F_reencode": EF_rec, "E_F_prop": EF_prop, "E_R_prop": ER_prop,
                      "G_R_reencode": G(ER), "G_F_reencode": G(EF_rec), "G_F_prop": G(EF_prop), "G_R_prop": G(ER_prop),
                      "eta_F_reencode": eta(EF_rec), "eta_F_prop": eta(EF_prop), "eta_R_prop": eta(ER_prop)}
        print(f"[13A {split}] G_R_reenc%={res[split]['G_R_reencode']}  G_F_prop%={res[split]['G_F_prop']}  G_R_prop%={res[split]['G_R_prop']}")
        print(f"          eta_F_prop={res[split]['eta_F_prop']}  eta_R_prop={res[split]['eta_R_prop']}")
    return res


def _A_of(model, xh, uh):
    with torch.no_grad():
        A, _ = model.get_AB(xh, uh)
    return A


def part_13C():
    A = load("A"); A0 = A.A0.detach()
    d = CFG["encoder"]["latent_dim"]; P = CFG["encoder"]["history_length"]
    d2 = np.load(os.path.join(DATA_DIR, "val.npz"))
    x = (d2["x"].astype(np.float64) - NORM["x_mean"]) / NORM["x_std"]
    u = (d2["u"].astype(np.float64) - NORM["u_mean"]) / NORM["u_std"]
    tid = d2["trajectory_id"]
    rho, nA, dA2, dAF, drift, gates = [], [], [], [], [], []
    growth = {str(H): [] for H in (2, 5, 10, 20)}
    corr = {"speed": [], "du": [], "dx": []}
    with torch.no_grad():
        for t in np.unique(tid):
            idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
            Aks, gs, feats = [], [], []
            for k in range(P - 1, len(xx) - 1):
                xh = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                uh = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
                Ak, _ = A.get_AB(xh, uh)
                c = A.ctx(torch.cat([xh.reshape(1, -1), uh.reshape(1, -1)], dim=1))
                gs.append(A.ga(c).squeeze(0).cpu().numpy())
                Aks.append(Ak[0].cpu().numpy())
                feats.append((np.linalg.norm(uu[k + 1] - uu[k]) if k + 1 < len(xx) else 0.0,
                              np.linalg.norm(xx[k + 1] - xx[k]) if k + 1 < len(xx) else 0.0,
                              np.linalg.norm(uu[k] - uu[k - 1]) if k >= 1 else 0.0))
            Aks = np.array(Aks); gs = np.array(gs); feats = np.array(feats)
            for i in range(len(Aks)):
                Ai = Aks[i]
                rho.append(float(np.max(np.abs(np.linalg.eigvals(Ai)))))
                nA.append(float(np.linalg.norm(Ai, 2)))
                D = Ai - A0.cpu().numpy()
                dA2.append(float(np.linalg.norm(D, 2))); dAF.append(float(np.linalg.norm(D, "fro")))
                if i > 0:
                    drift.append(float(np.linalg.norm(Aks[i] - Aks[i - 1], "fro") / (np.linalg.norm(Aks[i - 1], "fro") + 1e-9)))
            gates.append(gs)
            for H in (2, 5, 10, 20):
                for s in range(len(Aks) - H + 1):
                    M = np.eye(d)
                    for j in range(H):
                        M = Aks[s + j] @ M
                    growth[str(H)].append(float(np.linalg.norm(M, 2) ** (1.0 / H)))
            sp = feats[:, 1] / 0.2  # per-step displacement / dt
            corr["speed"].append(np.corrcoef(gs.mean(1), sp)[0, 1])
            corr["du"].append(np.corrcoef(gs.mean(1), feats[:, 0])[0, 1])
            corr["dx"].append(np.corrcoef(gs.mean(1), feats[:, 1])[0, 1])
    q = lambda v, p: float(np.quantile(v, p))
    allg = np.concatenate(gates, 0)
    res = {
        "rho": {"median": q(rho, .5), "q95": q(rho, .95), "q99": q(rho, .99), "max": float(np.max(rho))},
        "normA2": {"median": q(nA, .5), "q95": q(nA, .95), "max": float(np.max(nA))},
        "dA_spec2": {"median": q(dA2, .5), "q95": q(dA2, .95), "q99": q(dA2, .99), "max": float(np.max(dA2))},
        "dA_fro": {"median": q(dAF, .5), "q95": q(dAF, .95), "q99": q(dAF, .99), "max": float(np.max(dAF))},
        "drift_fro_ratio": {"median": q(drift, .5), "q95": q(drift, .95), "max": float(np.max(drift))},
        "A0_norm2": float(np.linalg.norm(A0.cpu().numpy(), 2)), "A0_rho": float(np.max(np.abs(np.linalg.eigvals(A0.cpu().numpy())))),
        "product_growth_gH": {H: {"median": q(v, .5), "q95": q(v, .95), "max": float(np.max(v))} for H, v in growth.items()},
        "gate_modes": {"mean": allg.mean(0).tolist(), "std": allg.std(0).tolist(),
                       "absmean": np.abs(allg).mean(0).tolist(),
                       "frac_active_gt_0.1": (np.abs(allg) > 0.1).mean(0).tolist()},
        "corr_gate_mean_with": {"speed": float(np.nanmean(corr["speed"])), "du": float(np.nanmean(corr["du"])), "dx": float(np.nanmean(corr["dx"]))},
    }
    print("[13C]", json.dumps(res, indent=2))
    return res


def part_13D(eps_u=0.5, stride=4):
    A = load("A")
    XH, UH, UT, XN, _ = build_split(DATA_DIR, "val", CFG, NORM)
    # current state and previous input per sample
    cur = XH[:, -1, :]; prev_u = UH[:, -1, :]
    n = len(XH)
    # nearest neighbor by current state, from a different trajectory: approximate by excluding identical index
    with torch.no_grad():
        cdist = torch.cdist(cur, cur); cdist.fill_diagonal_(float("inf"))
        # u-distance
        udist = torch.cdist(prev_u, prev_u)
        nn = cdist.argmin(1)
        ok = udist[torch.arange(n), nn] <= eps_u
        idx = torch.arange(n)[ok]
        jdx = nn[ok]
        # cap for speed
        sel = torch.randperm(len(idx))[:600]
        i2, j2 = idx[sel], jdx[sel]
        A_orig, _ = A.get_AB(XH.to(DEV), UH.to(DEV))
        A_swap, _ = A.get_AB(XH[j2].to(DEV), UH[j2].to(DEV))
        dA = torch.linalg.norm(A_orig[i2.to(DEV)] - A_swap, dim=(1, 2))
        pred_o = A(XH[i2].to(DEV), UH[i2].to(DEV), UT[i2].to(DEV))
        pred_s = A(XH[j2].to(DEV), UH[j2].to(DEV), UT[i2].to(DEV))
        eo = torch.linalg.norm(pred_o - XN[i2].to(DEV), dim=1)
        es = torch.linalg.norm(pred_s - XN[i2].to(DEV), dim=1)
    res = {"n_pairs": int(len(i2)), "eps_u": eps_u,
           "cur_state_dist_mean": float(cdist[i2, j2].mean()), "prev_u_dist_mean": float(udist[i2, j2].mean()),
           "next_step_err_normal": float(eo.mean()), "next_step_err_swapped": float(es.mean()),
           "err_ratio": float(es.mean() / eo.mean()),
           "dA_orig_vs_swapped_mean": float(dA.mean()), "dA_orig_vs_swapped_q95": float(dA.quantile(0.95)),
           "A0_fro": float(torch.linalg.norm(A.A0).item())}
    print("[13D]", json.dumps(res, indent=2))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--part", default="A,C,D")
    args = ap.parse_args()
    CFG = load_config(os.path.join(REPO, "configs", "platform2.yaml"))
    DATA_DIR = os.path.abspath(os.path.join(REPO, CFG["data"]["data_dir"]))
    _, _, _, _, NORM = build_split(DATA_DIR, "train", CFG)
    out = {}
    if "A" in args.part: out["gate13A"] = part_13A()
    if "C" in args.part: out["gate13C"] = part_13C()
    if "D" in args.part: out["gate13D"] = part_13D()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("saved", OUT)
