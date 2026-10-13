# -*- coding: utf-8 -*-
"""Experiment 1 -- latent-consistency loss (GPT sec.5.1 / report sec.9.2).

MOTIVATION
----------
The frozen training objective constrains ONLY measurement-space prediction error
(run_gate1.py:168-173):

    L_x = mean((predict(xh,uin,ut) - x_next)**2)                # one step
        + w_roll * mean((rollout(xh,uin,uf)[:, :roll_h] - xf)**2)   # multi step

Nothing constrains the LIFTED coordinate z.  Since
``PatchTSTEncoder.forward`` returns ``cat([xh[:,-1,:], projection(h)])``
(library.py:97), the first ``n`` entries of z are EXACTLY the current measurement
and are not learnable -- only ``psi = z[n:]`` is free.  So "latent consistency"
can only mean constraining psi, which is precisely the coordinate the leakage
analysis blames for the long-horizon degradation.

INTERVENTION (single variable: the loss; model class / data / cfg all frozen)
----------------------------------------------------------------------------
    L = L_x + w_z * L_z
    L_z = mean_i || z_prop_i[n:] - sg( z_enc(X_true(k+1+i))[n:] ) ||^2

* ``z_prop_i`` is the PROPAGATED latent inside the rollout (latent propagation,
  Theory_Package/01 4.3), i.e. the quantity that drifts.
* the target is the encoder applied to the TRUE history window, with
  **stop-gradient**: the encoder is never dragged toward the propagated state.
* index bookkeeping: at loop step ``i`` the context is the window ending at
  ``x_{k+i}`` (it produces ``A(c_i)``), while the latent produced by that update
  corresponds to time ``k+1+i`` -- so its target window is ``i+1``.  Getting this
  off by one would silently compare psi against the wrong time index.

ANTI-COLLAPSE CONTROL (report sec.9.2 requires at least one)
-----------------------------------------------------------
1. stop-gradient on the target (above); and
2. every arm additionally REPORTS psi's effective rank (spectral entropy of the
   singular values) and its per-dimension spread, so a collapse to a constant is
   visible; and
3. every arm is compared against the pure-x linear baseline M0 on the same frozen
   test starts -- a collapsed psi stops beating M0.

WHY A SEPARATE SCRIPT
---------------------
``models/library.py`` and ``scripts/run_gate1.py`` stay byte-identical, so no
evidence already bound to them is invalidated (defect D-018).  Nothing here
writes to ``results/modeling/gate1_ledger.json``.

Run
---
    python scripts/train_latent_consistency.py --device soft_platform \
        --models M4 M5 --seeds 0 1 2 --epochs 50
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

import device as dev                       # noqa: E402
dev.bootstrap_from_argv()

import protocol as proto                   # noqa: E402
import run_gate1 as g1                     # noqa: E402
import run_gate2 as g2                     # noqa: E402

N = dev.current()["n_state"]
D = dev.current()["latent_dim"]
CKPT = os.path.join(dev.checkpoints_dir(), "lc")
RESULTS = dev.results_dir("modeling")
os.makedirs(CKPT, exist_ok=True)

# arms: (name, w_roll, w_z).  w_roll=None means "take the paired cfg's value".
ARMS = (
    ("base",    None, 0.0),     # frozen objective, re-trained at the SAME cfg
    ("z0p3",    None, 0.3),
    ("z3",      None, 3.0),
    ("zonly3",  0.0,  3.0),     # no multi-step x loss; only one-step x + psi
)


def true_window(S, Ufull, P, i):
    """The true history window/inputs ending at time step ``i`` of the sequence."""
    return S[:, i:i + P, :], Ufull[:, i:i + P - 1, :]


def latent_rollout(model, xh0, uin0, uf):
    """Latent-propagation rollout that ALSO returns the propagated latents."""
    H = uf.shape[1]
    z = model.encoder(xh0)
    xbuf, ubuf = xh0.clone(), uin0.clone()
    outs, zs = [], []
    for i in range(H):
        c = model.ctx(xbuf, ubuf)
        A, B = model.A_of(c), model.B_of(z[:, :N])
        u = uf[:, i, :]
        z = torch.bmm(A, z.unsqueeze(-1)).squeeze(-1) + \
            torch.bmm(B, u.unsqueeze(-1)).squeeze(-1)
        zs.append(z)
        outs.append(z[:, :N])
        xbuf = torch.cat([xbuf[:, 1:, :], z[:, :N].unsqueeze(1)], dim=1)
        ubuf = torch.cat([ubuf[:, 1:, :], u.unsqueeze(1)], dim=1)
    return torch.stack(outs, dim=1), torch.stack(zs, dim=1)


def rollout_with_consistency(model, xh, uin, uf, xf, roll_h):
    """ONE latent-propagation rollout, returning (x_predictions, L_z).

    Speed note: this shares a single rollout between the multi-step x loss and the
    psi-consistency term, and issues ONE batched encoder call for all ``roll_h``
    target windows instead of ``roll_h`` separate calls.  Both changes are
    mathematically identical to the naive form -- they only remove redundant work,
    which matters because the host is commit-starved and the grid must run on CPU.
    """
    P = xh.shape[1]
    B = xh.shape[0]
    S = torch.cat([xh, xf], dim=1)
    pred, zs = latent_rollout(model, xh, uin, uf[:, :roll_h, :])
    # latent produced at loop step i lives at time k+1+i  ->  window slice i+1
    xw = torch.stack([S[:, i + 1:i + 1 + P, :] for i in range(roll_h)], dim=1)
    with torch.no_grad():
        tgt = model.encoder(xw.reshape(B * roll_h, P, xh.shape[2]))[:, N:]
        tgt = tgt.reshape(B, roll_h, -1)
    return pred, torch.mean((zs[:, :, N:] - tgt) ** 2)


def train_arm(spec, cfg, seed, w_roll, w_z, tr, va, epochs, bs=64):
    torch.manual_seed(seed)
    np.random.seed(seed)
    lr = cfg.get("lr", 1e-3)
    roll_h = int(cfg.get("roll_h", 10))
    model = g1.build_model(spec, seed=seed,
                           **{k: v for k, v in cfg.items()
                              if k not in ("lr", "epochs", "w_roll", "roll_h")})
    model.to(g1.DEV)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                            lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=6,
                                                       min_lr=1e-6)
    n = len(tr["k"])
    bs = max(8, int(bs))
    best = {"val": float("inf"), "epoch": -1, "state": None}
    rng = np.random.default_rng(seed)
    for ep in range(epochs):
        model.train()
        perm = rng.permutation(n)
        tot, nb = 0.0, 0
        for s in range(0, n, bs):
            idx = perm[s:s + bs]
            if len(idx) < 8:
                continue
            xh = g1.batchify(tr, "Xh", idx)
            uin = g1.batchify(tr, "Uin", idx)
            ut = g1.batchify(tr, "Ut", idx)
            xn = g1.batchify(tr, "Xn", idx)
            loss = torch.mean((model.predict(xh, uin, ut) - xn) ** 2)
            if w_roll > 0 or w_z > 0:
                uf = g1.batchify(tr, "UF", idx)[:, :roll_h, :]
                xf = g1.batchify(tr, "XF", idx)[:, :roll_h, :]
                if w_z > 0:
                    # one shared rollout feeds BOTH terms
                    pred, lz = rollout_with_consistency(model, xh, uin, uf, xf, roll_h)
                    if w_roll > 0:
                        loss = loss + w_roll * torch.mean((pred - xf) ** 2)
                    loss = loss + w_z * lz
                else:
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
        vsel = g1.rollout_metric(model, va, proto.SELECTION_HORIZON, vidx) \
            if len(vidx) else float("inf")
        sched.step(vsel)
        if vsel < best["val"]:
            best = {"val": vsel, "epoch": ep,
                    "state": {k: v.detach().cpu().clone()
                              for k, v in model.state_dict().items()}}
        if ep - best["epoch"] > 18:
            break
    if best["state"] is not None:
        model.load_state_dict(best["state"])
    return model, {"best_val_roll25": best["val"], "best_epoch": best["epoch"],
                   "epochs_run": ep + 1}


@torch.no_grad()
def psi_diagnostics(model, split="test", n_batch=200):
    """Anti-collapse evidence: psi spread and effective rank on frozen starts."""
    w, _ = g1.tensors(split, proto.SELECTION_HORIZON, frozen_eval=True)
    idx = np.arange(min(n_batch, len(w["k"])))
    xh = g1.batchify(w, "Xh", idx)
    psi = model.encoder(xh)[:, N:]
    psi_c = psi - psi.mean(dim=0, keepdim=True)
    sv = torch.linalg.svdvals(psi_c)
    p = (sv ** 2) / max(float((sv ** 2).sum()), 1e-30)
    eff_rank = float(torch.exp(-(p * torch.log(p + 1e-30)).sum()))
    return {"psi_dim": int(psi.shape[1]),
            "psi_std_mean": float(psi.std(dim=0).mean()),
            "psi_abs_mean": float(psi.abs().mean()),
            "psi_eff_rank": eff_rank,
            "psi_eff_rank_frac": eff_rank / float(psi.shape[1])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", "-d", default=None)
    ap.add_argument("--models", nargs="+", default=["M4", "M5"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--bs", type=int, default=64,
                    help="batch size; lowered from 128 because the host is commit-starved")
    ap.add_argument("--arms", nargs="+", default=[a[0] for a in ARMS])
    ap.add_argument("--smoke", action="store_true",
                    help="1 arm / 1 seed / few epochs, for a code+timing check")
    ap.add_argument("--cpu", action="store_true",
                    help="force CPU: the host is commit-starved and a CUDA step has "
                         "already failed once with 'unknown error'")
    args = ap.parse_args()
    if args.cpu:
        g1.DEV = "cpu"
        print("[cpu] run_gate1.DEV forced to 'cpu'")

    if args.smoke:
        args.arms = ["base", "z3"]
        args.seeds = args.seeds[:1]
        args.epochs = min(args.epochs, 5)

    ledger = json.load(io.open(os.path.join(RESULTS, "gate1_ledger.json"), encoding="utf-8"))
    base_cfg = g2.paired_cfg(ledger["best"]["M5"]["cfg"])
    tr, _ = g1.tensors("train", proto.SELECTION_HORIZON, stride=4)
    va, _ = g1.tensors("val", proto.SELECTION_HORIZON, stride=4)
    print("device=%s  n=%d d=%d  train_windows=%d  paired_cfg=%s"
          % (dev.current()["name"], N, D, len(tr["k"]), base_cfg))

    out_path = os.path.join(RESULTS, "latent_consistency_%s%s.json"
                            % (dev.current()["name"], "_smoke" if args.smoke else ""))
    out = {"device": dev.current()["name"], "paired_cfg": base_cfg,
           "epochs": args.epochs, "seeds": args.seeds, "arms": {},
           "m0_reference": None}
    led0 = ledger.get("test", {}).get("M0")
    if led0:
        # eval_all returns per-horizon dicts, not scalars
        out["m0_reference"] = {
            "one_step": {k: float(np.mean([r["test"]["one_step"][k] for r in led0]))
                         for k in led0[0]["test"]["one_step"]},
            "rollout": {k: float(np.mean([r["test"]["rollout"][k] for r in led0]))
                        for k in led0[0]["test"]["rollout"]}}

    # merge-safe: a later invocation for the remaining arms must not drop earlier ones
    if os.path.exists(out_path):
        try:
            prev = json.load(io.open(out_path, encoding="utf-8"))
            if prev.get("device") == dev.current()["name"]:
                for k in ("arms", "m0_reference"):
                    if k in prev:
                        out[k] = prev[k]
                print("merging into existing %s (already present: %s)"
                      % (os.path.basename(out_path), sorted(prev.get("arms", {}))))
        except Exception as exc:                                  # noqa: BLE001
            print("could not merge existing results (%r); starting fresh" % exc)

    for spec in args.models:
        for arm_name, w_roll_ov, w_z in ARMS:
            if arm_name not in args.arms:
                continue
            w_roll = base_cfg.get("w_roll", 0.0) if w_roll_ov is None else w_roll_ov
            # resume: keep only runs produced with THIS epochs/weight setting, so a
            # crash mid-grid never loses finished work and stale smoke entries are
            # dropped automatically (they carry no "epochs" key)
            prev = out["arms"].get(spec, {}).get(arm_name, {})
            runs = [r for r in prev.get("runs", [])
                    if r.get("epochs") == args.epochs
                    and abs(float(r.get("w_z", -1.0)) - w_z) < 1e-12]
            done = {r["seed"] for r in runs}
            for seed in args.seeds:
                if seed in done:
                    print("  %s/%-7s seed%d already done at %d epochs -- skipped"
                          % (spec, arm_name, seed, args.epochs))
                    continue
                t0 = time.time()
                model, info = train_arm(spec, base_cfg, seed, w_roll, w_z, tr, va,
                                        args.epochs, args.bs)
                ev = g1.eval_all(model, "test")
                diag = psi_diagnostics(model)
                torch.save(model.state_dict(),
                           os.path.join(CKPT, "%s_%s_seed%d.pt" % (spec, arm_name, seed)))
                run = {"seed": seed, "w_roll": w_roll, "w_z": w_z,
                       "epochs": args.epochs, "info": info,
                       "test": {"one_step": ev["one_step"], "rollout": ev["rollout"],
                                "curve": ev["curve"]},
                       "psi": diag, "seconds": time.time() - t0}
                runs.append(run)
                print("  %s/%-7s seed%d  val_roll25=%.6f  test roll25=%.6f roll100=%.6f  "
                      "psi_eff_rank=%.2f  %.0fs"
                      % (spec, arm_name, seed, info["best_val_roll25"],
                         ev["rollout"]["mid"], ev["rollout"]["long"],
                         diag["psi_eff_rank"], run["seconds"]))
                out["arms"].setdefault(spec, {})[arm_name] = {
                    "w_roll": w_roll, "w_z": w_z, "runs": runs}
                with io.open(out_path, "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(out, fh, ensure_ascii=False, indent=1)
            g1.free()
            print("  -> %s/%s aggregated over %d seeds written to %s"
                  % (spec, arm_name, len(runs), out_path))
    print("written -> %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
