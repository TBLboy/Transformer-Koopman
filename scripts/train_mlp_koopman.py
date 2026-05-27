"""Train the MLP-Koopman baseline (control comparison vs PatchTST)."""
import argparse
import json
import os

import numpy as np
import torch

from patchtst_koopman.models.mlp_koopman_model import MLPKoopmanModel
from patchtst_koopman.training.mlp_koopman_trainer import MLPKoopmanTrainer
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.data_prep import prepare_datasets
from patchtst_koopman.utils.device import resolve_device
from patchtst_koopman.utils.evaluation import (
    evaluate_on_first_trajectory,
    plot_trajectory_comparison,
)
from patchtst_koopman.utils.seed import set_seed


def parse_args():
    parser = argparse.ArgumentParser(description="MLP-Koopman baseline training")
    parser.add_argument("--config", type=str, required=True, help="YAML config path")
    parser.add_argument(
        "--save_dir",
        type=str,
        default="./results/mlp_koopman",
        help="Output directory for model + plots",
    )
    parser.add_argument("--device", type=str, default=None, help="cuda / cpu")
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("MLP-Koopman training (baseline)")
    print("=" * 60)
    print(f"  Config:  {args.config}")
    print(f"  Output:  {args.save_dir}")

    config = load_config(args.config)
    config["experiment"]["device"] = resolve_device(
        args.device or config["experiment"]["device"]
    )
    print(f"Using device: {config['experiment']['device']}")

    set_seed(config["experiment"]["seed"])

    precision = config["experiment"].get("precision", "float32")
    if precision == "float64":
        torch.set_default_dtype(torch.float64)
    else:
        torch.set_default_dtype(torch.float32)

    os.makedirs(args.save_dir, exist_ok=True)

    train_dataset, val_dataset, test_dataset, norm_stats = prepare_datasets(config)
    print(f"  Train: {len(train_dataset)} / Val: {len(val_dataset)} / Test: {len(test_dataset)}")

    model = MLPKoopmanModel(config)
    model = model.double() if precision == "float64" else model.float()
    model = model.to(config["experiment"]["device"])

    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}")

    trainer = MLPKoopmanTrainer(model, config)
    trainer.train(train_dataset, val_dataset)

    # Save checkpoint
    A, B = model.get_koopman_matrices()
    spectral_radius = float(np.max(np.abs(np.linalg.eigvals(A))))
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "config": config,
        "koopman_A": A,
        "koopman_B": B,
        "spectral_radius": spectral_radius,
        "normalization": norm_stats,
    }
    model_save_path = os.path.join(args.save_dir, "model.pth")
    torch.save(checkpoint, model_save_path)
    print(f"  Saved: {model_save_path}  rho={spectral_radius:.4f}")

    rollout = evaluate_on_first_trajectory(model, test_dataset, config, norm_stats)
    plot_trajectory_comparison(
        rollout, save_path=os.path.join(args.save_dir, "test_prediction.png")
    )

    with open(os.path.join(args.save_dir, "results.json"), "w") as f:
        json.dump(
            {
                "method": "mlp_koopman",
                "training_method": config["mlp_koopman"]["training_method"],
                "test_rmse": rollout["rmse"],
                "test_mae": rollout["mae"],
            },
            f,
            indent=2,
        )

    print(f"Final test RMSE: {rollout['rmse']:.6f}")
    print(f"Final test MAE:  {rollout['mae']:.6f}")


if __name__ == "__main__":
    main()
