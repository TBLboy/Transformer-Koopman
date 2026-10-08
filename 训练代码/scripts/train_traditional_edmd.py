"""Train the Traditional EDMD baseline (no neural net, hand-crafted lifting)."""
import argparse
import os

import matplotlib.pyplot as plt
import numpy as np

from patchtst_koopman.training.traditional_edmd_trainer import TraditionalEDMDTrainer
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.data_prep import prepare_datasets
from patchtst_koopman.utils.seed import set_seed


def parse_args():
    parser = argparse.ArgumentParser(description="Traditional EDMD training")
    parser.add_argument("--config", type=str, required=True, help="YAML config path")
    parser.add_argument(
        "--save_dir",
        type=str,
        default="./results/traditional_edmd",
        help="Output directory for matrices + plots",
    )
    return parser.parse_args()


def test_on_trajectory(trainer, test_dataset, config, norm_stats, save_dir):
    """Open-loop rollout: ``z_t = psi(x_t)`` -> ``z_{t+1} = A z + B u`` -> ``x = C z``."""
    P = config["encoder"]["history_length"]

    unique_traj_ids = np.unique(test_dataset.trajectory_id)
    mask = test_dataset.trajectory_id == unique_traj_ids[0]
    x_traj = test_dataset.x[mask]
    u_traj = test_dataset.u[mask]
    t_traj = test_dataset.t[mask]

    T = len(x_traj)
    print(f"Trajectory length: {T}; predicting {T - P} steps")

    x_t = x_traj[P - 1, :]
    u_sequence = u_traj[P - 1 : -1, :]
    x_true_norm = x_traj[P:, :]

    A, B, C = trainer.A, trainer.B, trainer.C
    lifting_fn = trainer.lifting_fn
    x_pred_list = []

    for h in range(len(u_sequence)):
        z_t = lifting_fn.transform(x_t.reshape(1, -1))[0]
        z_next = A @ z_t + B @ u_sequence[h]
        x_next = C @ z_next
        x_pred_list.append(x_next)
        x_t = x_next

    x_pred_norm = np.array(x_pred_list)

    if norm_stats is not None and norm_stats["x_mean"] is not None:
        x_pred = x_pred_norm * norm_stats["x_std"] + norm_stats["x_mean"]
        x_true = x_true_norm * norm_stats["x_std"] + norm_stats["x_mean"]
    else:
        x_pred, x_true = x_pred_norm, x_true_norm

    rmse = float(np.sqrt(np.mean((x_pred - x_true) ** 2)))
    mae = float(np.mean(np.abs(x_pred - x_true)))
    print(f"  RMSE: {rmse:.6f}")
    print(f"  MAE:  {mae:.6f}")

    n_state = x_true.shape[1]
    t = t_traj[P:]
    fig, axes = plt.subplots(n_state, 1, figsize=(14, 3 * n_state))
    if n_state == 1:
        axes = [axes]

    for i in range(n_state):
        ax = axes[i]
        ax.plot(t, x_true[:, i], "b-", label="True", linewidth=2, alpha=0.8)
        ax.plot(t, x_pred[:, i], "r--", label="Predicted", linewidth=2, alpha=0.8)
        err = np.abs(x_pred[:, i] - x_true[:, i])
        ax.fill_between(
            t, x_true[:, i] - err, x_true[:, i] + err,
            color="red", alpha=0.15, label="Error band",
        )
        ax.set_xlabel("Time (s)", fontsize=12)
        ax.set_ylabel(f"State Dim {i + 1}", fontsize=12)
        ax.legend(loc="best", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_title(f"Dim {i + 1}  RMSE: {rmse:.6f}  MAE: {mae:.6f}", fontsize=12)

    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "test_prediction.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Plot saved: {save_path}")

    return rmse, mae


def main():
    args = parse_args()

    print("=" * 60)
    print("Traditional EDMD training (baseline)")
    print("=" * 60)
    print(f"  Config:  {args.config}")
    print(f"  Output:  {args.save_dir}")

    config = load_config(args.config)
    set_seed(config["experiment"]["seed"])
    os.makedirs(args.save_dir, exist_ok=True)

    train_dataset, val_dataset, test_dataset, norm_stats = prepare_datasets(config)
    print(f"  Train: {len(train_dataset)} / Val: {len(val_dataset)} / Test: {len(test_dataset)}")

    trainer = TraditionalEDMDTrainer(config)
    trainer.train(train_dataset, val_dataset)

    trainer.save_model(args.save_dir)

    test_rmse, test_mae = test_on_trajectory(
        trainer, test_dataset, config, norm_stats, save_dir=args.save_dir
    )

    results = {
        "method": "traditional_edmd",
        "lifting_function": config["training"]["traditional_edmd"]["lifting_function"]["type"],
        "test_rmse": test_rmse,
        "test_mae": test_mae,
    }
    np.save(os.path.join(args.save_dir, "results.npy"), results)

    print("\nTraining complete")
    print(f"  Output: {args.save_dir}")
    print(f"  RMSE:   {test_rmse:.6f}")
    print(f"  MAE:    {test_mae:.6f}")


if __name__ == "__main__":
    main()
