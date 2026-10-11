# -*- coding: utf-8 -*-
"""Gate 4: control scenario evaluation in OFFLINE CLOSED-LOOP SIMULATION.

Honesty frame (plan section 6):
  * this is closed-loop SIMULATION: the controller output drives a simulated
    plant's next state -- it is NOT a real hardware experiment;
  * the plant is a separately trained model of a DIFFERENT family from every
    controller's internal model (plant A = M3 GRU, plant B = M6 Transformer);
  * every conclusion is scoped to the plant used, and each plant's own Gate-1
    test rollout RMSE is quoted with the results;
  * offline QP solve time is NOT the closed-loop period.

Controllers (plan section 7.2):
  C0  fixed linear model (A0,B0 of the trained scheduled model) + LTI-MPC
  C1  M4  A(c)+B0   + frozen-schedule LTV-MPC
  C2  M5  A(c)+B(x) + frozen-schedule LTV-MPC

Run:  python scripts/run_gate4.py --split val --search
      python scripts/run_gate4.py --split test
"""
from __future__ import annotations

import argparse
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

import protocol as proto                                     # noqa: E402
import run_gate1 as g1                                       # noqa: E402
from ltv_mpc import ScheduledLTVMPC, LTIMPC                   # noqa: E402

RESULTS = os.path.join(EXP, "results", "control")
os.makedirs(RESULTS, exist_ok=True)

U_LOWER = np.array([-3.584351, -3.552817])
U_UPPER = np.array([3.567328, 3.559557])
U_PHYS = 100.0
CTRL = {"C0": ("M4", LTIMPC), "C1": ("M4", ScheduledLTVMPC), "C2": ("M5", ScheduledLTVMPC)}
PLANTS = {"plant_A_M3_GRU": "M3", "plant_B_M6_Transformer": "M6"}
P = proto.P


# ------------------------------------------------------------------ scenarios
def build_scenarios(split, n_setpoint=3, n_tracking=3, traj_len=300):
    """Scenario definitions. Targets come from the TRAIN split only (no test leakage)."""
    x_tr, _, _ = proto.load_split("train")
    xn_tr, _ = proto.normalise(x_tr, np.zeros_like(x_tr))
    med = np.median(xn_tr, axis=0)
    p05, p25, p75, p95 = (np.quantile(xn_tr, q, axis=0) for q in (0.05, 0.25, 0.75, 0.95))
    targets = [med.copy(), np.array([p75[0], p25[1]]), np.array([p95[0], p05[1]])][:n_setpoint]
    amp = 0.5 * np.minimum(p95 - med, med - p05)

    x, u, tid = proto.load_split(split)
    xn, un = proto.normalise(x, u)
    n_traj = int(tid.max()) + 1
    starts = proto.frozen_starts(traj_len, 200, max(n_setpoint, n_tracking))
    scen = []
    for i, target in enumerate(targets):
        T = 100
        ref = np.tile(target, (T + 1, 1))
        scen.append({"name": "setpoint_%d" % i, "kind": "setpoint", "split": split,
                     "start": int(starts[min(i, len(starts) - 1)]), "target": target.tolist(),
                     "horizon": T, "ref": ref})
    specs = [("slow_sinusoid", 100), ("fast_sinusoid", 40), ("piecewise_setpoints", 0)]
    for j, (nm, T1) in enumerate(specs[:n_tracking]):
        T = 200
        if nm == "piecewise_setpoints":
            seg = T // 4
            ref = np.vstack([np.tile(targets[min(k // seg, len(targets) - 1)], (seg, 1))
                             for k in range(4)] + [targets[-1][None]])
        else:
            k = np.arange(T + 1)
            ref = np.stack([med[0] + amp[0] * np.sin(2 * np.pi * k / T1),
                            med[1] + amp[1] * np.cos(2 * np.pi * k / T1)], axis=1)
        scen.append({"name": nm, "kind": "tracking", "split": split,
                     "start": int(starts[min(j, len(starts) - 1)]), "horizon": T, "ref": ref})
    return scen, {"targets": [t.tolist() for t in targets], "amplitude": amp.tolist(),
                  "median": med.tolist()}


def history_at(split, start):
    """True history window ending at ``start`` (normalised)."""
    x, u, tid = proto.load_split(split)
    xn, un = proto.normalise(x, u)
    xh = np.stack([xn[start - P + 1:start + 1]])
    uin = np.stack([un[start - P + 1:start]])
    return (torch.as_tensor(xh, dtype=torch.float32),
            torch.as_tensor(uin, dtype=torch.float32))


# ------------------------------------------------------------------ closed loop
def run_scenario(plant, controller, scen, N):
    xh, uin = history_at(scen["split"], scen["start"])
    u_prev = uin[0, -1].numpy().copy()
    ref = scen["ref"]
    T = scen["horizon"]
    xs, us, times, fails = [], [], [], []
    for k in range(T):
        win = ref[k:min(k + N + 1, T + 1)]
        if win.shape[0] < N + 1:                     # documented clamp at the end
            win = np.vstack([win, np.tile(win[-1], (N + 1 - win.shape[0], 1))])
        u0, U, info = controller.step(xh.numpy(), uin.numpy(), u_prev, win)
        times.append(info.get("run_time", np.nan) * 1e3)
        fails.append(0 if info.get("solved", False) else 1)
        with torch.no_grad():
            xn = plant.predict(xh, uin, torch.as_tensor(u0[None], dtype=torch.float32))
        xs.append(xn[0].numpy().copy())
        us.append(u0.copy())
        xh = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
        uin = torch.cat([uin[:, 1:, :], torch.as_tensor(u0[None, None], dtype=torch.float32)],
                        dim=1)
        u_prev = u0
    X = np.asarray(xs)
    U = np.asarray(us)
    R = ref[1:T + 1]
    return X, U, R, np.asarray(times), int(np.sum(fails))


def metrics(X, U, R, times, fails, kind, target=None, dt=0.2):
    e = X - R
    m = {"rmse": float(np.sqrt(np.mean(e ** 2))), "mae": float(np.mean(np.abs(e))),
         "max_error": float(np.max(np.abs(e))),
         "control_energy": float(np.sum(U ** 2)),
         "input_variation": float(np.sum(np.diff(U, axis=0) ** 2)) if len(U) > 1 else 0.0,
         "constraint_violations": int(np.sum((U < U_LOWER - 1e-6) | (U > U_UPPER + 1e-6))),
         "solve_failures": fails,
         "solve_ms_median": float(np.median(times)),
         "solve_ms_p95": float(np.quantile(times, 0.95)),
         "solve_ms_p99": float(np.quantile(times, 0.99))}
    if kind == "setpoint":
        tail = slice(int(0.8 * len(X)), len(X))
        ss = float(np.mean(np.abs(X[tail] - R[tail])))
        m["steady_state_error"] = ss
        err = np.linalg.norm(e, axis=1)
        band = 0.02 * max(np.linalg.norm(R[0]), 1e-9)
        idx = np.where(err <= band)[0]
        m["settling_time_steps"] = int(idx[0]) if len(idx) else -1
        peak = np.max(np.linalg.norm(X - R[0], axis=1))
        m["overshoot_pct"] = float(100.0 * max(peak - np.linalg.norm(R[0]), 0.0)
                                   / max(np.linalg.norm(R[0]), 1e-9))
    else:
        m["phase_lag_steps"] = _phase_lag(X, R)
    return m


def _phase_lag(X, R):
    """Best integer lag (in steps) minimising the RMSE between X and shifted R."""
    best, bl = None, 0
    for lag in range(0, 15):
        if lag == 0:
            d = X - R
        else:
            d = X[lag:] - R[:-lag]
        v = float(np.sqrt(np.mean(d ** 2)))
        if best is None or v < best:
            best, bl = v, lag
    return bl


# ------------------------------------------------------------------ main
def load_models(ledger, seed=0):
    out = {}
    for spec in ("M3", "M4", "M5", "M6"):
        cfg = ledger["best"][spec]["cfg"]
        m, _ = g1.make_train_rollout(spec, cfg, seed=seed)
        m.eval()
        out[spec] = m
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test", choices=["val", "test"])
    ap.add_argument("--search", action="store_true",
                    help="run the sensitivity study on validation scenarios")
    ap.add_argument("--N", type=int, default=10)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    ledger = json.load(open(os.path.join(EXP, "results", "modeling", "gate1_ledger.json"),
                            encoding="utf-8"))
    models = load_models(ledger, seed=args.seed)
    scen, meta = build_scenarios(args.split)
    print("split=%s scenarios=%s" % (args.split, [s["name"] for s in scen]))

    plant_fidelity = {}
    for pname, spec in PLANTS.items():
        t = ledger.get("test", {}).get(spec)
        plant_fidelity[pname] = (None if not t else
                                 {"roll5": float(np.mean([r["test"]["rollout"]["short"] for r in t])),
                                  "roll25": float(np.mean([r["test"]["rollout"]["mid"] for r in t])),
                                  "roll100": float(np.mean([r["test"]["rollout"]["long"] for r in t])),
                                  "one_step": float(np.mean([r["test"]["one_step"]["short"] for r in t]))})
        print("  plant %s (%s) fidelity: %s" % (pname, spec, plant_fidelity[pname]))

    settings = [("default", 1.0, 1e-3, 1e-2)]
    if args.search:
        settings = [("default", 1.0, 1e-3, 1e-2), ("loose_R", 1.0, 1e-4, 1e-2),
                    ("tight_R", 1.0, 1e-2, 1e-2), ("more_rate", 1.0, 1e-3, 1e-1),
                    ("N5", 1.0, 1e-3, 1e-2), ("N20", 1.0, 1e-3, 1e-2)]
        print("\nsensitivity settings (applied IDENTICALLY to every controller): %s"
              % [s[0] for s in settings])

    out = {"split": args.split, "scenario_meta": meta, "plant_fidelity": plant_fidelity,
           "u_limit_physical_assumed": U_PHYS,
           "frame": ("offline closed-loop simulation; the plant is a separately trained "
                     "model; no hardware experiment was performed"),
           "runs": {}, "sensitivity": {}, "started": time.strftime("%Y-%m-%d %H:%M:%S")}

    for setting, q, r, s in settings:
        N = 5 if setting == "N5" else (20 if setting == "N20" else args.N)
        key = setting
        out["runs"].setdefault(key, {})
        print("\n=== setting=%s  N=%d  R=%.0e  S=%.0e ===" % (setting, N, r, s))
        for pname, pspec in PLANTS.items():
            plant = models[pspec]
            for cname, (mspec, cls) in CTRL.items():
                ctrl = cls(models[mspec], N=N, Q=q * np.eye(2), P_term=q * np.eye(2),
                           R=r * np.eye(2), S=s * np.eye(2),
                           u_min=U_LOWER, u_max=U_UPPER)
                for sc in scen:
                    X, U, R, times, fails = run_scenario(plant, ctrl, sc, N)
                    mm = metrics(X, U, R, times, fails, sc["kind"])
                    out["runs"][key].setdefault(pname, {}).setdefault(cname, {})[sc["name"]] = mm
                    print("  %-22s %-3s %-20s rmse=%.4f ss=%.4f e=%.3g viol=%d fail=%d ms=%.2f"
                          % (pname, cname, sc["name"], mm["rmse"],
                             mm.get("steady_state_error", float("nan")),
                             mm["control_energy"], mm["constraint_violations"],
                             mm["solve_failures"], mm["solve_ms_median"]))
                    out["runs"][key][pname][cname][sc["name"]]["_traj"] = {
                        "X": X.tolist(), "U": U.tolist()}

    out["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    name = "control_%s%s.json" % (args.split, "_search" if args.search else "")
    with io.open(os.path.join(RESULTS, name), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False)
    print("\nwritten -> %s" % os.path.join(RESULTS, name))


if __name__ == "__main__":
    main()
