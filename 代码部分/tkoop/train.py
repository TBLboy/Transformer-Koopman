"""训练：闭式解、阶段一（一步损失）、阶段二（视野 H_R 的多步滚动损失）。

本模块只通过 load_train_data 取数据，接触不到测试集。
"""
from __future__ import annotations

import csv
import json
import math
import random
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np
import torch
import yaml

from .config import CONFIG_DIR, ROOT, RUNS_DIR, digest, grid, resolve, search_space, stage1_config, stage1_key
from .data import TrainData, load_train_data, split_window, train_starts, windows
from .evaluate import evaluate, evaluate_run
from .predictor import Predictor, build_predictor


class TrainingDiverged(RuntimeError):
    """训练损失出现非有限值。"""


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def git_state() -> dict:
    def run(*args):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    try:
        return {"commit": run("rev-parse", "HEAD"), "dirty": bool(run("status", "--porcelain", "--", "."))}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "dirty": None}


# ---------------------------------------------------------------- 损失 ----

def rollout_loss(pred: Predictor, seg_x: torch.Tensor, seg_u: torch.Tensor, P_h: int, alpha: float) -> torch.Tensor:
    """测量预测误差加提升状态一致性（论文式 eq:joint_training_loss，ω_i = 1/H）。

    H = 1 且调度关闭时就是阶段一的一步损失（论文式 eq:training_one_step_objects）。
    一致性目标 z^E_{k+i} = G(X_{k+i}) 取自记录的测量窗口；上下文沿预测历史更新。
    """
    X0, v0, U, Y = split_window(seg_x, seg_u, P_h)
    xhat, z = pred.rollout(X0, v0, U)
    B, H = U.shape[:2]
    targets = seg_x.unfold(1, P_h, 1)[:, 1:].permute(0, 1, 3, 2)  # X_{k+1..k+H}，[B, H, P_h, n]
    zE = pred.lift(targets.reshape(B * H, P_h, -1)).view(B, H, -1)
    return ((xhat - Y).pow(2).sum(-1) + alpha * (z - zE).pow(2).sum(-1)).mean()


# -------------------------------------------------------------- 闭式解 ----

@torch.no_grad()
def fit_closed_form(pred: Predictor, data: TrainData, cfg: dict, seed: int) -> None:
    """用训练集拟合特征映射，再由最小二乘解 [A B]（论文式 eq:edmd_control_solution）。

    ridge > 0 时解 (1/M)||Z^+ - K [Z; U]||_F^2 + ridge ||K||_F^2；ridge = 0 时取最小范数最小二乘解。
    """
    P_h = cfg["shared"]["P_h"]
    seg_x, seg_u = windows(data.train, P_h, 1, train_starts)
    X0, _, U, _ = split_window(seg_x, seg_u, P_h)
    pred.lifting.fit(X0, seed)
    Z, Zp = pred.lift(X0).double(), pred.lift(seg_x[:, 1:]).double()
    Phi = torch.cat([Z, U[:, 0].double()], 1)
    ridge = float(cfg["closed_form"]["ridge"])
    if ridge > 0:
        M = len(Phi)
        gram = Phi.T @ Phi / M + ridge * torch.eye(Phi.shape[1], dtype=torch.float64)
        K = torch.linalg.solve(gram, Phi.T @ Zp / M).T
    else:
        K = torch.linalg.lstsq(Phi, Zp, driver="gelsd").solution.T
    d = Z.shape[1]
    pred.dynamics.nominal.A0.copy_(K[:, :d].float())
    pred.dynamics.nominal.B0.copy_(K[:, d:].float())


# ------------------------------------------------------------ 训练循环 ----

def lr_factor(step: int, total: int, warmup_frac: float, min_ratio: float) -> float:
    """学习率相对峰值的比例：先线性预热，再按余弦衰减到 min_ratio。只取决于步数。"""
    warm = max(1, int(total * warmup_frac))
    if step < warm:
        return (step + 1) / warm
    t = min(1.0, (step - warm) / max(1, total - warm))
    return min_ratio + (1.0 - min_ratio) * 0.5 * (1.0 + math.cos(math.pi * t))


def run_stage(pred: Predictor, params: list, frozen: list, H: int, scfg: dict, cfg: dict,
              data: TrainData, out_dir: Path, seed: int, stage: str) -> dict:
    """训练一个阶段。每轮在验证集上评测全部视野，并保存：

      best_H<h>.pt      每个视野各一份验证误差最小的参数；
      last.pt           最后一轮的完整训练状态（模型、优化器、调度器、轮数、随机数状态）；
      epoch_<k>.pt      每隔 snapshot_every 轮的参数快照；
      train_log.csv     每轮的学习率、训练损失、各视野验证 RMSE。
    第 0 轮（训练前的起点）也参与选模。返回各视野的最优验证 RMSE。
    """
    device = torch.device(cfg["device"])
    P_h, ev = cfg["shared"]["P_h"], cfg["eval"]
    horizons = ev["horizons"]
    seg_x, seg_u = (t.to(device) for t in windows(data.train, P_h, H, train_starts))
    N, bs, epochs = len(seg_x), scfg["batch_size"], scfg["epochs"]
    total = math.ceil(N / bs) * epochs
    opt = torch.optim.AdamW(params, lr=scfg["lr"], weight_decay=scfg["weight_decay"])
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda step: lr_factor(step, total, scfg["warmup_frac"], scfg["lr_min_ratio"]))
    gen = torch.Generator().manual_seed(seed)
    best = {str(h): math.inf for h in horizons}
    out_dir.mkdir(parents=True, exist_ok=True)

    def validate(epoch: int) -> dict:
        val = evaluate(pred, data.val, data.normalizer.x_std, P_h, horizons, ev["diverge_threshold_cm"], device)
        rmse = {h: m["rmse_cm"] for h, m in val.items()}
        for h, value in rmse.items():
            if value < best[h]:
                best[h] = value
                torch.save({"model": pred.state_dict(), "stage": stage, "epoch": epoch, "val_rmse_cm": rmse},
                           out_dir / f"best_H{h}.pt")
        return rmse

    with open(out_dir / "train_log.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "lr", "train_loss", *[f"val_H{h}_cm" for h in horizons], "seconds"])
        rmse = validate(0)
        writer.writerow([0, "", "", *[rmse[str(h)] for h in horizons], ""])
        for epoch in range(1, epochs + 1):
            t0 = time.time()
            pred.train()
            for mod in frozen:
                mod.eval()
            loss_sum = 0.0
            for idx in torch.randperm(N, generator=gen).split(bs):
                idx = idx.to(device)
                loss = rollout_loss(pred, seg_x[idx], seg_u[idx], P_h, scfg["alpha"])
                if not torch.isfinite(loss):
                    raise TrainingDiverged(f"{stage} 第 {epoch} 轮的训练损失非有限")
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(params, scfg["grad_clip"])
                opt.step()
                sched.step()
                loss_sum += loss.item() * len(idx)
            lr = opt.param_groups[0]["lr"]
            validated = epoch % scfg["val_every"] == 0 or epoch == epochs
            rmse = validate(epoch) if validated else {}
            torch.save({"model": pred.state_dict(), "stage": stage, "epoch": epoch, "val_rmse_cm": rmse,
                        "optimizer": opt.state_dict(), "scheduler": sched.state_dict(),
                        "generator": gen.get_state()}, out_dir / "last.pt")
            if scfg["snapshot_every"] and epoch % scfg["snapshot_every"] == 0:
                torch.save({"model": pred.state_dict(), "stage": stage, "epoch": epoch, "val_rmse_cm": rmse},
                           out_dir / f"epoch_{epoch:04d}.pt")
            writer.writerow([epoch, lr, loss_sum / N, *[rmse.get(str(h), "") for h in horizons],
                             round(time.time() - t0, 3)])
            f.flush()
    return best


# ------------------------------------------------------------ 运行目录 ----

def run_dir(runs_dir: Path, tag: str, variant: str, seed: int) -> Path:
    return Path(runs_dir) / tag / variant / f"seed{seed}"


def stage1_dir(runs_dir: Path, cfg: dict, seed: int) -> Path:
    """阶段一按配置内容寻址：配置相同的变体自动共用同一份结果。"""
    return Path(runs_dir) / "_stage1" / stage1_key(cfg) / f"seed{seed}"


def _start(out: Path, cfg: dict, data: TrainData, seed: int, extra: dict | None = None) -> None:
    """清空未完成的运行目录，写入本次运行的配置、代码版本和归一化统计量。"""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    header = {"seed": seed, "git": git_state(), **(extra or {}), "config": cfg}
    with open(out / "config.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(header, f, allow_unicode=True, sort_keys=False)
    with open(out / "normalizer.json", "w", encoding="utf-8") as f:
        json.dump(data.normalizer.to_dict(), f)


def _finish(out: Path, info: dict) -> None:
    with open(out / "done.json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)


def _is_done(out: Path, cfg: dict) -> bool:
    if not (out / "done.json").is_file():
        return False
    with open(out / "config.yaml", encoding="utf-8") as f:
        if yaml.safe_load(f)["config"] != cfg:
            raise RuntimeError(f"{out} 已有另一份配置的结果。请换一个 --tag，或先删除该目录。")
    return True


# ------------------------------------------------------------ 训练入口 ----

def _fail(out: Path, err: Exception) -> None:
    with open(out / "failed.json", "w", encoding="utf-8") as f:
        json.dump({"error": str(err)}, f, ensure_ascii=False)


def ensure_stage1(cfg: dict, seed: int, data: TrainData, runs_dir: Path = RUNS_DIR) -> Path:
    """阶段一：调度关闭，用一步损失联合训练提升映射与 A_0、B_0。已有结果时直接复用。"""
    s1cfg = stage1_config(cfg)
    out = stage1_dir(runs_dir, cfg, seed)
    if _is_done(out, s1cfg):
        return out
    if (out / "failed.json").is_file():
        with open(out / "failed.json", encoding="utf-8") as f:
            raise TrainingDiverged(f"阶段一此前已失败（{json.load(f)['error']}）：{out}。排查后删除该目录再重跑。")
    _start(out, s1cfg, data, seed)
    seed_everything(seed)
    pred = build_predictor(s1cfg, data.n, data.m, nominal_only=True).to(cfg["device"])
    try:
        best = run_stage(pred, list(pred.parameters()), [], 1, cfg["stage1"], cfg, data, out, seed, "stage1")
    except TrainingDiverged as err:
        _fail(out, err)
        raise
    _finish(out, {"best_val_rmse_cm": best})
    return out


def load_stage1(pred: Predictor, state: dict) -> None:
    """把阶段一的提升映射与 A_0、B_0 载入变体的预测器；只允许调度参数缺失。"""
    result = pred.load_state_dict(state, strict=False)
    bad = [k for k in result.missing_keys if k.startswith(("lifting.", "dynamics.nominal."))]
    if result.unexpected_keys or bad:
        raise RuntimeError(f"阶段一参数与变体结构不匹配：多余 {result.unexpected_keys}，缺失 {bad}")


def is_deterministic(cfg: dict, n: int) -> bool:
    """延迟坐标 EDMDc 不用径向基（因而不涉及聚类）时结果与种子无关，只需运行一次。"""
    lift, sh = cfg["lifting"], cfg["shared"]
    return lift["kind"] == "delay_pca" and lift.get("n_rbf", 0) == 0 and sh["d"] - n <= n * (sh["P_h"] - 1)


def train_variant(cfg: dict, seed: int, tag: str = "dev", runs_dir: Path = RUNS_DIR) -> Path:
    """训练一个变体的一个种子，返回运行目录。已完成的运行直接跳过；未完成的从头重跑。"""
    out = run_dir(runs_dir, tag, cfg["variant"], seed)
    if _is_done(out, cfg):
        return out
    data = load_train_data(cfg)
    if "closed_form" in cfg:
        _start(out, cfg, data, seed)
        seed_everything(seed)
        pred = build_predictor(cfg, data.n, data.m)
        fit_closed_form(pred, data, cfg, seed)
        torch.save({"model": pred.state_dict(), "stage": "closed_form"}, out / "model.pt")
        info = {}
    else:
        s1 = ensure_stage1(cfg, seed, data, runs_dir)
        _start(out, cfg, data, seed, {"stage1_dir": str(s1.relative_to(runs_dir))})
        select = cfg["eval"]["select_horizon"]
        s1_ckpt = s1 / f"best_H{select}.pt"
        if not s1_ckpt.is_file():
            raise TrainingDiverged(f"阶段一在验证集的 H = {select} 上没有得到有限误差：{s1}")
        seed_everything(seed)
        pred = build_predictor(cfg, data.n, data.m).to(cfg["device"])
        load_stage1(pred, torch.load(s1_ckpt, map_location=cfg["device"], weights_only=False)["model"])
        if cfg["stage2"]["trainable"] == "scheduling":
            frozen = [pred.lifting, pred.dynamics.nominal]
            for mod in frozen:
                mod.requires_grad_(False)
            params = pred.dynamics.scheduling_parameters()
        else:
            frozen, params = [], list(pred.parameters())
        try:
            best = run_stage(pred, params, frozen, cfg["shared"]["H_R"], cfg["stage2"], cfg, data, out, seed, "stage2")
        except TrainingDiverged as err:
            _fail(out, err)
            raise
        info = {"best_val_rmse_cm": best}
    val = evaluate_run(out, "val")
    info["val_rmse_cm"] = {h: m["rmse_cm"] for h, m in val["horizons"].items()}
    _finish(out, info)
    return out


def tune(variant: str, seed: int = 0, max_trials: int = 12, keys: list[str] | None = None,
         overrides: dict | None = None, config_dir: Path = CONFIG_DIR, runs_dir: Path = RUNS_DIR) -> Path:
    """超参数选型：只用验证集。候选来自配置里的 search；组合数超过 max_trials 时固定随机抽取。

    keys 给出时只搜索以这些前缀开头的键，其余取配置中的当前值。结果写入 runs/tune/<variant>_summary.csv。
    """
    kw = {"config_dir": config_dir}
    space = search_space(variant, **kw)
    if keys:
        space = {k: v for k, v in space.items() if k.startswith(tuple(keys))}
    combos = grid(space)
    if len(combos) > max_trials:
        combos = random.Random(0).sample(combos, max_trials)
    rows = []
    for combo in combos:
        cfg = resolve(variant, {**(overrides or {}), **combo}, **kw)
        row = {"trial": digest(cfg), **combo}
        try:
            out = train_variant(cfg, seed, f"tune/{row['trial']}", runs_dir)
            with open(out / "val_metrics.json", encoding="utf-8") as f:
                val = json.load(f)["horizons"]
            row.update(status="ok", **{f"val_H{h}_cm": m["rmse_cm"] for h, m in val.items()})
        except TrainingDiverged as err:
            row.update(status=f"diverged: {err}")
        rows.append(row)
    select = f"val_H{resolve(variant, overrides, **kw)['eval']['select_horizon']}_cm"
    rows.sort(key=lambda r: r[select] if isinstance(r.get(select), float) and math.isfinite(r[select]) else math.inf)
    path = Path(runs_dir) / "tune" / f"{variant}_summary.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path
