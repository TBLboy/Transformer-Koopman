"""Gate-14A: manifold consistency defect d_M(H) and its correlation with physical error."""
import sys, os, json
import numpy as np, torch

sys.path.insert(0, r"C:\Users\12187\AppData\Local\Temp\opencode")
from gate_context_koopman import CtxKoopman, build_split, H_EVAL, H_MAX, REPO
from gate14_stabilize import BudgetedCtxKoopman
from patchtst_koopman.utils.config_loader import load_config

DEV = "cuda" if torch.cuda.is_available() else "cpu"
STATE = r"C:\Users\12187\AppData\Local\Temp\opencode\gate_states"
OUT = r"C:\Users\12187\AppData\Local\Temp\opencode\gate14a_result.json"
CFG = load_config(os.path.join(REPO, "configs", "platform2.yaml"))
DATA_DIR = os.path.abspath(os.path.join(REPO, CFG["data"]["data_dir"]))
_, _, _, _, NORM = build_split(DATA_DIR, "train", CFG)


def defect(model, split, sched, stride=8):
    d = np.load(os.path.join(DATA_DIR, f"{split}.npz"))
    x = (d["x"].astype(np.float64) - NORM["x_mean"]) / NORM["x_std"]
    u = (d["u"].astype(np.float64) - NORM["u_mean"]) / NORM["u_std"]
    tid = d["trajectory_id"]; P = CFG["encoder"]["history_length"]; m = CFG["data"]["control_dim"]
    res = {h: {"dM": [], "err": []} for h in H_EVAL}
    with torch.no_grad():
        for t in np.unique(tid):
            idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
            for k in range(P - 1, len(xx) - H_MAX - 1, stride):
                xh0 = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                uh0 = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
                zt = model.encoder(xh0)
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
                    zt = torch.einsum('nij,nj->ni', A, zt) + torch.einsum('nij,nj->ni', B, ut)
                    xn = model.decoder(zt)
                    xbuf.append(xn[0].cpu().numpy()); ubuf.append(uu[k + h - 1])
                    xhE = torch.tensor(np.array(xbuf[-P:]), dtype=torch.float32).unsqueeze(0).to(DEV)
                    uhE = torch.tensor(np.array(ubuf[-(P - 1):]), dtype=torch.float32).unsqueeze(0).to(DEV)
                    zE = model.encoder(xhE)
                    dM = (torch.linalg.norm(zt - zE) / (torch.linalg.norm(zE) + 1e-9)).item()
                    gt = torch.tensor(xx[k + h], dtype=torch.float32).to(DEV)
                    err = torch.linalg.norm(xn.squeeze(0) - gt).item()
                    if h in res:
                        res[h]["dM"].append(dM); res[h]["err"].append(err)
    out = {}
    for h in H_EVAL:
        dm = np.array(res[h]["dM"]); er = np.array(res[h]["err"])
        out[str(h)] = {"dM_mean": float(dm.mean()), "dM_q95": float(np.quantile(dm, .95)),
                       "err_mean": float(er.mean()),
                       "corr_dM_err": float(np.corrcoef(dm, er)[0, 1]) if len(dm) > 2 else None}
    return out


if __name__ == "__main__":
    res = {}
    base = CtxKoopman(CFG, "A", r=2).to(DEV)
    base.load_state_dict(torch.load(os.path.join(STATE, "A_r2.pt"), map_location=DEV)); base.eval()
    for name, m, sched in [("A_r2_Rprop", base, True), ("A_r2_Fprop", base, False)]:
        res[name] = defect(m, "val", sched)
        print(name, json.dumps({h: {k: round(v, 4) for k, v in d.items()} for h, d in res[name].items()}))
    ol = BudgetedCtxKoopman(CFG).to(DEV)
    ol.load_state_dict(torch.load(os.path.join(STATE, "A_stab_openloop_lam0.0_rho0.99.pt"), map_location=DEV)); ol.eval()
    for name, m, sched in [("A_openloop_Rprop", ol, True), ("A_openloop_Fprop", ol, False)]:
        res[name] = defect(m, "val", sched)
        print(name, json.dumps({h: {k: round(v, 4) for k, v in d.items()} for h, d in res[name].items()}))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("saved", OUT)
