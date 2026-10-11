# -*- coding: utf-8 -*-
"""Gate 2: new-model effectiveness diagnostics.

E-M3 structural ablation (paired: identical encoder, window, latent dim, loss and
     optimisation budget; only the scheduling branch changes):
         A0+B0 (M_base) | A(c)+B0 (M4) | A0+B(x) (M7) | A(c)+B(x) (M5)
E-M4 capacity / budget matching: enlarge the A(c)+B0 variant until its parameter
     count matches M5's, so a parameter increase cannot be mistaken for a
     scheduling-structure gain.
E-M5 scheduling diagnostics: ||A(c)-A0||_2, ||B(x)-B0||_2, effective rank, gamma
     distribution and measurement-dependent input response.

Negative results are kept (plan section 11, Gate 2).

Run:  python scripts/run_gate2.py --seeds 3
"""
from __future__ import annotations

import argparse
import gc
import io
import json
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

import run_gate1 as g1                      # noqa: E402
from library import build_model, n_params, ScheduledKoopman   # noqa: E402

RESULTS = os.path.join(EXP, "results", "modeling")
os.makedirs(RESULTS, exist_ok=True)
VARIANTS = [("A0B0", "M_base"), ("AcB0", "M4"), ("A0Bx", "M7"), ("AcBx", "M5")]


def paired_cfg(cfg):
    """One shared config for all four variants (E-M3 pairing requirement)."""
    keys = ("r_A", "r_B", "g_A", "g_B", "d_model", "n_layers", "n_heads", "d_ff",
            "dropout", "lr", "w_roll", "roll_h", "epochs")
    out = {k: cfg[k] for k in keys if k in cfg}
    out.setdefault("r_A", 3)
    out.setdefault("r_B", 3)
    out.setdefault("g_A", 0.1)
    out.setdefault("g_B", 0.1)
    return out


def train_and_eval(spec, cfg, seed):
    model, info = g1.make_train_rollout(spec, cfg, seed=seed)
    ev = g1.eval_all(model, "test")
    return model, ev, info


def scheduling_diagnostics(model, split="test", n_batch=30):
    """E-M5 diagnostics on the frozen mid-horizon test starts."""
    w, _ = g1.tensors(split, 25, frozen_eval=True)
    idx = np.arange(min(n_batch, len(w["k"])))
    xh = g1.batchify(w, "Xh", idx)
    uin = g1.batchify(w, "Uin", idx)
    out = model.diagnostics(xh, uin)
    # effective rank of the scheduling deviation and measurement-dependent input response
    with torch.no_grad():
        c = model.ctx(xh, uin)
        z = model.encoder(xh)
        A = model.A_of(c)
        B = model.B_of(z[:, :2])
        dA = (A - model.A0.unsqueeze(0)).cpu().numpy()
        sv = np.linalg.svd(dA.reshape(len(idx), -1), compute_uv=False)
        sv = sv / max(sv[0], 1e-12)
        out["dA_effective_rank_90pct"] = int(np.searchsorted(np.cumsum(sv ** 2)
                                                             / np.sum(sv ** 2), 0.9) + 1)
        out["dA_rank_numerical"] = int(np.sum(sv > 1e-6))
        # same input, different measured state -> how different is B(x)u ?
        u = torch.tensor([[1.0, 1.0]], device=B.device)
        rels = []
        for i in range(0, len(idx) - 1, 2):
            b1 = B[i] @ u[0]
            b2 = B[i + 1] @ u[0]
            denom = max(float(torch.norm(b1)), 1e-9)
            rels.append(float(torch.norm(b2 - b1)) / denom)
        out["Bx_response_rel_diff_mean"] = float(np.mean(rels)) if rels else 0.0
        out["Bx_response_rel_diff_max"] = float(np.max(rels)) if rels else 0.0
        out["A0_spectral_radius"] = float(torch.linalg.eigvals(model.A0).abs().max())
        out["B0_fro"] = float(model.B0.norm())
    return out


def capacity_match(target_params, base_cfg, spec="M4", tol=0.05):
    """Find (d_model, r_A) for the A(c)+B0 variant closest to M5's parameter count."""
    cands = []
    for d_model in (16, 24, 32, 48, 64, 96):
        for r_A in (1, 2, 3, 5, 8, 12, 20):
            cfg = dict(base_cfg)
            cfg.update({"d_model": d_model, "r_A": r_A})
            m = build_model(spec, seed=0, **{k: v for k, v in cfg.items()
                                             if k not in ("lr", "epochs", "w_roll", "roll_h")})
            p = n_params(m)
            cands.append({"d_model": d_model, "r_A": r_A, "params": p,
                          "rel_err": abs(p - target_params) / target_params})
            del m
    cands.sort(key=lambda r: r["rel_err"])
    ok = [c for c in cands if c["rel_err"] <= tol]
    return (ok[0] if ok else cands[0]), cands[:5]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--n-batch", type=int, default=30)
    args = ap.parse_args()

    ledger = json.load(open(os.path.join(RESULTS, "gate1_ledger.json"), encoding="utf-8"))
    m5_best = ledger["best"]["M5"]["cfg"]
    cfg = paired_cfg(m5_best)
    print("paired E-M3 config (from M5's selected config): %s" % cfg)

    report = {"paired_cfg": cfg, "source": "gate1_ledger.json best['M5']",
              "em3": {}, "em4": {}, "em5": {}, "started": time.strftime("%Y-%m-%d %H:%M:%S")}

    # ---------------------------------------------------------------- E-M3
    models = {}
    for variant, spec in VARIANTS:
        print("\n=== E-M3 %s (%s) x %d seeds ===" % (variant, spec, args.seeds))
        runs = []
        for s in range(args.seeds):
            t0 = time.time()
            model, ev, info = train_and_eval(spec, cfg, seed=s)
            runs.append({"seed": s, "test": ev, "params": n_params(model),
                         "info": info, "seconds": time.time() - t0})
            print("  seed %d  one-step=%.6f roll5=%.6f roll25=%.6f roll100=%.6f params=%d %.0fs"
                  % (s, ev["one_step"]["short"], ev["rollout"]["short"], ev["rollout"]["mid"],
                     ev["rollout"]["long"], n_params(model), time.time() - t0))
            if s == 0:
                models[variant] = model
            g1.free()
        report["em3"][variant] = runs

    # summary: mean +/- std of the mid-horizon rollout RMSE
    for variant, _ in VARIANTS:
        v = [r["test"]["rollout"]["mid"] for r in report["em3"][variant]]
        report["em3"].setdefault("summary", {})[variant] = {
            "roll25_mean": float(np.mean(v)), "roll25_std": float(np.std(v)),
            "roll100_mean": float(np.mean([r["test"]["rollout"]["long"]
                                           for r in report["em3"][variant]])),
            "one_step_mean": float(np.mean([r["test"]["one_step"]["short"]
                                            for r in report["em3"][variant]])),
            "params": report["em3"][variant][0]["params"]}

    # ---------------------------------------------------------------- E-M5
    print("\n=== E-M5 scheduling diagnostics ===")
    for variant in ("A0B0", "AcB0", "A0Bx", "AcBx"):
        d = scheduling_diagnostics(models[variant], n_batch=args.n_batch)
        report["em5"][variant] = d
        print("  %-5s dA_spec_max=%.4f dB_spec_max=%.4f rho_A_max=%.4f rank90=%d Bx_rel=%.3f"
              % (variant, d.get("A_dev_spec_max", 0.0), d.get("B_dev_spec_max", 0.0),
                 d.get("rho_A_max", 0.0), d.get("dA_effective_rank_90pct", 0),
                 d.get("Bx_response_rel_diff_mean", 0.0)))

    # ---------------------------------------------------------------- E-M4
    print("\n=== E-M4 capacity matching (A(c)+B0 enlarged to M5's parameter count) ===")
    target = report["em3"]["summary"]["AcBx"]["params"]
    best, top = capacity_match(target, cfg, spec="M4")
    print("  M5 params=%d ; matched AcB0: %s (top-5 %s)" % (target, best, top))
    report["em4"]["target_params"] = target
    report["em4"]["selected"] = best
    report["em4"]["candidates_top5"] = top
    cfg4 = dict(cfg)
    cfg4.update({"d_model": best["d_model"], "r_A": best["r_A"]})
    runs = []
    for s in range(args.seeds):
        model, ev, info = train_and_eval("M4", cfg4, seed=s)
        runs.append({"seed": s, "test": ev, "params": n_params(model), "info": info})
        print("  matched seed %d  roll25=%.6f roll100=%.6f params=%d"
              % (s, ev["rollout"]["mid"], ev["rollout"]["long"], n_params(model)))
        g1.free()
    report["em4"]["matched_AcB0"] = runs
    report["em4"]["matched_summary"] = {
        "roll25_mean": float(np.mean([r["test"]["rollout"]["mid"] for r in runs])),
        "roll25_std": float(np.std([r["test"]["rollout"]["mid"] for r in runs])),
        "params": runs[0]["params"]}

    report["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    out = os.path.join(RESULTS, "gate2_diagnostics.json")
    with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print("\nwritten -> %s" % out)


if __name__ == "__main__":
    main()
