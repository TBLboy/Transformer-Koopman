# -*- coding: utf-8 -*-
"""Gate 1 driver: train M0-M6 under the frozen protocol, select on validation,
then evaluate once on the test split.

Stages (plan section 4.2): pilot -> formal search -> multi-seed final -> test.

Usage:
    python scripts/run_gate1.py --stage pilot  --models M0 M1 M2 M3 M4 M5 M6
    python scripts/run_gate1.py --stage formal --trials 12
    python scripts/run_gate1.py --stage final  --seeds 3
    python scripts/run_gate1.py --stage test

Everything is written incrementally to results/modeling/ so a long run can be
inspected (and resumed) without losing work.
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

import protocol as proto          # noqa: E402
from library import build_model, n_params   # noqa: E402

RESULTS = os.path.join(EXP, "results", "modeling")
CKPT = os.path.join(EXP, "checkpoints")
os.makedirs(RESULTS, exist_ok=True)
os.makedirs(CKPT, exist_ok=True)

DEV = "cuda" if torch.cuda.is_available() else "cpu"


def free():
    """Release host/GPU memory between trials (16 GB host RAM on this box)."""
    gc.collect()
    if DEV == "cuda":
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

ALL_MODELS = ["M0", "M1", "M2", "M3", "M4", "M5", "M6"]

# ------------------------------------------------------------------ search spaces
def search_space(spec, trial, rng):
    """Method-specific search space (plan section 4.3)."""
    if spec == "M0":
        return {"delay": int(rng.choice([0, 1, 2]))}
    if spec == "M1":
        return {"n_rbf": int(rng.choice([0, 0, 32, 64])),
                "sigma": float(rng.choice([0.5, 1.0, 2.0])),
                "ridge": float(rng.choice([1e-8, 1e-6, 1e-4]))}
    if spec == "M2":
        return {"d_lift": int(rng.choice([8, 16, 32])),
                "hidden": int(rng.choice([16, 32, 64])),
                "ridge": float(rng.choice([1e-8, 1e-6, 1e-4])),
                "lr": float(rng.choice([1e-3, 3e-3])),
                "epochs": int(rng.choice([40, 80]))}
    if spec == "M3":
        return {"cell": str(rng.choice(["gru", "lstm"])),
                "hidden": int(rng.choice([32, 64, 128])),
                "layers": int(rng.choice([1, 2])),
                "lr": float(rng.choice([1e-3, 3e-3])),
                "w_roll": float(rng.choice([0.0, 1.0, 5.0])),
                "roll_h": int(rng.choice([5, 10]))}
    if spec in ("M4", "M5", "M7"):
        return {"r_A": int(rng.choice([1, 2, 3, 5])),
                "r_B": int(rng.choice([1, 2, 3, 5])),
                "g_A": float(rng.choice([0.02, 0.1, 0.3])),
                "g_B": float(rng.choice([0.02, 0.1, 0.3])),
                "d_model": int(rng.choice([16, 32])),
                "n_layers": int(rng.choice([1, 2])),
                "lr": float(rng.choice([5e-4, 1e-3, 3e-3])),
                "w_roll": float(rng.choice([0.0, 1.0, 5.0])),
                "roll_h": int(rng.choice([5, 10, 20]))}
    if spec == "M6":
        return {"d_model": int(rng.choice([16, 32, 64])),
                "n_layers": int(rng.choice([1, 2, 3])),
                "lr": float(rng.choice([5e-4, 1e-3, 3e-3])),
                "w_roll": float(rng.choice([0.0, 1.0, 5.0])),
                "roll_h": int(rng.choice([5, 10]))}
    raise ValueError(spec)


# ------------------------------------------------------------------ data
def tensors(split, horizon, stride=None, frozen_eval=False):
    x, u, tid = proto.load_split(split)
    xn, un = proto.normalise(x, u)
    if frozen_eval:
        starts = proto.all_starts({5: "short", 25: "mid", 100: "long"}[horizon], int(tid.max()) + 1)
    else:
        starts = np.stack([proto.dense_starts(int(np.sum(tid == t)), horizon, stride or 1)
                           for t in range(int(tid.max()) + 1)])
    w = proto.make_windows(xn, un, tid, horizon, starts=starts)
    return w, (x, u, tid)


def to_t(dev=DEV):
    return dev


def batchify(w, key, idx):
    return torch.as_tensor(w[key][idx], dtype=torch.float32, device=DEV)


def rollout_metric(model, w, horizon, idx):
    """Normalised rollout RMSE over the given window indices."""
    xh = batchify(w, "Xh", idx)
    uin = batchify(w, "Uin", idx)
    uf = batchify(w, "UF", idx)
    tgt = batchify(w, "XF", idx)
    with torch.no_grad():
        pred = model.rollout(xh, uin, uf)
    return float(torch.sqrt(torch.mean((pred - tgt) ** 2)))


def one_step_metric(model, w, idx):
    xh = batchify(w, "Xh", idx)
    uin = batchify(w, "Uin", idx)
    ut = batchify(w, "Ut", idx)
    xn = batchify(w, "Xn", idx)
    with torch.no_grad():
        pred = model.predict(xh, uin, ut)
    return float(torch.sqrt(torch.mean((pred - xn) ** 2)))


# ------------------------------------------------------------------ training
def train_gradient(spec, cfg, seed, tr, va, epochs, lr, w_roll, roll_h, wd=1e-4):
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = build_model(spec, seed=seed, **{k: v for k, v in cfg.items()
                                            if k not in ("lr", "epochs", "w_roll", "roll_h")})
    model.to(DEV)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                            lr=lr, weight_decay=wd)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=6, min_lr=1e-6)
    n = len(tr["k"])
    bs = 128
    best = {"val": float("inf"), "epoch": -1, "state": None}
    hist = []
    rng = np.random.default_rng(seed)
    for ep in range(epochs):
        model.train()
        perm = rng.permutation(n)
        tot = 0.0
        nb = 0
        for s in range(0, n, bs):
            idx = perm[s:s + bs]
            if len(idx) < 8:
                continue
            xh = batchify(tr, "Xh", idx)
            uin = batchify(tr, "Uin", idx)
            ut = batchify(tr, "Ut", idx)
            xn = batchify(tr, "Xn", idx)
            loss = torch.mean((model.predict(xh, uin, ut) - xn) ** 2)
            if w_roll > 0:
                uf = batchify(tr, "UF", idx)[:, :roll_h, :]
                xf = batchify(tr, "XF", idx)[:, :roll_h, :]
                pred = model.rollout(xh, uin, uf)
                loss = loss + w_roll * torch.mean((pred - xf) ** 2)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                [p for p in model.parameters() if p.requires_grad], 5.0)
            opt.step()
            tot += float(loss)
            nb += 1
        vidx = np.arange(len(va["k"]))
        vsel = rollout_metric(model, va, 25, vidx) if len(vidx) else float("inf")
        sched.step(vsel)
        hist.append({"epoch": ep, "train": tot / max(nb, 1), "val_roll25": vsel})
        if vsel < best["val"]:
            best = {"val": vsel, "epoch": ep,
                    "state": {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}}
        if ep - best["epoch"] > 18:
            break
    if best["state"] is not None:
        model.load_state_dict(best["state"])
    return model, {"best_val_roll25": best["val"], "best_epoch": best["epoch"],
                   "epochs_run": len(hist), "history": hist[-5:]}


def train_one(spec, cfg, seed, tr, va, w_roll=0.0, roll_h=10, epochs=80, lr=1e-3):
    if spec == "M0":
        x, u, tid = tr["_raw"]
        model = build_model(spec, seed=seed, delay=cfg.get("delay", 0))
        model.fit(x, u, tid)
        return model, {"closed_form": True, "delay": cfg.get("delay", 0)}
    if spec == "M1":
        x, u, tid = tr["_raw"]
        model = build_model(spec, seed=seed, **{k: v for k, v in cfg.items()})
        model.fit(x, u, tid)
        return model, {"closed_form": True}
    if spec == "M2":
        x, u, tid = tr["_raw"]
        model = build_model(spec, seed=seed, d_lift=cfg["d_lift"], hidden=cfg["hidden"],
                            ridge=cfg["ridge"])
        model.to(DEV)
        opt = torch.optim.Adam(model.mlp.parameters(), lr=cfg.get("lr", 1e-3))
        n = len(tr["k"])
        bs = 512
        rng = np.random.default_rng(seed)
        # initial linear fit on the random dictionary
        with torch.no_grad():
            Z = model.lift(batchify(tr, "Xh", np.arange(n))[:, -1, :])
            U = batchify(tr, "Ut", np.arange(n))
            Y = model.lift(batchify(tr, "Xn", np.arange(n)))
            model.refit_linear(Z, U, Y)
        for ep in range(cfg.get("epochs", 80)):
            perm = rng.permutation(n)
            for s in range(0, n, bs):
                idx = perm[s:s + bs]
                if len(idx) < 8:
                    continue
                xh = batchify(tr, "Xh", idx)
                ut = batchify(tr, "Ut", idx)
                xn = batchify(tr, "Xn", idx)
                loss = torch.mean((model.predict(xh, None, ut) - xn) ** 2)
                opt.zero_grad(set_to_none=True)
                loss.backward()
                opt.step()
            if ep % 5 == 4:      # alternating least squares
                with torch.no_grad():
                    Z = model.lift(batchify(tr, "Xh", np.arange(n))[:, -1, :])
                    U = batchify(tr, "Ut", np.arange(n))
                    Y = model.lift(batchify(tr, "Xn", np.arange(n)))
                    model.refit_linear(Z, U, Y)
        with torch.no_grad():
            Z = model.lift(batchify(tr, "Xh", np.arange(n))[:, -1, :])
            U = batchify(tr, "Ut", np.arange(n))
            Y = model.lift(batchify(tr, "Xn", np.arange(n)))
            model.refit_linear(Z, U, Y)
        return model, {"alternating": True}
    model, info = train_gradient(spec, cfg, seed, tr, va, epochs=epochs, lr=lr,
                                 w_roll=w_roll, roll_h=roll_h)
    return model, info


# ------------------------------------------------------------------ main
def make_train_rollout(spec, cfg, seed):
    """Fit a model on the training split; returns (model, info).

    Train windows use horizon = roll_h (stride 2) for the rollout loss; the
    validation windows use H=25 (stride 4) for model selection.
    """
    horizon = max(int(cfg.get("roll_h", 10)), 5)
    tr, raw_tr = tensors("train", horizon, stride=4)
    tr["_raw"] = raw_tr
    va, _ = tensors("val", 25, stride=4)
    w_roll = float(cfg.get("w_roll", 0.0))
    model, info = train_one(spec, cfg, seed, tr, va, w_roll=w_roll,
                            roll_h=int(cfg.get("roll_h", 10)),
                            epochs=int(cfg.get("epochs", 80)),
                            lr=float(cfg.get("lr", 1e-3)))
    return model, info


def _build_for_cfg(spec, cfg, seed):
    """Construct the same architecture that ``train_one`` would train.

    Must stay in sync with ``train_one``; it exists so a saved state_dict can be
    loaded into an identically-shaped module without retraining.
    """
    if spec == "M0":
        return build_model(spec, seed=seed, delay=cfg.get("delay", 0))
    if spec == "M1":
        return build_model(spec, seed=seed, **{k: v for k, v in cfg.items()})
    if spec == "M2":
        return build_model(spec, seed=seed, d_lift=cfg["d_lift"], hidden=cfg["hidden"],
                           ridge=cfg["ridge"])
    return build_model(spec, seed=seed, **{k: v for k, v in cfg.items()
                                           if k not in ("lr", "epochs", "w_roll", "roll_h")})


CLOSED_FORM_SPECS = ("M0", "M1", "M2")


def load_or_train(spec, cfg, seed=0, save=True):
    """Load ``<spec>_seed<seed>.pt`` when present, otherwise train and save it.

    Downstream stages (control scenarios, auxiliary metrics) must use the SAME
    parameters that the Gate-1 test stage evaluated.  Retraining would normally be
    equivalent, but loading is exact and removes any CUDA-nondeterminism doubt;
    ``run_gate4`` additionally re-checks the loaded/retrained model against the
    ledger's seed-0 metrics.

    NOTE (defect found and worked around): the closed-form models M0/M1/M2 keep
    their fitted linear maps as plain attributes, not as ``nn.Parameter`` /
    buffers, so those maps are NOT part of ``state_dict``.  Loading their
    checkpoint yields ``A = None`` and crashes at prediction time.  They are
    therefore always retrained (they take < 5 s each).
    """
    path = os.path.join(CKPT, "%s_seed%d.pt" % (spec, seed))
    if spec not in CLOSED_FORM_SPECS and os.path.exists(path):
        model = _build_for_cfg(spec, cfg, seed)
        model.load_state_dict(torch.load(path, map_location="cpu"))
        model.to(DEV).eval()          # keep the same device contract as training
        return model, {"loaded": True, "path": os.path.basename(path)}
    model, info = make_train_rollout(spec, cfg, seed)
    if save and spec not in CLOSED_FORM_SPECS:
        torch.save(model.state_dict(), path)
    return model, {"loaded": False, "trained": True, "closed_form": spec in CLOSED_FORM_SPECS,
                   **info}


def eval_all(model, split="test"):
    """Full frozen evaluation on the pre-fixed start sets."""
    out = {"one_step": {}, "rollout": {}, "per_channel": {}, "curve": {}, "quantiles": {}}
    for key, H in (("short", 5), ("mid", 25), ("long", 100)):
        w, raw = tensors(split, H, frozen_eval=True)
        idx = np.arange(len(w["k"]))
        out["one_step"][key] = one_step_metric(model, w, idx)
        out["rollout"][key] = rollout_metric(model, w, H, idx)
        xh, uin, uf = batchify(w, "Xh", idx), batchify(w, "Uin", idx), batchify(w, "UF", idx)
        tgt = batchify(w, "XF", idx)
        with torch.no_grad():
            pred = model.rollout(xh, uin, uf)
        e = (pred - tgt)
        out["per_channel"][key] = torch.sqrt(torch.mean(e ** 2, dim=(0, 1))).cpu().numpy().tolist()
        out["curve"][key] = proto.horizon_curve(pred.cpu().numpy(), tgt.cpu().numpy()).tolist()
        out["quantiles"][key] = proto.quantiles(pred.cpu().numpy(), tgt.cpu().numpy())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="pilot", choices=["pilot", "formal", "final", "test", "all"])
    ap.add_argument("--models", nargs="*", default=ALL_MODELS)
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=60)
    args = ap.parse_args()

    print("device=%s cuda=%s" % (DEV, torch.cuda.is_available()))
    ledger_path = os.path.join(RESULTS, "gate1_ledger.json")
    ledger = {}
    if os.path.exists(ledger_path):
        ledger = json.load(open(ledger_path, encoding="utf-8"))
    ledger.setdefault("stage", args.stage)
    ledger.setdefault("trials", {})

    rng = np.random.default_rng(args.seed)
    todo = args.models if args.stage != "test" else list(ledger.get("best", {}).keys())
    if args.models != ALL_MODELS:
        todo = args.models

    if args.stage in ("pilot", "formal", "all"):
        n_trials = 3 if args.stage == "pilot" else args.trials
        for spec in todo:
            print("\n=== %s : %d trials (%s) ===" % (spec, n_trials, args.stage))
            runs = []
            for i in range(n_trials):
                cfg = search_space(spec, i, rng)
                cfg.setdefault("epochs", args.epochs)
                t0 = time.time()
                try:
                    model, info = make_train_rollout(spec, cfg, seed=1000 + i)
                    va, _ = tensors("val", 25, stride=4)
                    vidx = np.arange(len(va["k"]))
                    vsel = rollout_metric(model, va, 25, vidx)
                    runs.append({"trial": i, "cfg": cfg, "val_roll25": vsel,
                                 "params": n_params(model), "seconds": time.time() - t0,
                                 "info": info, "status": "ok"})
                    print("  trial %2d  val_roll25=%.6f  params=%d  %.1fs  %s"
                          % (i, vsel, n_params(model), time.time() - t0, cfg))
                except Exception as exc:      # noqa: BLE001 - record every failure
                    runs.append({"trial": i, "cfg": cfg, "status": "failed",
                                 "error": repr(exc), "seconds": time.time() - t0})
                    print("  trial %2d  FAILED: %r" % (i, exc))
                free()
                ledger["trials"].setdefault(spec, []).append(runs[-1])
                with io.open(ledger_path, "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(ledger, fh, ensure_ascii=False, indent=1)
            ok = [r for r in runs if r["status"] == "ok"]
            if ok:
                best = min(ok, key=lambda r: r["val_roll25"])
                ledger.setdefault("best", {})[spec] = best
                print("  -> best %s: val_roll25=%.6f cfg=%s" % (spec, best["val_roll25"], best["cfg"]))
            with io.open(ledger_path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(ledger, fh, ensure_ascii=False, indent=1)

    if args.stage in ("final", "all"):
        for spec in todo:
            best = ledger.get("best", {}).get(spec)
            if not best:
                print("  %s: no selected config, skipping" % spec)
                continue
            print("\n=== %s : %d seeds (final) ===" % (spec, args.seeds))
            finals = []
            for s in range(args.seeds):
                model, info = make_train_rollout(spec, best["cfg"], seed=s)
                ev = eval_all(model, "val")
                finals.append({"seed": s, "val": ev, "params": n_params(model), "info": info})
                print("  seed %d  val one-step=%.6f  roll5=%.6f  roll25=%.6f"
                      % (s, ev["one_step"]["short"], ev["rollout"]["short"], ev["rollout"]["mid"]))
                torch.save(model.state_dict(),
                           os.path.join(CKPT, "%s_seed%d.pt" % (spec, s)))
            ledger.setdefault("final", {})[spec] = finals
            with io.open(ledger_path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(ledger, fh, ensure_ascii=False, indent=1)

    if args.stage in ("test", "all"):
        for spec in todo:
            best = ledger.get("best", {}).get(spec)
            if not best:
                continue
            print("\n=== %s : frozen TEST evaluation ===" % spec)
            results = []
            for s in range(args.seeds):
                model, _ = make_train_rollout(spec, best["cfg"], seed=s)
                t0 = time.time()
                ev = eval_all(model, "test")
                results.append({"seed": s, "test": ev, "params": n_params(model),
                                "eval_seconds": time.time() - t0})
                print("  seed %d  TEST one-step=%.6f  roll5=%.6f  roll25=%.6f  roll100=%.6f"
                      % (s, ev["one_step"]["short"], ev["rollout"]["short"],
                         ev["rollout"]["mid"], ev["rollout"]["long"]))
            ledger.setdefault("test", {})[spec] = results
            with io.open(ledger_path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(ledger, fh, ensure_ascii=False, indent=1)

    print("\ndone -> %s" % ledger_path)


if __name__ == "__main__":
    main()
