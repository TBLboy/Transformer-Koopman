from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch
import yaml

from tkoop.config import COMPARISON, VARIANTS, resolve, stage1_key
from tkoop.data import Normalizer, TrainData, eval_starts, eval_windows, split_window, train_starts, windows
from tkoop.evaluate import evaluate
from tkoop.predictor import build_predictor
from tkoop.report import report
from tkoop.train import run_stage


def _traj(T: int = 24) -> tuple[np.ndarray, np.ndarray]:
    t = np.arange(T, dtype=np.float64)
    x = np.stack([0.1 * t, np.sin(t / 4)], axis=1)
    u = np.stack([np.cos(t / 5), np.sin(t / 6)], axis=1)
    return x, u


def test_non_overlapping_eval_starts_and_window_contract() -> None:
    assert eval_starts(24, 4, 5) == [3, 8, 13, 18]
    traj = [_traj()]
    sx, su = windows(traj, 4, 5, eval_starts)
    assert sx.shape == (4, 9, 2)
    assert su.shape == (4, 8, 2)
    X, v, U, Y = split_window(sx, su, 4)
    assert X.shape == (4, 4, 2)
    assert v.shape == (4, 3, 2)
    assert U.shape == Y.shape[:2] + (2,)
    assert Y.shape == (4, 5, 2)
    # The first prediction target is immediately after the current measurement.
    torch.testing.assert_close(Y[:, 0], sx[:, 4])


def test_full_horizon_keeps_one_segment_per_trajectory() -> None:
    trajs = [_traj(24), _traj(24)]
    result = eval_windows(trajs, 4, "full")
    assert len(result) == 1
    horizon, sx, su = result[0]
    assert horizon == 20
    assert sx.shape == (2, 24, 2)
    assert su.shape == (2, 23, 2)


def test_normalizer_is_fit_on_train_only() -> None:
    train = [(_traj(5)[0], _traj(5)[1])]
    norm = Normalizer.fit(train)
    applied = norm.apply(train)
    np.testing.assert_allclose(np.concatenate([x for x, _ in applied]).mean(0), 0.0, atol=1e-12)
    assert not np.allclose(norm.x_mean, _traj(24)[0].mean(0))


@pytest.mark.parametrize("variant", VARIANTS)
def test_all_variants_forward_and_rollout(variant: str) -> None:
    cfg = resolve(variant)
    torch.manual_seed(0)
    pred = build_predictor(cfg, n=2, m=2)
    X0 = torch.randn(3, cfg["shared"]["P_h"], 2)
    v0 = torch.randn(3, cfg["shared"]["P_h"] - 1, 2)
    U = torch.randn(3, 3, 2)
    if "closed_form" in cfg:
        pred.lifting.fit(X0, seed=0)
    xhat, z, A, B = pred.rollout(X0, v0, U, return_matrices=True)
    assert xhat.shape == (3, 3, 2)
    assert z.shape == (3, 3, cfg["shared"]["d"])
    assert A.shape == (3, 3, cfg["shared"]["d"], cfg["shared"]["d"])
    assert B.shape == (3, 3, cfg["shared"]["d"], 2)
    assert torch.isfinite(xhat).all()


def test_zero_scheduling_is_fixed_dynamics() -> None:
    fixed_cfg = resolve("abl_no_sched")
    scheduled_cfg = resolve("full")
    torch.manual_seed(7)
    fixed = build_predictor(fixed_cfg, 2, 2)
    torch.manual_seed(7)
    scheduled = build_predictor(scheduled_cfg, 2, 2)
    with torch.no_grad():
        scheduled.dynamics.amp_A.weight.zero_()
        scheduled.dynamics.amp_A.bias.zero_()
        scheduled.dynamics.amp_B.weight.zero_()
        scheduled.dynamics.amp_B.bias.zero_()
    X0 = torch.randn(2, 8, 2)
    v0 = torch.randn(2, 7, 2)
    U = torch.randn(2, 4, 2)
    fixed_out = fixed.rollout(X0, v0, U)
    scheduled_out = scheduled.rollout(X0, v0, U)
    torch.testing.assert_close(fixed_out[0], scheduled_out[0])
    torch.testing.assert_close(fixed_out[1], scheduled_out[1])


def test_stage1_keys_are_shared_by_declared_variants() -> None:
    cfgs = {name: resolve(name) for name in VARIANTS}
    assert stage1_key(cfgs["full"]) == stage1_key(cfgs["abl_no_sched"])
    assert stage1_key(cfgs["deep_koopman"]) == stage1_key(cfgs["abl_no_hist_lift"])
    assert stage1_key(cfgs["full"]) != stage1_key(cfgs["deep_koopman"])


def test_config_rejects_invalid_scheduling_rank() -> None:
    with pytest.raises(ValueError, match="r_B"):
        resolve("full", {"dynamics.r_B": 11})
    with pytest.raises(ValueError, match="horizons"):
        resolve("full", {"eval.horizons": [8, 8]})


def test_cli_help_lists_all_workflows() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "tkoop", "--help"],
        cwd=Path(__file__).parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    assert all(word in result.stdout for word in ("train", "eval", "tune", "freeze", "report"))


def _write_fake_run(root: Path, variant: str, split: str = "test") -> None:
    run = root / "final" / variant / "seed0"
    run.mkdir(parents=True)
    cfg = resolve(variant)
    with (run / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump({"seed": 0, "config": cfg}, f, allow_unicode=True, sort_keys=False)
    with (run / "normalizer.json").open("w", encoding="utf-8") as f:
        json.dump({"x_mean": [0, 0], "x_std": [1, 1], "u_mean": [0, 0], "u_std": [1, 1]}, f)
    metrics = {
        "variant": variant,
        "seed": 0,
        "split": split,
        "selection": "single_H8",
        "horizons": {
            str(h): {
                "rmse_cm": 1.0,
                "n_segments": 2,
                "n_nonfinite": 0,
                "n_diverged": 1 if variant == "full" and str(h) == "8" else 0,
                "segments_cm": [1.0, 1.0],
            }
            for h in cfg["eval"]["horizons"]
        },
    }
    with (run / f"{split}_metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f)


def test_report_requires_complete_runs_and_writes_tables(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    for variant in VARIANTS:
        _write_fake_run(runs, variant)
    outputs = report(tag="final", runs_dir=runs, out_dir=tmp_path / "results")
    assert {p.name for p in outputs} == {"comparison", "ablation"}
    comparison = (tmp_path / "results" / "comparison.csv").read_text(encoding="utf-8")
    table = (tmp_path / "results" / "comparison.tex").read_text(encoding="utf-8")
    assert all(name in comparison for name in ("edmdc", "delay_edmdc", "full"))
    assert "H8_n_diverged" in comparison
    assert r"\textsuperscript{[1]}" in table

    (runs / "final" / COMPARISON[0] / "seed0" / "test_metrics.json").unlink()
    with pytest.raises(FileNotFoundError, match="不完整"):
        report(tag="final", runs_dir=runs, out_dir=tmp_path / "results_missing")


def test_stage_saves_best_last_and_snapshot(tmp_path: Path) -> None:
    torch.manual_seed(0)
    trajs = [_traj(24), _traj(24)]
    norm = Normalizer.fit(trajs)
    data = TrainData(norm.apply(trajs[:1]), norm.apply(trajs[1:]), norm, 2, 2)
    cfg = {
        "device": "cpu",
        "shared": {"d": 4, "P_h": 4, "H_R": 2},
        "eval": {"horizons": [1, 2], "diverge_threshold_cm": 100.0},
    }
    model_cfg = {
        "shared": cfg["shared"],
        "lifting": {"kind": "mlp", "hidden": 8, "layers": 1},
        "dynamics": {"kind": "fixed"},
    }
    pred = build_predictor(model_cfg, 2, 2)
    scfg = {
        "batch_size": 8,
        "epochs": 1,
        "lr": 1e-3,
        "weight_decay": 0.0,
        "grad_clip": 1.0,
        "warmup_frac": 0.1,
        "lr_min_ratio": 0.01,
        "val_every": 1,
        "snapshot_every": 1,
        "alpha": 0.1,
    }
    run_stage(pred, list(pred.parameters()), [], 2, scfg, cfg, data, tmp_path, 0, "stage-test")
    assert (tmp_path / "best_H1.pt").is_file()
    assert (tmp_path / "best_H2.pt").is_file()
    assert (tmp_path / "last.pt").is_file()
    assert (tmp_path / "epoch_0001.pt").is_file()
    assert (tmp_path / "train_log.csv").is_file()
    state = torch.load(tmp_path / "last.pt", weights_only=False)
    assert state["stage"] == "stage-test"
    assert state["epoch"] == 1
    assert "optimizer" in state and "scheduler" in state
