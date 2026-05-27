"""Test a trained MLP-Koopman checkpoint on one or all test trajectories."""
import argparse
import os

import numpy as np
import torch

from patchtst_koopman.data.dataset import KoopmanDataset
from patchtst_koopman.models.mlp_koopman_model import MLPKoopmanModel
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.device import resolve_device
from patchtst_koopman.utils.evaluation import (
    iterative_prediction,
    plot_trajectory_comparison,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Test an MLP-Koopman checkpoint")
    parser.add_argument("--model_path", type=str, required=True, help=".pth checkpoint")
    parser.add_argument("--config", type=str, required=True, help="YAML config path")
    parser.add_argument(
        "--traj_idx",
        type=int,
        default=0,
        help="Index of the test trajectory to roll out",
    )
    parser.add_argument(
        "--save_dir", type=str, default="./results/mlp_koopman/test", help="Output dir"
    )
    parser.add_argument("--device", type=str, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.save_dir, exist_ok=True)

    config = load_config(args.config)
    device = resolve_device(args.device or config["experiment"]["device"])
    config["experiment"]["device"] = device

    checkpoint = torch.load(args.model_path, map_location=device, weights_only=False)
    model = MLPKoopmanModel(checkpoint["config"])
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device).float()
    model.eval()

    norm_stats = checkpoint.get("normalization")
    if norm_stats is None:
        print("WARNING: checkpoint missing normalisation; recomputing from training set")
        train_ds = KoopmanDataset(config["data"]["data_dir"], config, "train")
        norm_stats = train_ds.get_norm_stats()

    test_dataset = KoopmanDataset(
        config["data"]["data_dir"], config, "test", norm_stats=norm_stats
    )

    P = config["encoder"]["history_length"]
    dtype = torch.float64 if config["experiment"].get("precision", "float32") == "float64" else torch.float32
    unique_ids = np.unique(test_dataset.trajectory_id)
    target_id = unique_ids[args.traj_idx]
    mask = test_dataset.trajectory_id == target_id
    x_traj = test_dataset.x[mask]
    u_traj = test_dataset.u[mask]
    t_traj = test_dataset.t[mask]

    x_history = torch.tensor(x_traj[:P], dtype=dtype).to(device)
    u_sequence = torch.tensor(u_traj[P - 1 : -1], dtype=dtype).to(device)
    x_true_norm = x_traj[P:]

    x_pred_norm = iterative_prediction(model, x_history, u_sequence, device)

    if norm_stats and norm_stats["x_mean"] is not None:
        x_pred = x_pred_norm * norm_stats["x_std"] + norm_stats["x_mean"]
        x_true = x_true_norm * norm_stats["x_std"] + norm_stats["x_mean"]
    else:
        x_pred, x_true = x_pred_norm, x_true_norm

    rmse = float(np.sqrt(np.mean((x_pred - x_true) ** 2)))
    mae = float(np.mean(np.abs(x_pred - x_true)))
    print(f"Trajectory {args.traj_idx} (id={target_id}): RMSE={rmse:.6f}  MAE={mae:.6f}")

    plot_trajectory_comparison(
        {
            "trajectory_id": int(target_id),
            "x_true": x_true,
            "x_pred": x_pred,
            "t": t_traj[P:],
            "rmse": rmse,
            "mae": mae,
        },
        save_path=os.path.join(args.save_dir, f"trajectory_{args.traj_idx}.png"),
    )


if __name__ == "__main__":
    main()
