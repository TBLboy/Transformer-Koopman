# -*- coding: utf-8 -*-
"""Stage-0 / Stage-1 training ablation for the Transformer-Koopman paper.

Implements the four training strategies requested by the review file
"Stage0_Stage1训练机制审查_两阶段意义与B矩阵冻结策略.md" (section 8):

    A : Stage 0 trains (theta, A0, B); Stage 1 trains only (phi, U, V, gamma_psi)
    B : Stage 0 trains (theta, A0, B); Stage 1 trains (theta, phi, A0, U, V, gamma_psi), B FROZEN
        -> what the paper text currently claims
    C : Stage 0 trains (theta, A0, B); Stage 1 trains ALL parameters including B
        -> what the released training code actually does (DEC-040)
    D : no Stage 0; random initialization, then Stage 1 trains ALL parameters

Stage 0 uses the modulation-free one-step model (A0, B0 only), which reproduces the
fixed time-invariant baseline of the paper. Stage 1 minimizes the rollout-aware
scheduled objective L_R (open-loop scheduled propagation, H_R = 20), re-scheduling
the context from the predictor's own rolled-out history.

Reported per run: scheduled-propagation rollout RMSE at H = 1, 5, 10, 20 (the
deployment mode), fixed-transition propagation RMSE, recurrent re-encoding RMSE,
per-epoch train/val losses (stability + convergence), and wall-clock time.
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

TEMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
sys.path.insert(0, TEMP)

import gate14_stabilize as g14
from gate_context_koopman import build_split, eval_rollout, H_EVAL, H_MAX, REPO, DEV
from gate14_stabilize import BudgetedCtxKoopman, build_seq_split, openloop_forward, eval_prop
from patchtst_koopman.utils.config_loader import load_config

STATE = r"C:\Users\12187\AppData\Local\Temp\opencode\gate_states"
OUT = r"D:\Project\Transformer-Koopman\Transformer-Koopman\杂项\ablation_stage01_result.json"

GROUPS = ("encoder", "ctx", "A0", "B0", "UV", "gamma")


class AblModel(BudgetedCtxKoopman):
    """BudgetedCtxKoopman with an explicit modulation switch for Stage 0."""

    def __init__(self, cfg, r=2, delta_A=0.07):
        super().__init__(cfg, r=r, delta_A=delta_A)
        self.use_mod = True

    def get_AB(self, xh, uh):
        if not self.use_mod:
            B = xh.shape[0]
            return (self.A0.unsqueeze(0).expand(B, -1, -1),
                    self.B0.unsqueeze(0).expand(B, -1, -1))
        return super().get_AB(xh, uh)


def param_groups(model):
    g = {"encoder": [], "ctx": [], "A0": [model.A0], "B0": [model.B0],
         "UV": [model.Uraw, model.Vraw], "gamma": [model.s, model.g.weight, model.g.bias]}
    for name, p in model.named_parameters():
        if name.startswith("encoder."):
            g["encoder"].append(p)
        elif name.startswith("ctx."):
            g["ctx"].append(p)
    return g


def apply_freeze(model, frozen):
    for name, p in model.named_parameters():
        if name.startswith("encoder."):
            grp = "encoder"
        elif name.startswith("ctx."):
            grp = "ctx"
        elif name == "A0":
            grp = "A0"
        elif name == "B0":
            grp = "B0"
        elif name in ("Uraw", "Vraw"):
            grp = "UV"
        else:
            grp = "gamma"
        p.requires_grad = grp not in frozen
    return [p for p in model.parameters() if p.requires_grad]


def n_trainable(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def run_stage(model, opt, epochs, batch, seq, loss_kind, lr_sched_note=""):
    """Train one stage. Returns per-epoch (train, val) losses."""
    XH, UH, UT, XN = batch
    XH0, UH0, UF, XF = seq
    n = len(XH)
    bs = 256
    curve = []
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(n)
        tot, cnt = 0.0, 0
        for s in range(0, n, bs):
            b = perm[s:s + bs]
            opt.zero_grad()
            if loss_kind == "one_step":
                pred = model(XH[b].to(DEV), UH[b].to(DEV), UT[b].to(DEV))
                target = XN[b].to(DEV)
            else:
                pred = openloop_forward(model, XH0[b].to(DEV), UH0[b].to(DEV), UF[b].to(DEV))
                target = XF[b].to(DEV)
            loss = F.mse_loss(pred, target)
            loss.backward()
            opt.step()
            tot += float(loss) * len(b)
            cnt += len(b)
        model.eval()
        with torch.no_grad():
            if loss_kind == "one_step":
                vl = float(F.mse_loss(model(XH.to(DEV), UH.to(DEV), UT.to(DEV)), XN.to(DEV)))
            else:
                vl = float(F.mse_loss(openloop_forward(model, XH0.to(DEV), UH0.to(DEV), UF.to(DEV)),
                                      XF.to(DEV)))
        curve.append({"epoch": ep + 1, "train": tot / max(cnt, 1), "val": vl})
    return curve


def make_model(cfg, seed, init_state=None):
    torch.manual_seed(seed)
    np.random.seed(seed)
    m = AblModel(cfg, r=2, delta_A=0.07).to(DEV)
    if init_state is not None:
        m.load_state_dict(init_state, strict=False)
    return m


def snapshot(model):
    return {k: v.detach().clone() for k, v in model.state_dict().items()}


def evaluate(model, cfg, data_dir, norm, val_batch, val_seq):
    model.use_mod = True
    model.eval()
    out = {
        "R_prop": eval_prop(model, "val", norm, sched=True),
        "F_prop": eval_prop(model, "val", norm, sched=False),
        "R_reencode": eval_rollout(model, cfg, data_dir, "val", norm),
    }
    with torch.no_grad():
        XH, UH, UT, XN = val_batch
        out["val_one_step_mse"] = float(F.mse_loss(model(XH.to(DEV), UH.to(DEV), UT.to(DEV)),
                                                   XN.to(DEV)))
        XH0, UH0, UF, XF = val_seq
        out["val_rollout_mse"] = float(F.mse_loss(
            openloop_forward(model, XH0.to(DEV), UH0.to(DEV), UF.to(DEV)), XF.to(DEV)))
    return out


def run_one(strategy, cfg, data_dir, seed, e0, e1, tr_batch, val_batch, tr_seq, val_seq, norm):
    t0 = time.time()
    log = {"strategy": strategy, "seed": seed, "e0": e0, "e1": e1}
    model = make_model(cfg, seed)
    opt_cfg = dict(lr=5e-4)

    # ---------------- Stage 0 (nominal one-step pretraining) ----------------
    if strategy in ("A", "B", "C"):
        model.use_mod = False
        trainable = apply_freeze(model, frozen=("ctx", "UV", "gamma"))
        log["stage0_trainable"] = n_trainable(model)
        log["stage0_groups"] = list(GROUPS)
        opt = torch.optim.Adam(trainable, **opt_cfg)
        log["stage0_curve"] = run_stage(model, opt, e0, tr_batch, tr_seq, "one_step")
        stage0_state = snapshot(model)
    else:  # strategy D: no Stage 0
        log["stage0_curve"] = []
        stage0_state = None
    t_stage0 = time.time() - t0

    # ---------------- Stage 1 (scheduled-rollout fine-tuning) ----------------
    frozen = {"A": ("encoder", "A0", "B0"), "B": ("B0",), "C": (), "D": ()}[strategy]
    model = make_model(cfg, seed, init_state=stage0_state)
    model.use_mod = True
    trainable = apply_freeze(model, frozen=frozen)
    log["stage1_frozen"] = list(frozen)
    log["stage1_trainable"] = n_trainable(model)
    opt = torch.optim.Adam(trainable, **opt_cfg)
    t1 = time.time()
    log["stage1_curve"] = run_stage(model, opt, e1, tr_batch, tr_seq, "rollout")
    t_stage1 = time.time() - t1

    log["stage0_seconds"] = round(t_stage0, 1)
    log["stage1_seconds"] = round(t_stage1, 1)
    log["total_seconds"] = round(time.time() - t0, 1)
    log["metrics"] = evaluate(model, cfg, data_dir, norm, val_batch, val_seq)
    log["state"] = {k: v.detach().cpu() for k, v in model.state_dict().items()}
    return log


def summarize(runs):
    keys = ["A", "B", "C", "D"]
    summary = {}
    for k in keys:
        rs = [r for r in runs if r["strategy"] == k]
        if not rs:
            continue
        entry = {"n_seeds": len(rs), "seeds": [r["seed"] for r in rs]}
        for metric in ("R_prop", "F_prop", "R_reencode"):
            for h in H_EVAL:
                vals = [r["metrics"][metric][h] for r in rs]
                entry["%s@H%d_mean" % (metric, h)] = float(np.mean(vals))
                entry["%s@H%d_std" % (metric, h)] = float(np.std(vals))
        for m in ("val_one_step_mse", "val_rollout_mse"):
            vals = [r["metrics"][m] for r in rs]
            entry[m + "_mean"] = float(np.mean(vals))
            entry[m + "_std"] = float(np.std(vals))
        entry["stage0_seconds_mean"] = float(np.mean([r["stage0_seconds"] for r in rs]))
        entry["stage1_seconds_mean"] = float(np.mean([r["stage1_seconds"] for r in rs]))
        entry["stage1_epochs_to_best_mean"] = float(np.mean([
            int(np.argmin([c["val"] for c in r["stage1_curve"]])) + 1 for r in rs]))
        # training stability: std of the last-quarter rollout val loss
        entry["stage1_val_tail_std_mean"] = float(np.mean([
            float(np.std([c["val"] for c in r["stage1_curve"][-max(1, len(r["stage1_curve"]) // 4):]]))
            for r in rs]))
        summary[k] = entry
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategies", type=str, default="A,B,C,D")
    ap.add_argument("--seeds", type=str, default="0")
    ap.add_argument("--e0", type=int, default=100)
    ap.add_argument("--e1", type=int, default=100)
    ap.add_argument("--tag", type=str, default="")
    args = ap.parse_args()

    cfg = load_config(os.path.join(REPO, "configs", "platform2.yaml"))
    data_dir = os.path.abspath(os.path.join(REPO, cfg["data"]["data_dir"]))
    g14.CFG = cfg          # eval_prop reads module-level CFG / DATA_DIR
    g14.DATA_DIR = data_dir

    print("device", DEV, "| P", cfg["encoder"]["history_length"], "| data", data_dir, flush=True)
    trXH, trUH, trUT, trXN, norm = build_split(data_dir, "train", cfg)
    vaXH, vaUH, vaUT, vaXN, _ = build_split(data_dir, "val", cfg, norm)
    tr_batch = (trXH, trUH, trUT, trXN)
    val_batch = (vaXH, vaUH, vaUT, vaXN)
    tr_seq = build_seq_split(data_dir, "train", cfg, norm, H_MAX)
    val_seq = build_seq_split(data_dir, "val", cfg, norm, H_MAX)
    print("train", trXH.shape, "val", vaXH.shape, "seq", tr_seq[0].shape, flush=True)

    runs = []
    for seed in [int(s) for s in args.seeds.split(",")]:
        for strat in args.strategies.split(","):
            strat = strat.strip()
            if not strat:
                continue
            print("=== %s seed=%d ===" % (strat, seed), flush=True)
            r = run_one(strat, cfg, data_dir, seed, args.e0, args.e1,
                        tr_batch, val_batch, tr_seq, val_seq, norm)
            print("  stage1_frozen=%s trainable=%d" % (r["stage1_frozen"], r["stage1_trainable"]),
                  flush=True)
            print("  R_prop", {k: round(v, 4) for k, v in r["metrics"]["R_prop"].items()}, flush=True)
            print("  F_prop", {k: round(v, 4) for k, v in r["metrics"]["F_prop"].items()}, flush=True)
            print("  time  stage0=%.1fs stage1=%.1fs" % (r["stage0_seconds"], r["stage1_seconds"]),
                  flush=True)
            runs.append(r)

    summary = summarize(runs)
    print("\n===== SUMMARY (val, scheduled propagation R_prop) =====", flush=True)
    for k, e in summary.items():
        print("%s  H1=%.4f H5=%.4f H10=%.4f H20=%.4f  val_rollout_mse=%.5f  t1=%.0fs"
              % (k, e["R_prop@H1_mean"], e["R_prop@H5_mean"], e["R_prop@H10_mean"],
                 e["R_prop@H20_mean"], e["val_rollout_mse_mean"], e["stage1_seconds_mean"]),
              flush=True)

    payload = {"config": {"strategies": args.strategies, "seeds": args.seeds, "e0": args.e0,
                          "e1": args.e1, "tag": args.tag, "r": 2, "delta_A": 0.07,
                          "H_R": H_MAX, "lr": 5e-4, "bs": 256},
               "summary": summary,
               "runs": [{k: v for k, v in r.items() if k != "state"} for r in runs]}
    if os.path.exists(OUT):
        try:
            old = json.load(open(OUT, encoding="utf-8"))
            if isinstance(old.get("runs"), list):
                payload["runs"] = old["runs"] + payload["runs"]
        except Exception:
            pass
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1, default=str)
    # keep the trained states separately (large)
    for r in runs:
        p = os.path.join(STATE, "ablation_%s_seed%d%s.pt" % (r["strategy"], r["seed"], args.tag))
        torch.save(r["state"], p)
    print("saved", OUT, flush=True)


if __name__ == "__main__":
    main()
