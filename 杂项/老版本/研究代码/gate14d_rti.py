"""Gate-14D: RTI-SQP (1 iteration) for RTI-RE and RTI-SP + runtime profiling.

RTI-RE: each prediction stage re-runs the full PatchTST encoder.
RTI-SP: rollout-trained scheduled propagation (latent propagated, context re-scheduled from decoded history).
Plant = independent DirectNN. Reports tracking RMSE, degradation vs exact oracle, runtime components, solver failure, max|u|.
"""
import sys, os, json, time
import numpy as np, torch
from scipy.optimize import minimize

sys.path.insert(0, r"C:\Users\12187\AppData\Local\Temp\opencode")
from gate14c_control import predict, CtxKoopman, BudgetedCtxKoopman, DirectNN, build_split, CFG, DATA_DIR, P, M, N, Q, R, S, UMIN, UMAX, DEV, STATE
from gate14_directnn import train as train_dnn

OUT = r"C:\Users\12187\AppData\Local\Temp\opencode\gate14d_result.json"


def rollout_and_jac(model, mode, xh, uh, U):
    U = U.clone().requires_grad_(True)
    pred = predict(model, xh, uh, U, mode)              # (N,n)
    J = torch.zeros(N * pred.shape[1], N * M, device=DEV)
    for i in range(N):
        for j in range(pred.shape[1]):
            g = torch.autograd.grad(pred[i, j], U, retain_graph=True)[0]
            J[i * pred.shape[1] + j] = g.reshape(-1)
    return pred.detach(), J.detach()


def solve_qp(pred, J, Uw, ref, u_prev):
    n = pred.shape[1]
    pf = pred.reshape(-1).cpu().numpy(); Jf = J.cpu().numpy()
    rf = ref.reshape(-1).cpu().numpy(); Uwf = Uw.detach().reshape(-1).cpu().numpy()
    up = u_prev.detach().cpu().numpy()
    Uw2 = Uwf.reshape(N, M)

    def cost(dU):
        U = Uwf + dU
        e = pf + Jf @ dU - rf
        U2 = U.reshape(N, M)
        d = np.vstack([U2[:1] - up, np.diff(U2, axis=0)])
        return Q * (e @ e) + R * (U @ U) + S * (d * d).sum()

    bounds = [(UMIN - Uwf[i], UMAX - Uwf[i]) for i in range(N * M)]
    r = minimize(cost, np.zeros(N * M), method="L-BFGS-B", bounds=bounds, options={"maxiter": 50})
    return Uw.detach() + torch.tensor(r.x.reshape(N, M), dtype=torch.float32).to(DEV), (not r.success)


def rti_step(model, mode, xh, uh, ref, Uw, u_prev, n_iter=1):
    t_roll = t_qp = 0.0; fail = False; U = Uw
    for _ in range(n_iter):
        a = time.time()
        pred, J = rollout_and_jac(model, mode, xh, uh, U)
        b = time.time()
        U, fail = solve_qp(pred, J, U, ref, u_prev)
        c = time.time()
        t_roll += (b - a) * 1000; t_qp += (c - b) * 1000
    return U, t_roll, t_qp, t_roll + t_qp, fail


def closed_loop_rti(model, mode, plant, x_ref, u_ref, n_iter=1):
    xh = torch.tensor(x_ref[:P], dtype=torch.float32).to(DEV)
    uh = torch.tensor(u_ref[:P - 1], dtype=torch.float32).to(DEV)
    u_prev = torch.tensor(u_ref[P - 1], dtype=torch.float32).to(DEV)
    Uw = u_prev.unsqueeze(0).repeat(N, 1)
    errs, t_roll, t_qp, t_tot, fails, umax = [], [], [], [], 0, 0.0
    for k in range(len(x_ref) - N - 1):
        ref = torch.tensor(x_ref[k + 1:k + 1 + N], dtype=torch.float32).to(DEV)
        Un, tr, tq, tt, fail = rti_step(model, mode, xh, uh, ref, Uw, u_prev, n_iter=n_iter)
        fails += int(fail); t_roll.append(tr); t_qp.append(tq); t_tot.append(tt)
        u0 = Un[0]; umax = max(umax, float(u0.abs().max()))
        with torch.no_grad():
            xn = plant(xh.unsqueeze(0), uh.unsqueeze(0), u0.unsqueeze(0)).squeeze(0)
        errs.append(torch.linalg.norm(xn - torch.tensor(x_ref[k + 1], dtype=torch.float32).to(DEV)).item())
        xh = torch.cat([xh[1:], xn.unsqueeze(0)]); uh = torch.cat([uh[1:], u0.unsqueeze(0)])
        Uw = torch.cat([Un[1:], Un[-1:]], dim=0); u_prev = u0
    q = lambda a, p: float(np.quantile(a, p))
    return {"rmse": float(np.sqrt(np.mean(np.square(errs)))),
            "roll_p50": q(t_roll, .5), "roll_p95": q(t_roll, .95),
            "qp_p50": q(t_qp, .5), "qp_p95": q(t_qp, .95),
            "total_p50": q(t_tot, .5), "total_p95": q(t_tot, .95),
            "solver_fail_pct": 100.0 * fails / max(1, len(errs)), "max_abs_u": umax}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--N", type=int, default=8)
    ap.add_argument("--n_iter", type=int, default=1); ap.add_argument("--tag", type=str, default="")
    args = ap.parse_args(); globals()["N"] = args.N
    print("N =", N, "n_iter =", args.n_iter)
    trXH, trUH, trUT, trXN, NORM = build_split(DATA_DIR, "train", CFG)
    plant, _ = train_dnn(trXH, trUH, trUT, trXN, epochs=100); plant.eval()
    aonly = CtxKoopman(CFG, "A", r=2).to(DEV); aonly.load_state_dict(torch.load(os.path.join(STATE, "A_r2.pt"), map_location=DEV)); aonly.eval()
    aol = BudgetedCtxKoopman(CFG).to(DEV); aol.load_state_dict(torch.load(os.path.join(STATE, "A_stab_openloop_lam0.0_rho0.99.pt"), map_location=DEV)); aol.eval()
    d = np.load(os.path.join(DATA_DIR, "val.npz")); trd = np.load(os.path.join(DATA_DIR, "train.npz"))
    x = (d["x"] - trd["x"].mean(0)) / (trd["x"].std(0) + 1e-8); u = (d["u"] - trd["u"].mean(0)) / (trd["u"].std(0) + 1e-8)
    tid = d["trajectory_id"]; trajs = list(np.unique(tid))[:3]
    res = {}
    for name, m, mode in [("RTI-RE", aonly, "reencode"), ("RTI-SP", aol, "sched")]:
        rows = [closed_loop_rti(m, mode, plant, x[np.where(tid == t)[0][:40]], u[np.where(tid == t)[0][:40]], n_iter=args.n_iter) for t in trajs]
        agg = {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}
        agg["total_p95"] = float(np.max([r["total_p95"] for r in rows]))
        res[name] = agg
        print(name, json.dumps({k: round(v, 2) for k, v in agg.items()}))
    # exact oracle references (from Gate-14C, re-encoding SLSQP)
    oracle = {"C0_fixed": 0.1367, "C2_aonly": 0.1360}
    for name, okey in [("RTI-RE", "C2_aonly")]:
        res[name]["oracle_rmse"] = oracle[okey]
        res[name]["degradation_vs_oracle_pct"] = 100.0 * (res[name]["rmse"] - oracle[okey]) / oracle[okey]
    res["RTI-SP"]["oracle_rmse"] = oracle["C2_aonly"]
    res["RTI-SP"]["degradation_vs_oracle_pct"] = 100.0 * (res["RTI-SP"]["rmse"] - oracle["C2_aonly"]) / oracle["C2_aonly"]
    res["_ref_oracle_fixed_C0"] = oracle["C0_fixed"]
    outp = OUT if not args.tag else OUT.replace(".json", f"{args.tag}.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2, default=str)
    print("saved", outp)
