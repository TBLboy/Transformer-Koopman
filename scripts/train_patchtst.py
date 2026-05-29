"""Train the PatchTST-Koopman model on a given platform config.

Usage:
    python scripts/train_patchtst.py --config configs/platform2.yaml
"""
import argparse
import os

import torch
from torch.utils.data import DataLoader

from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
from patchtst_koopman.training.edmd_trainer import EDMDTrainer
from patchtst_koopman.utils.checkpoint import save_model, save_results
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.data_prep import prepare_datasets
from patchtst_koopman.utils.device import resolve_device
from patchtst_koopman.utils.evaluation import (
    evaluate_on_first_trajectory,
    plot_trajectory_comparison,
)
from patchtst_koopman.training.performance import apply_gpu_training_defaults
from patchtst_koopman.utils.seed import configure_cuda_performance, set_seed


def parse_args():
    parser = argparse.ArgumentParser(description="Train PatchTST-Koopman")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to a platform YAML config (e.g. configs/platform2.yaml)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Override config experiment.device (cuda / cpu)",
    )
    parser.add_argument(
        "--precision",
        type=str,
        default=None,
        choices=["float32", "float64"],
        help="Override config experiment.precision",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("PatchTST-Koopman training")
    print("=" * 60)

    config = load_config(args.config)
    print(f"Loaded config: {args.config}")

    if args.precision:
        config["experiment"]["precision"] = args.precision
    if args.device:
        config["experiment"]["device"] = args.device

    config["experiment"]["device"] = resolve_device(config["experiment"]["device"])
    print(f"Using device: {config['experiment']['device']}")

    apply_gpu_training_defaults(config)
    set_seed(config["experiment"]["seed"])
    configure_cuda_performance(config)

    precision = config["experiment"].get("precision", "float32")
    if precision == "float64":
        torch.set_default_dtype(torch.float64)
        print("Using float64 precision")
    else:
        torch.set_default_dtype(torch.float32)
        print("Using float32 precision")

    os.makedirs(config["experiment"]["save_dir"], exist_ok=True)
    os.makedirs(config["experiment"]["log_dir"], exist_ok=True)

    print("\n" + "=" * 60)
    print("Preparing datasets")
    print("=" * 60)
    train_dataset, val_dataset, test_dataset, norm_stats = prepare_datasets(config)

    print("\n" + "=" * 60)
    print("Building model")
    print("=" * 60)
    model = PatchTSTKoopmanModel(config)
    model = model.double() if precision == "float64" else model.float()
    model = model.to(config["experiment"]["device"])

    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}")

    method = config["training"]["method"]
    trainer = EDMDTrainer(model, config)
    trainer.train(train_dataset, val_dataset)

    # Quick test-set RMSE on the whole loader
    print("\n" + "=" * 60)
    print("Evaluating model")
    print("=" * 60)
    model.eval()
    test_loader = DataLoader(test_dataset, batch_size=256, shuffle=False)
    total_loss = 0.0
    with torch.no_grad():
        for batch in test_loader:
            x_history = batch["x_history"].to(config["experiment"]["device"])
            u_t = batch["u_t"].to(config["experiment"]["device"])
            x_next = batch["x_next"].to(config["experiment"]["device"])
            x_pred = model(x_history, u_t)
            total_loss += torch.nn.functional.mse_loss(x_pred, x_next).item()
    test_rmse_onestep = (total_loss / len(test_loader)) ** 0.5
    print(f"One-step test RMSE: {test_rmse_onestep:.6f}")

    print("\nSaving model and results...")
    model_path = save_model(model, config, norm_stats=norm_stats)

    rollout = evaluate_on_first_trajectory(model, test_dataset, config, norm_stats)
    plot_path = os.path.join(
        config["experiment"]["save_dir"], "auto_test", "test_prediction.png"
    )
    plot_trajectory_comparison(rollout, save_path=plot_path)

    results = {
        "method": method,
        "test_rmse_onestep": float(test_rmse_onestep),
        "auto_test_rmse": rollout["rmse"],
        "auto_test_mae": rollout["mae"],
    }
    save_results(results, config)

    print("\n" + "=" * 60)
    print("Training complete")
    print("=" * 60)
    print(f"  Model:      {model_path}")
    print(f"  Test plot:  {plot_path}")
    print(f"  Rollout RMSE: {rollout['rmse']:.6f}")
    print(f"  Rollout MAE:  {rollout['mae']:.6f}")


if __name__ == "__main__":
    main()
