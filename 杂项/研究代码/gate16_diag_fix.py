"""Gate-16 diagnostics FIX (review items #2, #3, #4):
 - absolute latent defect d_abs(H) for a like-for-like bound comparison (Prop.2)
 - Corollary-1 bound with the correct augmented-map L_F
 - linearization remainder with proper delta scaling (delta^2 check) and fitted M_F
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
P = CFG["encoder"]["history_length"]; M = CFG["data"]["control_dim"]; H_LIST = [1, 5, 10, 20]
print("P =", P, "d =", CFG["encoder"]["latent_dim"], flush=True)

model = BudgetedCtxKoopman(CFG).to(DEV)
model.load_state_dict(torch.load(os.path.join(STATE, "A_stab_openloop_lam0.0_rho0.99.pt"), map_location=DEV)); model.eval()

d = np.load(os.path.join(DATA_DIR, "val.npz")); trd = np.load(os.path.join(DATA_DIR, "train.npz"))
x = (d["x"] - trd["x"].mean(0)) / (trd["x"].std(0) + 1e-8)
u = (d["u"] - trd["u"].mean(0)) / (trd["u"].std(0) + 1e-8)
tid = d["trajectory_id"]

# ---------- absolute eps and absolute d_abs ----------
eps_abs = []; d_abs = {h: [] for h in H_LIST}; d_norm = {h: [] for h in H_LIST}; prod = {h: [] for h in H_LIST}
with torch.no_grad():
    for t in np.unique(tid):
        idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
        for k in range(P - 1, len(xx) - max(H_LIST) - 1, 4):
            xh0 = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
            uh0 = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
            xhn = torch.tensor(xx[k - P + 2:k + 2], dtype=torch.float32).unsqueeze(0).to(DEV)
            uhn = torch.tensor(uu[k - P + 2:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
            z = model.encoder(xh0); A, B = model.get_AB(xh0, uh0)
            ut0 = torch.tensor(uu[k], dtype=torch.float32).reshape(1, M).to(DEV)
            z2 = torch.einsum('nij,nj->ni', A, z) + torch.einsum('nij,nj->ni', B, ut0)
            eps_abs.append(float(torch.linalg.norm(z2 - model.encoder(xhn))))
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
                    d_norm[h].append(float(torch.linalg.norm(zc - zE) / (torch.linalg.norm(zE) + 1e-6)))
                    Pm = np.eye(CFG["encoder"]["latent_dim"])
                    for Ai in As[-h:]:
                        Pm = Ai @ Pm
                    prod[h].append(float(np.linalg.norm(Pm, 2)))

q = lambda a, p: float(np.quantile(np.asarray(a, float), p))
eps95 = q(eps_abs, .95); eps50 = q(eps_abs, .5)
print("eps_abs median/q95 =", round(eps50, 4), round(eps95, 4), flush=True)

out = {"P": P, "eps_abs": {"median": eps50, "q95": eps95},
       "d_abs": {str(h): q(d_abs[h], .5) for h in H_LIST},
       "d_norm": {str(h): q(d_norm[h], .5) for h in H_LIST},
       "prod": {str(h): q(prod[h], .5) for h in H_LIST}}

# Prop.2 bound (absolute, median prod, eps95) vs ABSOLUTE actual d_abs  -> like-for-like
b_abs = {}
for h in H_LIST:
    p = q(prod[h], .5) ** (1.0 / h)
    s = sum(p ** i for i in range(h))
    b_abs[str(h)] = {"bound": eps95 * s, "actual": q(d_abs[h], .5), "ratio": (eps95 * s) / (q(d_abs[h], .5) + 1e-12)}
out["prop2_bound_vs_actual_abs"] = b_abs
print("Prop2 abs bound/actual:", {k: round(v["ratio"], 2) for k, v in b_abs.items()}, flush=True)

# Corollary 1 with augmented-map L_F (from diagnostics json)
LF = 1.44464
phys = {1: 0.010764446617697092, 5: 0.02215185992070836, 10: 0.029719543465888225, 20: 0.04185685781619683}
c1 = {}
for h in H_LIST:
    b = eps95 * sum(LF ** j for j in range(h))
    c1[str(h)] = {"bound_LF": b, "actual_phys_rmse": phys[h], "ratio": b / phys[h]}
out["corollary1_bound_LF"] = c1
print("Cor1 (L_F=1.445) bound/actual:", {k: round(v["ratio"], 1) for k, v in c1.items()}, flush=True)

# ---------- linearization remainder with delta^2 scaling ----------
def aug_F_flat(xh, uh, z, ut):
    A, B = model.get_AB(xh, uh)
    z2 = torch.einsum('nij,nj->ni', A, z) + torch.einsum('nij,nj->ni', B, ut)
    xn = model.decoder(z2)
    xh2 = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
    uh2 = torch.cat([uh[:, 1:, :], ut.unsqueeze(1)], dim=1)
    return torch.cat([xh2.reshape(-1), uh2.reshape(-1), z2.reshape(-1)])

rem = {}
for dn in (1e-2, 3e-2, 1e-1):
    ratios = []
    for t in list(np.unique(tid))[:4]:
        idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
        for k in range(P - 1, min(len(xx) - 2, 90), 5):
            xh = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
            uh = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
            z = model.encoder(xh)
            ut = torch.tensor(uu[k], dtype=torch.float32).unsqueeze(0).to(DEV)
            Jm = torch.autograd.functional.jacobian(lambda a, b, c: aug_F_flat(a, b, c, ut), (xh, uh, z), vectorize=False)
            torch.manual_seed(0)
            dxh = torch.randn_like(xh); duh = torch.randn_like(uh); dz = torch.randn_like(z)
            dxh = dxh / dxh.norm() * dn; duh = duh / duh.norm() * dn; dz = dz / dz.norm() * dn
            f0 = aug_F_flat(xh, uh, z, ut)
            f1 = aug_F_flat(xh + dxh, uh + duh, z + dz, ut)
            Jd = (Jm[0].reshape(Jm[0].shape[0], -1) @ dxh.reshape(-1)
                  + Jm[1].reshape(Jm[1].shape[0], -1) @ duh.reshape(-1)
                  + Jm[2].reshape(Jm[2].shape[0], -1) @ dz.reshape(-1))
            r = float((f1 - f0 - Jd).norm())
            dnorm = float(torch.sqrt(dxh.norm() ** 2 + duh.norm() ** 2 + dz.norm() ** 2))
            ratios.append(r / (dnorm ** 2))
    rem[str(dn)] = {"r_over_delta2_median": q(ratios, .5), "r_over_delta2_q95": q(ratios, .95), "M_F_est": 2 * q(ratios, .95)}
out["lin_remainder_scaling"] = rem
print("M_F_est by delta:", {k: round(v["M_F_est"], 3) for k, v in rem.items()}, flush=True)

p = os.path.join(TMP, "gate16_diag_fix.json")
with open(p, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("saved", p)
