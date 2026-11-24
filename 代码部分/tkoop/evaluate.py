"""分段评测与 RMSE：所有模型、所有变体共用的唯一实现（需求基线 R5、R6）。"""
from __future__ import annotations

import json
from pathlib import Path

import torch
import yaml

from .data import Normalizer, data_dir, eval_windows, load_split, split_window
from .predictor import Predictor, build_predictor


@torch.no_grad()
def evaluate(pred: Predictor, trajs: list, x_std, P_h: int, horizons: list, threshold_cm: float,
             device="cpu", batch_size: int = 4096) -> dict:
    """对已归一化的轨迹做分段自由滚动，返回每个视野的指标（物理单位 cm）。

    段 RMSE = sqrt(段内各步 ||xhat - x||_2^2 的平均)；rmse_cm 是全部段的算术平均。
    发散的段不剔除、不截断：rmse_cm 照常包含它们，另报非有限段数与超过阈值的段数。
    """
    pred.eval()
    scale = torch.as_tensor(x_std, dtype=torch.float32, device=device)
    out = {}
    for h in horizons:
        parts = []
        for _, seg_x, seg_u in eval_windows(trajs, P_h, h):
            for i in range(0, len(seg_x), batch_size):
                X0, v0, U, Y = split_window(seg_x[i : i + batch_size].to(device), seg_u[i : i + batch_size].to(device), P_h)
                xhat, _ = pred.rollout(X0, v0, U)
                err_cm = (xhat - Y) * scale
                parts.append(err_cm.pow(2).sum(-1).mean(1).sqrt().cpu())
        r = torch.cat(parts) if parts else torch.empty(0)
        nonfinite = ~torch.isfinite(r)
        out[str(h)] = {
            "rmse_cm": float(r.mean()) if len(r) else float("nan"),
            "n_segments": len(r),
            "n_nonfinite": int(nonfinite.sum()),
            "n_diverged": int((nonfinite | (r > threshold_cm)).sum()),
            "segments_cm": r.tolist(),
        }
    return out


def read_run(run_dir: Path) -> tuple[dict, Normalizer]:
    run_dir = Path(run_dir)
    with open(run_dir / "config.yaml", encoding="utf-8") as f:
        header = yaml.safe_load(f)
    with open(run_dir / "normalizer.json", encoding="utf-8") as f:
        norm = Normalizer.from_dict(json.load(f))
    return header, norm


def _checkpoint(run_dir: Path, horizon, select) -> Path:
    """某个视野所用的参数文件。缺失时依次退回选模视野的最优参数、最后一轮参数。"""
    for name in ("model.pt", f"best_H{horizon}.pt", f"best_H{select}.pt", "last.pt"):
        if (run_dir / name).is_file():
            return run_dir / name
    raise FileNotFoundError(f"{run_dir} 中没有可用的模型参数")


def evaluate_run(run_dir: Path, split: str, per_horizon: bool = False, select=None, force: bool = False) -> dict:
    """评测一次训练的结果并写出 <split>_metrics.json。

    默认所有视野都用选模视野 select 上验证误差最小的那份参数；per_horizon 为真时每个视野用它自己的最优参数。
    测试集的结果文件已存在时拒绝覆盖；force 为真时把旧文件改名保留后重写。
    """
    run_dir = Path(run_dir)
    header, norm = read_run(run_dir)
    cfg = header["config"]
    out_path = run_dir / f"{split}_metrics.json"
    if split == "test" and out_path.exists():
        if not force:
            raise FileExistsError(f"{out_path} 已存在：测试集只评测一次。确需重评请显式加 --force。")
        n_prev = len(list(run_dir.glob("test_metrics.prev*.json")))
        out_path.rename(run_dir / f"test_metrics.prev{n_prev}.json")

    ev, P_h = cfg["eval"], cfg["shared"]["P_h"]
    select = ev["select_horizon"] if select is None else select
    trajs = norm.apply(load_split(data_dir(cfg), split))
    device = torch.device(cfg["device"])
    pred = build_predictor(cfg, len(norm.x_std), len(norm.u_std)).to(device)

    horizons, used = {}, {}
    for h in ev["horizons"]:
        ckpt = _checkpoint(run_dir, h if per_horizon else select, select)
        used[str(h)] = ckpt.name
    for name in sorted(set(used.values())):
        state = torch.load(run_dir / name, map_location=device, weights_only=False)
        pred.load_state_dict(state["model"])
        hs = [h for h in ev["horizons"] if used[str(h)] == name]
        horizons.update(evaluate(pred, trajs, norm.x_std, P_h, hs, ev["diverge_threshold_cm"], device))

    result = {
        "variant": cfg["variant"],
        "seed": header["seed"],
        "split": split,
        "selection": "per_horizon" if per_horizon else f"single_H{select}",
        "checkpoints": used,
        "horizons": {str(h): horizons[str(h)] for h in ev["horizons"]},
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    return result
