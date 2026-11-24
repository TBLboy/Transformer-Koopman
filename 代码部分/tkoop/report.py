"""汇总：把各变体各种子的测试指标合成对比表和消融表。只读结果文件，不重新计算预测。"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

from .config import ABLATION, BASE_ONLY, COMPARISON, RESULTS_DIR, RUNS_DIR
from .evaluate import read_run

NAMES = {
    "edmdc": "EDMDc",
    "delay_edmdc": "Delay-coordinate EDMDc",
    "deep_koopman": "Deep Koopman",
    "lstm_koopman": "LSTM--Koopman",
    "full": "Proposed",
    "abl_no_sched": "w/o scheduling",
    "abl_no_hist_lift": "w/o history lifting",
    "abl_no_input_ctx": "w/o past inputs in context",
    "abl_ctx_once": "w/o context update",
}


def collect(runs_dir: Path, tag: str, variants: list[str], split: str = "test") -> tuple[list[dict], list]:
    """读取结果并检查一致性：所有运行的共用配置相同（R3），选模方式相同。"""
    rows, shared, selection, horizons = [], None, None, []
    for variant in variants:
        runs = []
        for path in sorted((Path(runs_dir) / tag / variant).glob(f"seed*/{split}_metrics.json")):
            header, _ = read_run(path.parent)
            base = {k: header["config"][k] for k in BASE_ONLY}
            if shared is None:
                shared, horizons = base, [str(h) for h in base["eval"]["horizons"]]
            elif base != shared:
                raise ValueError(f"{path.parent} 的共用配置（数据、d、P_h、H_R、评测视野）与其他运行不一致")
            with open(path, encoding="utf-8") as f:
                run = json.load(f)
            if selection is None:
                selection = run["selection"]
            elif run["selection"] != selection:
                raise ValueError(f"{path} 的选模方式是 {run['selection']}，与其他运行的 {selection} 不一致")
            runs.append(run)
        if not runs:
            raise FileNotFoundError(
                f"{Path(runs_dir) / tag / variant} 没有 {split}_metrics.json；"
                "不能生成不完整的汇总表"
            )
        row = {"variant": variant, "n_seeds": len(runs), "selection": selection if runs else ""}
        for h in horizons:
            values = np.array([r["horizons"][h]["rmse_cm"] for r in runs], dtype=float)
            row[f"H{h}_mean_cm"] = float(values.mean())
            row[f"H{h}_std_cm"] = float(values.std(ddof=1)) if len(values) > 1 else math.nan
            row[f"H{h}_n_diverged"] = sum(r["horizons"][h]["n_diverged"] for r in runs)
            row[f"H{h}_n_segments"] = sum(r["horizons"][h]["n_segments"] for r in runs)
        rows.append(row)
    return rows, horizons


def _cell(row: dict, h: str) -> str:
    mean = row.get(f"H{h}_mean_cm")
    if mean is None:
        return "--"
    text = f"{mean:.3f}" if math.isfinite(mean) else "diverged"
    std = row[f"H{h}_std_cm"]
    if math.isfinite(mean) and math.isfinite(std):
        text += f" $\\pm$ {std:.3f}"
    if row[f"H{h}_n_diverged"]:
        text += f"\\textsuperscript{{[{row[f'H{h}_n_diverged']}]}}"
    return text


def write_table(rows: list[dict], horizons: list, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(stem.with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    head = " & ".join(["Model"] + ["Full" if h == "full" else f"$H={h}$" for h in horizons])
    lines = [
        "% 由 python -m tkoop report 生成，请勿手改。",
        "% 滚动预测 RMSE，单位 cm；多种子时为均值 ± 标准差；上标 [k] 为发散段总数（未剔除）。",
        f"\\begin{{tabular}}{{l{'c' * len(horizons)}}}",
        "\\hline",
        head + " \\\\",
        "\\hline",
        *[" & ".join([NAMES.get(r["variant"], r["variant"])] + [_cell(r, h) for h in horizons]) + " \\\\" for r in rows],
        "\\hline",
        "\\end{tabular}",
    ]
    stem.with_suffix(".tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def report(tag: str = "final", split: str = "test", runs_dir: Path = RUNS_DIR, out_dir: Path = RESULTS_DIR) -> list[Path]:
    """生成 comparison.{csv,tex} 与 ablation.{csv,tex}。验证集的汇总文件名带 _val 后缀。"""
    suffix = "" if split == "test" else f"_{split}"
    stems = []
    for name, variants in (("comparison", COMPARISON), ("ablation", ABLATION)):
        rows, horizons = collect(runs_dir, tag, variants, split)
        stem = Path(out_dir) / f"{name}{suffix}"
        write_table(rows, horizons, stem)
        stems.append(stem)
    return stems
