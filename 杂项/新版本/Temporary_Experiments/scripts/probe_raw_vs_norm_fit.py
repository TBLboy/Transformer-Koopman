# -*- coding: utf-8 -*-
"""A/B: fit the closed-form models on RAW units (current code) vs NORMALISED units.

Both are evaluated on the SAME normalised validation windows, so the difference
isolates the unit mismatch in ``run_gate1.train_one`` (``tr["_raw"]`` is raw).
"""
import io
import json
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
print("=" * 78)
print("device=%s  n=%d m=%d dt=%g" % (D["name"], proto.N, proto.M, proto.DT))

va, _ = g1.tensors("val", proto.SELECTION_HORIZON, stride=4)
vidx = np.arange(len(va["k"]))
tgt = g1.batchify(va, "XF", vidx)
Xh = g1.batchify(va, "Xh", vidx)
triv_one = float(torch.sqrt(torch.mean((Xh[:, -1:, :] - tgt[:, :1, :]) ** 2)))
triv_r25 = float(torch.sqrt(torch.mean((Xh[:, -1:, :].expand_as(tgt) - tgt) ** 2)))
print("  trivial no-change: one-step=%.6f roll25=%.6f" % (triv_one, triv_r25))

x_raw, u_raw, tid = proto.load_split("train")
xn, un = proto.normalise(x_raw, u_raw)

CFGS = {
    "M0": {"delay": 1},
    "M1": {"n_rbf": 0, "sigma": 0.5, "ridge": 1e-8},
    "M1rbf": {"n_rbf": 64, "sigma": 1.0, "ridge": 1e-6},
}

res = {}
for name, cfg in CFGS.items():
    spec = "M0" if name == "M0" else "M1"
    for units, (xx, uu) in (("raw", (x_raw, u_raw)), ("norm", (xn, un))):
        m = build_model(spec, seed=0, **cfg)
        m.fit(xx, uu, tid)
        one = g1.one_step_metric(m, va, vidx)
        r25 = g1.rollout_metric(m, va, proto.SELECTION_HORIZON, vidx)
        res["%s_%s" % (name, units)] = {"one_step": one, "roll25": r25}
        print("  %-6s fit=%-5s  one-step=%-12.6g roll25=%s"
              % (name, units, one, ("%.6g" % r25) if np.isfinite(r25) else "NON-FINITE"))
        g1.free()

p = os.path.join(dev.results_dir("modeling"), "probe_raw_vs_norm_fit.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
with io.open(p, "w", encoding="utf-8", newline="\n") as fh:
    json.dump({"device": D["name"], "trivial": {"one_step": triv_one, "roll25": triv_r25},
               "rows": res}, fh, ensure_ascii=False, indent=1)
print("written -> %s" % p)
