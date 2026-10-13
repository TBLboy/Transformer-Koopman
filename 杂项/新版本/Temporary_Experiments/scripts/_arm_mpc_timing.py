# -*- coding: utf-8 -*-
"""Measure the per-control-step cost of the arm MPC (N=50) before sizing scenarios."""
import os
import sys
import time

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "models"))
sys.path.insert(0, os.path.join(EXP, "controllers"))
sys.path.insert(0, HERE)

import device as dev                       # noqa: E402
dev.bootstrap_from_argv()

import protocol as proto                   # noqa: E402
from library import build_model            # noqa: E402
from ltv_mpc import ScheduledLTVMPC        # noqa: E402

D = dev.current()
N_STATE, N_CTRL = proto.N, proto.M
print("device=%s N=%d n=%d m=%d" % (D["name"], D["mpc_N"], N_STATE, N_CTRL))

# controller internal model (architecture only; timing does not depend on weights)
ctrl_model = build_model("M5", seed=0, r_A=3, r_B=3, g_A=0.2, g_B=0.2)
ctrl_model.eval()
# plant stand-in (different family), also architecture only
plant = build_model("M3", seed=0)
plant.eval()

rng = np.random.default_rng(0)
xh = torch.as_tensor(rng.normal(scale=0.3, size=(1, proto.P, N_STATE)), dtype=torch.float32)
uin = torch.as_tensor(rng.normal(scale=0.5, size=(1, proto.P - 1, N_CTRL)), dtype=torch.float32)
x_ref = np.zeros((D["mpc_N"] + 1, N_STATE))
lo, hi = dev.u_limits_normalised()

for N in (D["mpc_N"],) + tuple(int(v) for v in D["mpc_N_sensitivity"]):
    mpc = ScheduledLTVMPC(ctrl_model, N=N, Q=np.eye(N_STATE), P_term=np.eye(N_STATE),
                          R=1e-3 * np.eye(N_CTRL), S=1e-2 * np.eye(N_CTRL),
                          u_min=lo, u_max=hi)
    u_prev = np.zeros(N_CTRL)
    t0 = time.time()
    n_steps = 20
    for k in range(n_steps):
        u0, U, info = mpc.step(xh.numpy(), uin.numpy(), u_prev, x_ref)
        u_prev = u0
    dt = (time.time() - t0) / n_steps
    print("  N=%-4d per MPC step = %.1f ms  ->  setpoint 500 steps = %.1f s, "
          "tracking 1000 steps = %.1f s" % (N, dt * 1e3, dt * 500, dt * 1000))

# plant step cost
with torch.no_grad():
    t0 = time.time()
    for k in range(200):
        plant.rollout(xh, uin, torch.zeros(1, 1, N_CTRL))
    print("  plant rollout 1 step = %.2f ms" % ((time.time() - t0) / 200 * 1e3))

print("\nBUDGET: combos = 2 plants x 3 controllers x 8 settings = 48 scenario-runs;")
