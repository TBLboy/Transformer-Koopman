"""Gate-16 Theory Diagnostics (GPT round-16 §19).

On the frozen deployment predictor (A_openloop, r=2 scheduled propagation):
  eps_k            one-step encoder-consistency defect  (Prop.2)
  d_M(H)           latent rollout/manifold defect, H=1/5/10/20  (Def.2 / Gate-14A)
  ||A_{k+H-1}..A_k||_2   transition product norm, H=1/5/10/20  (Prop.2 mechanism)
  ||dF/dxi||_2     empirical Lipschitz of augmented map  (Thm.1 L_F)
  bound vs actual  Theorem-1 finite-horizon bound vs physical error
  linearization remainder  RTI Taylor remainder quantiles  (Prop.3)
"""
import sys, os, json
import numpy as np, torch

TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
sys.path.insert(0, TMP)
from gate_context_koopman import CtxKoopman, build_split, REPO
from gate14_stabilize import BudgetedCtxKoopman
from patchtst_koopman.utils.config_loader import load_config

DEV = "cuda" if torch.cuda.is_available() else "cpu"
STATE = os.path.join(TMP, "gate_states")
OUT = os.path.join(TMP, "gate16_theory_diagnostics.json")
CFG = load_config(os.path.join(REPO, "configs", "platform2.yaml"))
DATA_DIR = os.path.abspath(os.path.join(REPO, CFG["data"]["data_dir"]))
P = CFG["encoder"]["history_length"]; M = CFG["data"]["control_dim"]; N = CFG["data"]["state_dim"]
D = CFG["encoder"]["latent_dim"]; H_LIST = [1, 5, 10, 20]
EPS0 = 1e-6


def q(a, p):
    return float(np.quantile(np.asarray(a, dtype=float), p))


def load_val():
    d = np.load(os.path.join(DATA_DIR, "val.npz")); trd = np.load(os.path.join(DATA_DIR, "train.npz"))
    x = (d["x"].astype(np.float64) - trd["x"].mean(0)) / (trd["x"].std(0) + 1e-8)
    u = (d["u"].astype(np.float64) - trd["u"].mean(0)) / (trd["u"].std(0) + 1e-8)
    return x, u, d["trajectory_id"]


def main():
    model = BudgetedCtxKoopman(CFG).to(DEV)
    model.load_state_dict(torch.load(os.path.join(STATE, "A_stab_openloop_lam0.0_rho0.99.pt"), map_location=DEV))
    model.eval()
    x, u, tid = load_val()
    res = {"model": "A_openloop r=2 (sched)", "P": P, "d": D, "H_list": H_LIST}

    # ---------- eps_k : one-step encoder-consistency defect ----------
    eps, eps_norm = [], []
    with torch.no_grad():
        for t in np.unique(tid):
            idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
            for k in range(P - 1, len(xx) - 1):
                xh = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                uh = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
                ut = torch.tensor(uu[k], dtype=torch.float32).unsqueeze(0).to(DEV)
                xhn = torch.tensor(xx[k - P + 2:k + 2], dtype=torch.float32).unsqueeze(0).to(DEV)
                uhn = torch.tensor(uu[k - P + 2:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                z = model.encoder(xh); A, B = model.get_AB(xh, uh)
                z2 = torch.einsum('nij,nj->ni', A, z) + torch.einsum('nij,nj->ni', B, ut)
                zE = model.encoder(xhn)
                e = torch.linalg.norm(z2 - zE).item(); nrm = torch.linalg.norm(zE).item()
                eps.append(e); eps_norm.append(e / (nrm + EPS0))
    res["eps_k"] = {"abs": {"median": q(eps, .5), "q90": q(eps, .9), "q95": q(eps, .95), "q99": q(eps, .99), "max": float(np.max(eps))},
                    "norm": {"median": q(eps_norm, .5), "q90": q(eps_norm, .9), "q95": q(eps_norm, .95), "q99": q(eps_norm, .99)}}
    print("eps_k", {k: round(v, 5) for k, v in res["eps_k"]["abs"].items()}, flush=True)

    # ---------- d_M(H) + product norms ----------
    dM = {h: [] for h in H_LIST}; prod = {h: [] for h in H_LIST}; prod_p95 = {h: [] for h in H_LIST}
    with torch.no_grad():
        for t in np.unique(tid):
            idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
            for k in range(P - 1, len(xx) - max(H_LIST) - 1, 4):
                xh0 = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                uh0 = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
                z = model.encoder(xh0)
                xbuf = [xx[j] for j in range(k - P + 1, k + 1)]; ubuf = [uu[j] for j in range(k - P + 1, k)]
                As = []
                for h in range(1, max(H_LIST) + 1):
                    ut = torch.tensor(uu[k + h - 1], dtype=torch.float32).reshape(1, M).to(DEV)
                    cx = torch.tensor(np.array(xbuf[-P:]), dtype=torch.float32).unsqueeze(0).to(DEV)
                    cu = torch.tensor(np.array(ubuf[-(P - 1):]), dtype=torch.float32).unsqueeze(0).to(DEV)
                    A, B = model.get_AB(cx, cu); As.append(A[0].cpu().numpy())
                    z = torch.einsum('nij,nj->ni', A, z) + torch.einsum('nij,nj->ni', B, ut)
                    xn = model.decoder(z); xbuf.append(xn[0].cpu().numpy()); ubuf.append(uu[k + h - 1])
                    if h in dM:
                        xhE = torch.tensor(xx[k + h - P + 1:k + h + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                        zE = model.encoder(xhE)
                        dM[h].append((torch.linalg.norm(z - zE) / (torch.linalg.norm(zE) + EPS0)).item())
                        Pm = np.eye(D)
                        for Ai in As[-h:]:
                            Pm = Ai @ Pm
                        prod[h].append(float(np.linalg.norm(Pm, 2)))
    res["dM"] = {str(h): {"median": q(dM[h], .5), "q90": q(dM[h], .9)} for h in H_LIST}
    res["prod_norm"] = {str(h): {"median": q(prod[h], .5), "q90": q(prod[h], .9), "max": float(np.max(prod[h]))} for h in H_LIST}
    print("dM", {k: round(v["median"], 4) for k, v in res["dM"].items()}, flush=True)
    print("prod", {k: round(v["median"], 4) for k, v in res["prod_norm"].items()}, flush=True)

    # ---------- ||dF/dxi||_2 : augmented map Jacobian ----------
    def aug_F(xh, uh, z, ut):
        A, B = model.get_AB(xh, uh)
        z2 = torch.einsum('nij,nj->ni', A, z) + torch.einsum('nij,nj->ni', B, ut)
        xn = model.decoder(z2)
        xh2 = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
        uh2 = torch.cat([uh[:, 1:, :], ut.unsqueeze(1)], dim=1)
        return xh2, uh2, z2

    jac_norms = []

    def aug_F_flat(xh, uh, z, ut):
        xh2, uh2, z2 = aug_F(xh, uh, z, ut)
        return torch.cat([xh2.reshape(-1), uh2.reshape(-1), z2.reshape(-1)])

    for t in list(np.unique(tid))[:6]:
        idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
        for k in range(P - 1, min(len(xx) - 2, 120), 3):
            xh = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
            uh = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
            z = model.encoder(xh)
            ut = torch.tensor(uu[k], dtype=torch.float32).unsqueeze(0).to(DEV)
            Jm = torch.autograd.functional.jacobian(
                lambda a, b, c: aug_F_flat(a, b, c, ut), (xh, uh, z), vectorize=False)
            Jcat = torch.cat([Jm[i].reshape(Jm[i].shape[0], -1) for i in range(3)], dim=1)
            sv = torch.linalg.svdvals(Jcat)
            jac_norms.append(float(sv[0]))
    res["dF_dxi"] = {"median": q(jac_norms, .5), "q90": q(jac_norms, .9), "q95": q(jac_norms, .95), "q99": q(jac_norms, .99), "max": float(np.max(jac_norms)), "n": len(jac_norms)}
    print("dF/dxi", {k: round(v, 4) for k, v in res["dF_dxi"].items() if k != "n"}, flush=True)

    # ---------- Prop.2 bound vs actual (latent) ----------
    eps95 = q(eps, .95)
    bound = {}
    for h in H_LIST:
        pm = q(prod[h], .5)
        p = pm ** (1.0 / h)
        s = sum(p ** i for i in range(h))
        bound[str(h)] = {"prod_median": pm, "geom_per_step": p,
                         "bound_latent": eps95 * s, "actual_dM_median": q(dM[h], .5),
                         "bound_over_actual": (eps95 * s) / (q(dM[h], .5) + EPS0)}
    res["bound_vs_actual"] = bound
    print("bound", {k: round(v["bound_over_actual"], 2) for k, v in bound.items()}, flush=True)

    # ---------- Prop.3 linearization remainder ----------
    rem = {}
    for dn in (1e-4, 1e-3, 1e-2):
        rs, ratios = [], []
        for t in list(np.unique(tid))[:4]:
            idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
            for k in range(P - 1, min(len(xx) - 2, 90), 5):
                xh = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                uh = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
                z = model.encoder(xh)
                ut = torch.tensor(uu[k], dtype=torch.float32).unsqueeze(0).to(DEV)
                Jm = torch.autograd.functional.jacobian(lambda a, b, c: aug_F_flat(a, b, c, ut), (xh, uh, z), vectorize=False)
                dxh = torch.randn_like(xh) * dn; duh = torch.randn_like(uh) * dn; dz = torch.randn_like(z) * dn
                dxh = dxh / dxh.norm() * dn; duh = duh / duh.norm() * dn; dz = dz / dz.norm() * dn
                f0 = aug_F_flat(xh, uh, z, ut)
                f1 = aug_F_flat(xh + dxh, uh + duh, z + dz, ut)
                Jd = (Jm[0].reshape(Jm[0].shape[0], -1) @ dxh.reshape(-1)
                      + Jm[1].reshape(Jm[1].shape[0], -1) @ duh.reshape(-1)
                      + Jm[2].reshape(Jm[2].shape[0], -1) @ dz.reshape(-1))
                r = (f1 - f0 - Jd)
                rn = float(r.norm()); dnorm = float(torch.sqrt(dxh.norm() ** 2 + duh.norm() ** 2 + dz.norm() ** 2))
                rs.append(rn); ratios.append(rn / (dnorm ** 2 + 1e-12))
        rem[str(dn)] = {"remainder_median": q(rs, .5), "remainder_q95": q(rs, .95),
                        "ratio_median": q(ratios, .5), "M_F_est": 2 * q(ratios, .95)}
    res["lin_remainder"] = rem
    print("lin_rem", {k: round(v["M_F_est"], 3) for k, v in rem.items()}, flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2, default=str)
    print("saved", OUT, flush=True)


if __name__ == "__main__":
    main()
