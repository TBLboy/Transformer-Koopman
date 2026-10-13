# -*- coding: utf-8 -*-
"""Quantify the raw-vs-normalised fit bug for M0/M1 on both devices.

Compares, on the SAME normalised validation windows:
  * the trivial 'no-change' predictor,
  * the ledger's closed-form models M0/M1/M2.
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

D = dev.current()
print("=" * 78)
print("device=%s  (n=%d m=%d dt=%g)" % (D["name"], proto.N, proto.M, proto.DT))

va, _ = g1.tensors("val", proto.SELECTION_HORIZON, stride=4)
vidx = np.arange(len(va["k"]))
tgt = g1.batchify(va, "XF", vidx)
Xh = g1.batchify(va, "Xh", vidx)
triv_one = float(torch.sqrt(torch.mean((Xh[:, -1:, :] - tgt[:, :1, :]) ** 2)))
triv_r25 = float(torch.sqrt(torch.mean((Xh[:, -1:, :].expand_as(tgt) - tgt) ** 2)))
print("  trivial no-change:  one-step=%.6f   roll25=%.6f" % (triv_one, triv_r25))

x_tr, u_tr, tid_tr = proto.load_split("train")
for spec in ("M0", "M1", "M2"):
    cfg = None
    led_path = os.path.join(dev.results_dir("modeling"), "gate1_ledger.json")
    led = json.load(io.open(led_path, encoding="utf-8")) if os.path.exists(led_path) else {}
    b = (led.get("best") or {}).get(spec)
    if not b:
        print("  %-3s : no selected config in the ledger" % spec)
        continue
    cfg = b["cfg"]
    model, info = g1.make_train_rollout(spec, cfg, seed=0)
    one = g1.one_step_metric(model, va, vidx)
    r25 = g1.rollout_metric(model, va, proto.SELECTION_HORIZON, vidx)
    print("  %-3s : val one-step=%.6f  roll25=%s   cfg=%s"
          % (spec, one, ("%.6f" % r25) if np.isfinite(r25) else "NON-FINITE",
             json.dumps(cfg, ensure_ascii=False)))
    g1.free()
print("=" * 78)
