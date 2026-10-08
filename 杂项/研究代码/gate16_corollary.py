"""Gate-16 addendum: Corollary-1 physical-space check (L_C, bound vs actual)."""
import sys, os, json
import numpy as np, torch
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
sys.path.insert(0, TMP)
from gate_context_koopman import build_split, REPO
from gate14_stabilize import BudgetedCtxKoopman
from patchtst_koopman.utils.config_loader import load_config

DEV = "cuda" if torch.cuda.is_available() else "cpu"
STATE = os.path.join(TMP, "gate_states")
CFG = load_config(os.path.join(REPO, "configs", "platform2.yaml"))
DATA_DIR = os.path.abspath(os.path.join(REPO, CFG["data"]["data_dir"]))
P = CFG["encoder"]["history_length"]; M = CFG["data"]["control_dim"]; H_LIST = [1, 5, 10, 20]

model = BudgetedCtxKoopman(CFG).to(DEV)
model.load_state_dict(torch.load(os.path.join(STATE, "A_stab_openloop_lam0.0_rho0.99.pt"), map_location=DEV)); model.eval()

# decoder = C = [I_n | 0] (projection, no params) -> L_C = ||C||_2 = 1 exactly
L_C = 1.0
print("decoder = [I_n|0] projection, L_C =", L_C, flush=True)

d = np.load(os.path.join(DATA_DIR, "val.npz")); trd = np.load(os.path.join(DATA_DIR, "train.npz"))
x = (d["x"] - trd["x"].mean(0)) / (trd["x"].std(0) + 1e-8)
u = (d["u"] - trd["u"].mean(0)) / (trd["u"].std(0) + 1e-8)
tid = d["trajectory_id"]

phys_err = {h: [] for h in H_LIST}
with torch.no_grad():
    for t in np.unique(tid):
        idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
        for k in range(P - 1, len(xx) - max(H_LIST) - 1, 4):
            xh0 = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
            uh0 = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
            z = model.encoder(xh0)
            xbuf = [xx[j] for j in range(k - P + 1, k + 1)]; ubuf = [uu[j] for j in range(k - P + 1, k)]
            for h in range(1, max(H_LIST) + 1):
                ut = torch.tensor(uu[k + h - 1], dtype=torch.float32).reshape(1, M).to(DEV)
                cx = torch.tensor(np.array(xbuf[-P:]), dtype=torch.float32).unsqueeze(0).to(DEV)
                cu = torch.tensor(np.array(ubuf[-(P - 1):]), dtype=torch.float32).unsqueeze(0).to(DEV)
                A, B = model.get_AB(cx, cu)
                z = torch.einsum('nij,nj->ni', A, z) + torch.einsum('nij,nj->ni', B, ut)
                xn = model.decoder(z); xbuf.append(xn[0].cpu().numpy()); ubuf.append(uu[k + h - 1])
                if h in phys_err:
                    gt = torch.tensor(xx[k + h], dtype=torch.float32).to(DEV)
                    phys_err[h].append(float(torch.linalg.norm(xn.squeeze(0) - gt)))

out = {"L_C": L_C,
       "physical_rmse": {str(h): float(np.sqrt(np.mean(np.square(phys_err[h])))) for h in H_LIST},
       "physical_mae": {str(h): float(np.mean(phys_err[h])) for h in H_LIST},
       "note": "Corollary-1 bound = L_C * (Prop.2 latent bound); compare with physical_rmse."}
p = os.path.join(TMP, "gate16_corollary.json")
with open(p, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(json.dumps(out, ensure_ascii=False, indent=2), flush=True)
print("saved", p)
