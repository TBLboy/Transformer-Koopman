"""Gate-16: N-matched exact oracle vs RTI (GPT round-16 §5).

Same plant (DirectNN, saved once) for oracle and RTI so the comparison isolates
the RTI approximation from the horizon change.
Reports: oracle-sched / oracle-reencode (exact SLSQP) and RTI-SP / RTI-RE (1-iter)
at N=5 and N=8, plus Delta_RTI = (RMSE_RTI - RMSE_oracle)/RMSE_oracle.
"""
import sys, os, json, time, argparse
import numpy as np, torch

TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
sys.path.insert(0, TMP)
import gate14c_control as G
import gate14d_rti as R
from gate14_directnn import DirectNN, train as train_dnn

OUT = os.path.join(TMP, "gate16_matched_oracle.json")
PLANT_PATH = os.path.join(TMP, "plant_dnn.pt")

ap = argparse.ArgumentParser()
ap.add_argument("--N", type=int, default=5)
ap.add_argument("--tag", type=str, default="")
args = ap.parse_args()
G.N = args.N; R.N = args.N
print("N =", args.N, flush=True)

# ---- data (identical to gate14c/d) ----
d = np.load(os.path.join(G.DATA_DIR, "val.npz")); trd = np.load(os.path.join(G.DATA_DIR, "train.npz"))
x = (d["x"] - trd["x"].mean(0)) / (trd["x"].std(0) + 1e-8)
u = (d["u"] - trd["u"].mean(0)) / (trd["u"].std(0) + 1e-8)
tid = d["trajectory_id"]; trajs = list(np.unique(tid))[:3]

# ---- plant: train once and save (reuse if present) ----
if os.path.exists(PLANT_PATH):
    ck = torch.load(PLANT_PATH, map_location=G.DEV)
    plant = DirectNN(G.CFG, ck["hidden"]).to(G.DEV); plant.load_state_dict(ck["sd"]); plant.eval()
    print("plant loaded from disk", flush=True)
else:
    trXH, trUH, trUT, trXN, NORM = G.build_split(G.DATA_DIR, "train", G.CFG)
    plant, vloss = train_dnn(trXH, trUH, trUT, trXN, epochs=100); plant.eval()
    torch.save({"sd": plant.state_dict(), "hidden": 48}, PLANT_PATH)
    print("plant trained and saved (val_loss=%.6f)" % vloss, flush=True)

# ---- models ----
aonly = G.CtxKoopman(G.CFG, "A", r=2).to(G.DEV)
aonly.load_state_dict(torch.load(os.path.join(G.STATE, "A_r2.pt"), map_location=G.DEV)); aonly.eval()
aol = G.BudgetedCtxKoopman(G.CFG).to(G.DEV)
aol.load_state_dict(torch.load(os.path.join(G.STATE, "A_stab_openloop_lam0.0_rho0.99.pt"), map_location=G.DEV)); aol.eval()

STEP = 30
res = {"N": args.N, "plant": "DirectNN(saved)"}

def run_oracle(m, mode):
    rows = []
    for t in trajs:
        idx = np.where(tid == t)[0][:STEP + args.N + 1]
        r, med, p95 = G.run_closed_loop(m, mode, plant, x[idx], u[idx])
        rows.append({"rmse": r, "med_ms": med, "p95_ms": p95})
    return {"rmse_mean": float(np.mean([q["rmse"] for q in rows])),
            "med_ms": float(np.median([q["med_ms"] for q in rows])),
            "p95_ms": float(np.median([q["p95_ms"] for q in rows]))}

def run_rti(m, mode):
    rows = [R.closed_loop_rti(m, mode, plant, x[np.where(tid == t)[0][:STEP + args.N + 1]],
                              u[np.where(tid == t)[0][:STEP + args.N + 1]], n_iter=1) for t in trajs]
    return {"rmse_mean": float(np.mean([q["rmse"] for q in rows])),
            "total_p50": float(np.median([q["total_p50"] for q in rows])),
            "total_p95": float(np.max([q["total_p95"] for q in rows]))}

for tag, fn, m, mode in [("oracle_sched", run_oracle, aol, "sched"),
                         ("oracle_reencode", run_oracle, aonly, "reencode"),
                         ("rti_sp", run_rti, aol, "sched"),
                         ("rti_re", run_rti, aonly, "reencode")]:
    t0 = time.time(); res[tag] = fn(m, mode); res[tag]["wall_s"] = time.time() - t0
    print(tag, json.dumps({k: round(v, 4) for k, v in res[tag].items() if isinstance(v, float)}), flush=True)

res["delta_rti_sp_pct"] = 100.0 * (res["rti_sp"]["rmse_mean"] - res["oracle_sched"]["rmse_mean"]) / res["oracle_sched"]["rmse_mean"]
res["delta_rti_re_pct"] = 100.0 * (res["rti_re"]["rmse_mean"] - res["oracle_reencode"]["rmse_mean"]) / res["oracle_reencode"]["rmse_mean"]
print("Delta_RTI_SP_pct =", round(res["delta_rti_sp_pct"], 2), flush=True)
print("Delta_RTI_RE_pct =", round(res["delta_rti_re_pct"], 2), flush=True)

outp = OUT if not args.tag else OUT.replace(".json", f"{args.tag}.json")
with open(outp, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2, default=str)
print("saved", outp, flush=True)
