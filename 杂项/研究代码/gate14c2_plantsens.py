import sys, os, numpy as np, torch
sys.path.insert(0, r"C:\Users\12187\AppData\Local\Temp\opencode")
import gate14c_control as G
from gate14c_control import run_closed_loop
from gate14_directnn import train as train_dnn
from gate_context_koopman import build_split

DEV = G.DEV; STATE = G.STATE; CFG = G.CFG; DATA_DIR = G.DATA_DIR
trXH, trUH, trUT, trXN, NORM = build_split(DATA_DIR, "train", CFG)
dnn, _ = train_dnn(trXH, trUH, trUT, trXN, epochs=100); dnn.eval()
fixed = G.CtxKoopman(CFG, "fixed").to(DEV); fixed.load_state_dict(torch.load(os.path.join(STATE, "fixed.pt"), map_location=DEV)); fixed.eval()
aonly = G.CtxKoopman(CFG, "A", r=2).to(DEV); aonly.load_state_dict(torch.load(os.path.join(STATE, "A_r2.pt"), map_location=DEV)); aonly.eval()
d = np.load(os.path.join(DATA_DIR, "val.npz")); trd = np.load(os.path.join(DATA_DIR, "train.npz"))
x = (d["x"] - trd["x"].mean(0)) / (trd["x"].std(0) + 1e-8); u = (d["u"] - trd["u"].mean(0)) / (trd["u"].std(0) + 1e-8)
tid = d["trajectory_id"]; t = list(np.unique(tid))[0]; idx = np.where(tid == t)[0][:30]
print("plant | C0_fixed | C2_aonly  (tracking RMSE, re-encoding MPC)")
for pname, plant in [("dnn", dnn), ("aonly", aonly), ("fixed", fixed)]:
    row = []
    for cname, m in [("C0", fixed), ("C2", aonly)]:
        r, med, p95 = run_closed_loop(m, "reencode", plant, x[idx], u[idx])
        row.append(round(r, 4))
    print(f"{pname:8s} | {row[0]} | {row[1]}")
