# -*- coding: utf-8 -*-
"""Diagnose M1 (EDMDc) divergence on the arm: is it a ridge/search-space artifact?"""
import io
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "models"))
sys.path.insert(0, HERE)

import device as dev                       # noqa: E402
dev.bootstrap_from_argv()

import protocol as proto                   # noqa: E402
import run_gate1 as g1                     # noqa: E402
from library import build_model            # noqa: E402

D = dev.current()
out = []
print("device=%s  n_state=%d n_ctrl=%d" % (D["name"], proto.N, proto.M))

x_tr, u_tr, tid_tr = proto.load_split("train")
va, _ = g1.tensors("val", proto.SELECTION_HORIZON, stride=4)
vidx = np.arange(len(va["k"]))

# reference: trivial "no change" predictor on the same validation windows
tgt = g1.batchify(va, "XF", vidx)
last = g1.batchify(va, "Xh", vidx)[:, -1:, :].expand_as(tgt)
triv = float(torch.sqrt(torch.mean((last - tgt) ** 2)))
print("trivial 'no-change' val roll25 RMSE = %.6f" % triv)
print()

for n_rbf in (0, 64):
    for ridge in (1e-8, 1e-6, 1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0):
        try:
            m = build_model("M1", seed=0, n_rbf=n_rbf, sigma=1.0, ridge=ridge)
            m.fit(x_tr, u_tr, tid_tr)
            Lx = int(m.lift(torch.zeros(1, proto.N)).shape[1])
            Amat = m.A[:, :Lx].detach().numpy()
            rho = float(np.max(np.abs(np.linalg.eigvals(Amat))))
            cond = float(np.linalg.cond(Amat))
            v = g1.rollout_metric(m, va, proto.SELECTION_HORIZON, vidx)
            one = g1.one_step_metric(m, va, vidx)
            print("n_rbf=%-3d ridge=%-6g  lift=%d  rho(A)=%-10.4f cond=%-10.3g "
                  "one_step=%-12.6g roll25=%s"
                  % (n_rbf, ridge, Lx, rho, cond, one,
                     ("%.6g" % v) if np.isfinite(v) else "NON-FINITE"))
            out.append({"n_rbf": n_rbf, "ridge": ridge, "lift": Lx, "rho_A": rho,
                        "cond": cond, "one_step": one,
                        "roll25": v if np.isfinite(v) else None})
        except Exception as exc:                                     # noqa: BLE001
            print("n_rbf=%-3d ridge=%-6g  FAILED %r" % (n_rbf, ridge, exc))
        g1.free()

p = os.path.join(dev.results_dir("modeling"), "m1_ridge_probe.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
import json
with io.open(p, "w", encoding="utf-8", newline="\n") as fh:
    json.dump({"trivial_no_change_roll25": triv, "rows": out}, fh, ensure_ascii=False, indent=1)
print("\nwritten -> %s" % p)
