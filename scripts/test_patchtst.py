"""Test a trained PatchTST-Koopman checkpoint on a single trajectory.

Usage:
    python scripts/test_patchtst.py \\
        --model_path results/models/<checkpoint>.pth \\
        --config configs/platform2.yaml \\
        --traj_idx 0
"""
import argparse
import os

import numpy as np
import torch

from patchtst_koopman.data.dataset import KoopmanDataset
from patchtst_koopman.utils.checkpoint import load_model
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.device import resolve_device
from patchtst_koopman.utils.evaluation import (
    iterative_prediction,
    plot_trajectory_comparison,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Test a PatchTST-Koopman checkpoint")
    parser.add_argument("--model_path", type=str, required=True, help="Path to .pth checkpoint")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to the YAML config used during training",
    )
    parser.add_argument(
        "--traj_idx", type=int, default=0, help="Index of the test trajectory to roll out"
    )
    parser.add_argument(
        "--save_dir", type=str, default="./results/test", help="Output directory"
    )
    parser.add_argument(
        "--device", type=str, default=None, help="cuda / cpu (overrides config)"
    )
    return parser.parse_args()


def test_single_trajectory(model, test_dataset, traj_idx, config, norm_stats):
    """Roll out the trajectory at ``traj_idx`` and return true/pred + metrics."""
    device = config["experiment"]["device"]
    precision = config["experiment"].get("precision", "float32")
    dtype = torch.float64 if precision == "float64" else torch.float32
    P = config["encoder"]["history_length"]

    unique_traj_ids = np.unique(test_dataset.trajectory_id)
    if traj_idx >= len(unique_traj_ids):
        raise ValueError(
            f"traj_idx {traj_idx} out of range; test set has {len(unique_traj_ids)} trajectories"
        )
    target_traj_id = unique_traj_ids[traj_idx]

    mask = test_dataset.trajectory_id == target_traj_id
    x_traj = test_dataset.x[mask]
    u_traj = test_dataset.u[mask]
    t_traj = test_dataset.t[mask]

    T = len(x_traj)
    print(f"\nTesting trajectory {traj_idx} (id={target_traj_id}):")
    print(f"  Length: {T} steps")
    print(f"  Predicting {T - P} steps")

    x_history_init = torch.tensor(x_traj[:P, :], dtype=dtype).to(device)
    u_sequence = torch.tensor(u_traj[P - 1 : -1, :], dtype=dtype).to(device)
    x_true_norm = x_traj[P:, :]

    x_pred_norm = iterative_prediction(model, x_history_init, u_sequence, device)

    if norm_stats is not None and norm_stats["x_mean"] is not None:
        x_mean = norm_stats["x_mean"]
        x_std = norm_stats["x_std"]
        x_pred = x_pred_norm * x_std + x_mean
        x_true = x_true_norm * x_std + x_mean
    else:
        x_pred = x_pred_norm
        x_true = x_true_norm

    rmse = float(np.sqrt(np.mean((x_pred - x_true) ** 2)))
    mae = float(np.mean(np.abs(x_pred - x_true)))

    print(f"  RMSE: {rmse:.6f}")
    print(f"  MAE:  {mae:.6f}")

    return {
        "trajectory_id": int(target_traj_id),
        "x_true": x_true,
        "x_pred": x_pred,
        "t": t_traj[P:],
        "rmse": rmse,
        "mae": mae,
    }


def main():
    args = parse_args()
    os.makedirs(args.save_dir, exist_ok=True)

    print("=" * 60)
    print("PatchTST-Koopman testing")
    print("=" * 60)
    print(f"  Model:  {args.model_path}")
    print(f"  Config: {args.config}")

    device = resolve_device(args.device or "cuda")
    model, model_config, checkpoint = load_model(args.model_path, device=device)

    # Override the checkpoint's embedded config with the user-supplied YAML —
    # data paths and post-training fields may legitimately differ.
    config = load_config(args.config)
    config["experiment"]["device"] = device

    if "normalization" in checkpoint:
        norm_stats = checkpoint["normalization"]
        print("  Normalisation: loaded from checkpoint")
    else:
        print("  WARNING: checkpoint missing normalisation; recomputing from training set")
        train_dataset = KoopmanDataset(config["data"]["data_dir"], config, "train")
        norm_stats = train_dataset.get_norm_stats()

    test_dataset = KoopmanDataset(
        config["data"]["data_dir"], config, "test", norm_stats=norm_stats
    )

    results = test_single_trajectory(model, test_dataset, args.traj_idx, config, norm_stats)

    plot_path = os.path.join(args.save_dir, f"trajectory_{args.traj_idx}_comparison.png")
    plot_trajectory_comparison(results, save_path=plot_path)

    npz_path = os.path.join(args.save_dir, f"trajectory_{args.traj_idx}_results.npz")
    np.savez(
        npz_path,
        x_true=results["x_true"],
        x_pred=results["x_pred"],
        t=results["t"],
        rmse=results["rmse"],
        mae=results["mae"],
    )
    print(f"Saved numeric results: {npz_path}")
    print("=" * 60)
    print("Test complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
