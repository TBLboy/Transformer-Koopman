"""Gate-16 FINAL theory diagnostics (single source of truth).

Resolves the eps_k = 0.345 vs 0.347 conflict flagged in GPT round-19 §17:
the two previous scripts used different sampling (stride 1 vs stride 4 and a
shorter k-range). This script uses ONE documented scheme for every quantity:
  - eps_k, d_abs(H), d_M(H), prod(H): stride 1 (all admissible samples)
  - L_F = ||dF/dxi||_2: 6 trajectories, stride 3 (as in the original run)
Everything is written to gate16_diag_final.json.
"""
import sys, os, json
import numpy as np, torch

TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
sys.path.insert(0, TMP)
from gate_context_koopman import REPO
from gate14_stabilize import BudgetedCtxKoopman
from patchtst_koopman.utils.config_loader import load_config

DEV = "cuda" if torch.cuda.is_available() else "cpu"
STATE = os.path.join(TMP, "gate_states")
CFG = load_config(os.path.join(REPO, "configs", "platform2.yaml"))
DATA_DIR = os.path.abspath(os.path.join(REPO, CFG["data"]["data_dir"]))
P = CFG["encoder"]["history_length"]; M = CFG["data"]["control_dim"]; D = CFG["encoder"]["latent_dim"]
H_LIST = [1, 5, 10, 20]; EPS0 = 1e-6
q = lambda a, p: float(np.quantile(np.asarray(a, float), p))

model = BudgetedCtxKoopman(CFG).to(DEV)
model.load_state_dict(torch.load(os.path.join(STATE, "A_stab_openloop_lam0.0_rho0.99.pt"), map_location=DEV)); model.eval()
d = np.load(os.path.join(DATA_DIR, "val.npz")); trd = np.load(os.path.join(DATA_DIR, "train.npz"))
x = (d["x"].astype(np.float64) - trd["x"].mean(0)) / (trd["x"].std(0) + 1e-8)
u = (d["u"].astype(np.float64) - trd["u"].mean(0)) / (trd["u"].std(0) + 1e-8)
tid = d["trajectory_id"]
print("P =", P, "| stride = 1 (all samples)", flush=True)

eps, eps_norm = [], []
d_abs = {h: [] for h in H_LIST}; d_norm = {h: [] for h in H_LIST}; prod = {h: [] for h in H_LIST}
with torch.no_grad():
    for t in np.unique(tid):
        idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
        # --- eps_k on ALL samples (full range) ---
        for k in range(P - 1, len(xx) - 1):
            xh = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
            uh = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
            ut = torch.tensor(uu[k], dtype=torch.float32).reshape(1, M).to(DEV)
            xhn = torch.tensor(xx[k - P + 2:k + 2], dtype=torch.float32).unsqueeze(0).to(DEV)
            z = model.encoder(xh); A, B = model.get_AB(xh, uh)
            z2 = torch.einsum('nij,nj->ni', A, z) + torch.einsum('nij,nj->ni', B, ut)
            zE = model.encoder(xhn)
            e = float(torch.linalg.norm(z2 - zE))
            eps.append(e); eps_norm.append(e / (float(torch.linalg.norm(zE)) + EPS0))
        # --- rollout diagnostics on ALL samples (stride 1) ---
        for k in range(P - 1, len(xx) - max(H_LIST) - 1):
            xh0 = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
            uh0 = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
            zc = model.encoder(xh0)
            xbuf = [xx[j] for j in range(k - P + 1, k + 1)]; ubuf = [uu[j] for j in range(k - P + 1, k)]
            As = []
            for h in range(1, max(H_LIST) + 1):
                ut = torch.tensor(uu[k + h - 1], dtype=torch.float32).reshape(1, M).to(DEV)
                cx = torch.tensor(np.array(xbuf[-P:]), dtype=torch.float32).unsqueeze(0).to(DEV)
                cu = torch.tensor(np.array(ubuf[-(P - 1):]), dtype=torch.float32).unsqueeze(0).to(DEV)
                A, B = model.get_AB(cx, cu); As.append(A[0].cpu().numpy())
                zc = torch.einsum('nij,nj->ni', A, zc) + torch.einsum('nij,nj->ni', B, ut)
                xn = model.decoder(zc); xbuf.append(xn[0].cpu().numpy()); ubuf.append(uu[k + h - 1])
                if h in d_abs:
                    xhE = torch.tensor(xx[k + h - P + 1:k + h + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                    zE = model.encoder(xhE)
                    d_abs[h].append(float(torch.linalg.norm(zc - zE)))
                    d_norm[h].append(float(torch.linalg.norm(zc - zE) / (float(torch.linalg.norm(zE)) + EPS0)))
                    Pm = np.eye(D)
                    for Ai in As[-h:]:
                        Pm = Ai @ Pm
                    prod[h].append(float(np.linalg.norm(Pm, 2)))

out = {"P": P, "sampling": {"eps_and_rollout": "stride 1 (all admissible samples)", "n_eps": len(eps), "n_rollout": len(prod[1])},
       "eps_k_abs": {"median": q(eps, .5), "q90": q(eps, .9), "q95": q(eps, .95), "q99": q(eps, .99), "max": float(np.max(eps))},
       "eps_k_norm": {"median": q(eps_norm, .5), "q95": q(eps_norm, .95)},
       "d_abs": {str(h): q(d_abs[h], .5) for h in H_LIST},
       "d_norm": {str(h): q(d_norm[h], .5) for h in H_LIST},
       "prod": {str(h): q(prod[h], .5) for h in H_LIST}}
print("eps_k abs:", {k: round(v, 4) for k, v in out["eps_k_abs"].items()}, flush=True)
print("d_abs:", {k: round(v, 4) for k, v in out["d_abs"].items()}, flush=True)
print("d_norm:", {k: round(v, 4) for k, v in out["d_norm"].items()}, flush=True)
print("prod:", {k: round(v, 4) for k, v in out["prod"].items()}, flush=True)

# --- L_F (unchanged sampling: 6 trajectories, stride 3) ---
def aug_F_flat(xh, uh, z, ut):
    A, B = model.get_AB(xh, uh)
    z2 = torch.einsum('nij,nj->ni', A, z) + torch.einsum('nij,nj->ni', B, ut)
    xn = model.decoder(z2)
    xh2 = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
    uh2 = torch.cat([uh[:, 1:, :], ut.unsqueeze(1)], dim=1)
    return torch.cat([xh2.reshape(-1), uh2.reshape(-1), z2.reshape(-1)])

jac = []
for t in list(np.unique(tid))[:6]:
    idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
    for k in range(P - 1, min(len(xx) - 2, 120), 3):
        xh = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
        uh = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
        z = model.encoder(xh); ut = torch.tensor(uu[k], dtype=torch.float32).unsqueeze(0).to(DEV)
        Jm = torch.autograd.functional.jacobian(lambda a, b, c: aug_F_flat(a, b, c, ut), (xh, uh, z), vectorize=False)
        Jcat = torch.cat([Jm[i].reshape(Jm[i].shape[0], -1) for i in range(3)], dim=1)
        jac.append(float(torch.linalg.svdvals(Jcat)[0]))
out["L_F"] = {"median": q(jac, .5), "q95": q(jac, .95), "max": float(np.max(jac)), "n": len(jac)}
print("L_F:", {k: round(v, 4) for k, v in out["L_F"].items() if k != "n"}, flush=True)

# --- Prop.2 bound/actual (absolute vs absolute) ---
eps95 = out["eps_k_abs"]["q95"]; b = {}
for h in H_LIST:
    p = out["prod"][str(h)] ** (1.0 / h); s = sum(p ** i for i in range(h))
    b[str(h)] = {"bound": eps95 * s, "actual": out["d_abs"][str(h)], "ratio": (eps95 * s) / out["d_abs"][str(h)]}
out["prop2_bound_vs_actual_abs"] = b
print("Prop2 abs bound/actual:", {k: round(v["ratio"], 2) for k, v in b.items()}, flush=True)

# --- Cor.1 with L_F ---
LF = out["L_F"]["median"]
phys = {1: 0.010764446617697092, 5: 0.02215185992070836, 10: 0.029719543465888225, 20: 0.04185685781619683}
c1 = {}
for h in H_LIST:
    bd = eps95 * sum(LF ** j for j in range(h))
    c1[str(h)] = {"bound_LF": bd, "actual_phys_rmse": phys[h], "ratio": bd / phys[h]}
out["corollary1_bound_LF"] = c1
print("Cor1 (L_F=%.4f) bound/actual:" % LF, {k: round(v["ratio"], 1) for k, v in c1.items()}, flush=True)

p = os.path.join(TMP, "gate16_diag_final.json")
with open(p, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("saved", p, flush=True)
