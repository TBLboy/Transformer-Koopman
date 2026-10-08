"""Gate-14C: closed-loop receding-horizon control proxy.

Plant = independent DirectNN (trained on real P2 data). Reference = recorded val trajectories.
Controllers:
  C0  fixed TK model + re-encoding MPC
  C2  A-only r2 model + re-encoding MPC
  C2b A-only open-loop-trained model + scheduled-propagation MPC
  C1  A-only r2 model + frozen latent-propagation MPC (expected to fail)
Solver: scipy SLSQP (oracle). Runtime measured per solve.
"""
import sys, os, json, time
import numpy as np, torch, torch.nn.functional as F

sys.path.insert(0, r"C:\Users\12187\AppData\Local\Temp\opencode")
from gate_context_koopman import CtxKoopman, build_split, REPO
from gate14_stabilize import BudgetedCtxKoopman
from gate14_directnn import DirectNN
from patchtst_koopman.utils.config_loader import load_config
from scipy.optimize import minimize

DEV = "cuda" if torch.cuda.is_available() else "cpu"
STATE = r"C:\Users\12187\AppData\Local\Temp\opencode\gate_states"
OUT = r"C:\Users\12187\AppData\Local\Temp\opencode\gate14c_result.json"
CFG = load_config(os.path.join(REPO, "configs", "platform2.yaml"))
DATA_DIR = os.path.abspath(os.path.join(REPO, CFG["data"]["data_dir"]))
P = CFG["encoder"]["history_length"]; M = CFG["data"]["control_dim"]; N = 8
UMIN, UMAX = -3.0, 3.0
Q, R, S = 1.0, 0.01, 0.1


def predict(model, xh0, uh0, U, mode):
    """U: (N,m) tensor. Returns (N,n) predicted x."""
    xh = xh0.clone(); uh = uh0.clone(); preds = []
    if mode == "reencode":
        for i in range(U.shape[0]):
            ut = U[i]
            xn = model(xh.unsqueeze(0), uh.unsqueeze(0), ut.unsqueeze(0)).squeeze(0)
            preds.append(xn); xh = torch.cat([xh[1:], xn.unsqueeze(0)]); uh = torch.cat([uh[1:], ut.unsqueeze(0)])
    else:  # prop (frozen or scheduled)
        z = model.encoder(xh0.unsqueeze(0))
        if mode == "frozen":
            A_f, B_f = model.get_AB(xh0.unsqueeze(0), uh0.unsqueeze(0))
        xbuf = [xh0[j] for j in range(P)]; ubuf = [uh0[j] for j in range(P - 1)]
        for i in range(U.shape[0]):
            ut = U[i]
            if mode == "sched":
                cx = torch.stack(xbuf[-P:]).unsqueeze(0); cu = torch.stack(ubuf[-(P - 1):]).unsqueeze(0)
                A, B = model.get_AB(cx, cu)
            else:
                A, B = A_f, B_f
            z = torch.einsum('nij,nj->ni', A, z) + torch.einsum('nij,nj->ni', B, ut.unsqueeze(0))
            xn = model.decoder(z).squeeze(0)
            preds.append(xn); xbuf.append(xn); ubuf.append(ut)
    return torch.stack(preds)


def mpc(model, mode, xh0, uh0, ref, u_prev):
    def cost(Unp):
        U = torch.tensor(Unp.reshape(N, M), dtype=torch.float32).to(DEV)
        pred = predict(model, xh0, uh0, U, mode)
        c = Q * ((pred - ref) ** 2).sum()
        c = c + R * (U ** 2).sum()
        du = torch.cat([U[:1] - u_prev.unsqueeze(0), U[1:] - U[:-1]], 0)
        c = c + S * (du ** 2).sum()
        return c.item()
    U0 = np.tile(np.clip(u_prev.detach().cpu().numpy(), UMIN, UMAX), (N, 1))
    bounds = [(UMIN, UMAX)] * (N * M)
    t0 = time.time()
    r = minimize(cost, U0.ravel(), method="SLSQP", bounds=bounds, options={"maxiter": 30, "ftol": 1e-6, "eps": 1e-3})
    dt = (time.time() - t0) * 1000
    return torch.tensor(r.x.reshape(N, M), dtype=torch.float32).to(DEV), dt


def run_closed_loop(ctrl_model, ctrl_mode, plant, x_ref, u_ref):
    x = x_ref.copy()
    xh = torch.tensor(x[:P], dtype=torch.float32).to(DEV)
    uh = torch.tensor(u_ref[:P - 1], dtype=torch.float32).to(DEV)
    u_prev = torch.tensor(u_ref[P - 1], dtype=torch.float32).to(DEV)
    errs, times = [], []
    for k in range(len(x_ref) - N - 1):
        ref = torch.tensor(x_ref[k + 1:k + 1 + N], dtype=torch.float32).to(DEV)
        U, dt = mpc(ctrl_model, ctrl_mode, xh, uh, ref, u_prev)
        u_prev = U[0]; times.append(dt)
        with torch.no_grad():
            xn = plant(xh.unsqueeze(0), uh.unsqueeze(0), U[0].unsqueeze(0)).squeeze(0)
        errs.append(torch.linalg.norm(xn - torch.tensor(x_ref[k + 1], dtype=torch.float32).to(DEV)).item())
        xh = torch.cat([xh[1:], xn.unsqueeze(0)]); uh = torch.cat([uh[1:], U[0].unsqueeze(0)])
    return float(np.sqrt(np.mean(np.square(errs)))), float(np.median(times)), float(np.quantile(times, .95))


if __name__ == "__main__":
    d = np.load(os.path.join(DATA_DIR, "val.npz"))
    trd = np.load(os.path.join(DATA_DIR, "train.npz"))
    x = (d["x"].astype(np.float64) - trd["x"].mean(0)) / (trd["x"].std(0) + 1e-8)
    u = (d["u"].astype(np.float64) - trd["u"].mean(0)) / (trd["u"].std(0) + 1e-8)
    tid = d["trajectory_id"]
    from gate14_directnn import train as train_dnn
    trXH, trUH, trUT, trXN, NORM = build_split(DATA_DIR, "train", CFG)
    plant, _ = train_dnn(trXH, trUH, trUT, trXN, epochs=100)
    plant.eval()
    fixed = CtxKoopman(CFG, "fixed").to(DEV); fixed.load_state_dict(torch.load(os.path.join(STATE, "fixed.pt"), map_location=DEV)); fixed.eval()
    aonly = CtxKoopman(CFG, "A", r=2).to(DEV); aonly.load_state_dict(torch.load(os.path.join(STATE, "A_r2.pt"), map_location=DEV)); aonly.eval()
    aol = BudgetedCtxKoopman(CFG).to(DEV); aol.load_state_dict(torch.load(os.path.join(STATE, "A_stab_openloop_lam0.0_rho0.99.pt"), map_location=DEV)); aol.eval()

    controllers = [("C0_fixed_reencode", fixed, "reencode"), ("C2_aonly_reencode", aonly, "reencode"),
                   ("C2b_aol_sched", aol, "sched"), ("C1_aonly_frozen", aonly, "frozen")]
    trajs = list(np.unique(tid))[:2]
    res = {}
    for name, m, mode in controllers:
        rr = []
        for t in trajs:
            idx = np.where(tid == t)[0][:36]
            if len(idx) < N + 5:
                continue
            r, med, p95 = run_closed_loop(m, mode, plant, x[idx], u[idx])
            rr.append({"rmse": r, "med_ms": med, "p95_ms": p95})
        res[name] = {"rmse_mean": float(np.mean([q["rmse"] for q in rr])),
                     "med_ms": float(np.median([q["med_ms"] for q in rr])),
                     "p95_ms": float(np.median([q["p95_ms"] for q in rr])), "per_traj": rr}
        print(name, "rmse", round(res[name]["rmse_mean"], 4), "med_ms", round(res[name]["med_ms"], 1), "p95_ms", round(res[name]["p95_ms"], 1))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2, default=str)
    print("saved", OUT)
