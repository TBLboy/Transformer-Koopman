import sys, os, numpy as np, torch
sys.path.insert(0, r"C:\Users\12187\AppData\Local\Temp\opencode")
import gate14c_control as G
from gate_context_koopman import build_split
from scipy.optimize import minimize
DEV = G.DEV
trXH, trUH, trUT, trXN, NORM = build_split(G.DATA_DIR, "train", G.CFG)
fixed = G.CtxKoopman(G.CFG, "fixed").to(DEV)
fixed.load_state_dict(torch.load(os.path.join(G.STATE, "fixed.pt"), map_location=DEV)); fixed.eval()
d = np.load(os.path.join(G.DATA_DIR, "val.npz")); trd = np.load(os.path.join(G.DATA_DIR, "train.npz"))
x = (d["x"] - trd["x"].mean(0)) / (trd["x"].std(0) + 1e-8); u = (d["u"] - trd["u"].mean(0)) / (trd["u"].std(0) + 1e-8)
P, N, M = G.P, G.N, G.M
xh = torch.tensor(x[:P], dtype=torch.float32).to(DEV); uh = torch.tensor(u[:P - 1], dtype=torch.float32).to(DEV)
ref = torch.tensor(x[1:1 + N], dtype=torch.float32).to(DEV); u_prev = torch.tensor(u[P - 1], dtype=torch.float32).to(DEV)

def cost(Unp):
    U = torch.tensor(Unp.reshape(N, M), dtype=torch.float32).to(DEV)
    pred = G.predict(fixed, xh, uh, U, "reencode")
    c = G.Q * ((pred - ref) ** 2).sum() + G.R * (U ** 2).sum()
    du = torch.cat([U[:1] - u_prev.unsqueeze(0), U[1:] - U[:-1]], 0)
    c = c + G.S * (du ** 2).sum()
    return c.item()

U0 = np.tile(u_prev.detach().cpu().numpy(), (N, 1)).ravel()
print("cost x0   ", round(cost(U0), 6))
print("cost +0.5 ", round(cost(U0 + 0.5), 6))
print("cost -0.5 ", round(cost(U0 - 0.5), 6))
print("cost ref-u", round(cost(np.tile(u[P:P + N], (1, 1)).ravel()), 6))
r = minimize(cost, U0, method="SLSQP", bounds=[(G.UMIN, G.UMAX)] * (N * M), options={"maxiter": 30, "ftol": 1e-6, "eps": 1e-3})
print("success", r.success, "nit", r.nit, "fun", round(r.fun, 6), "msg", r.message)
print("U0[:4]", np.round(U0[:4], 3), "r.x[:4]", np.round(r.x[:4], 3))
print("u_prev", u_prev.cpu().numpy(), "u_ref window", np.round(u[P:P + 4], 3))
