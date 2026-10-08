"""Test a trained Traditional EDMD model (A/B/C + lifting metadata)."""
import argparse
import os

import matplotlib.pyplot as plt
import numpy as np

from patchtst_koopman.training.traditional_edmd_trainer import TraditionalEDMDTrainer
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.data_prep import prepare_datasets


def parse_args():
    parser = argparse.ArgumentParser(description="Test a Traditional EDMD model")
    parser.add_argument(
        "--model_dir",
        type=str,
        required=True,
        help="Directory containing A_matrix.npy / B_matrix.npy / C_matrix.npy / lifting_meta.npz",
    )
    parser.add_argument("--config", type=str, required=True, help="YAML config path")
    parser.add_argument(
        "--traj_idx", type=int, default=0, help="Index of the test trajectory"
    )
    parser.add_argument(
        "--save_dir", type=str, default="./results/traditional_edmd/test", help="Output dir"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.save_dir, exist_ok=True)

    config = load_config(args.config)
    _, _, test_dataset, norm_stats = prepare_datasets(config)

    trainer = TraditionalEDMDTrainer(config)
    trainer.load_model(args.model_dir)

    P = config["encoder"]["history_length"]
    unique_ids = np.unique(test_dataset.trajectory_id)
    target_id = unique_ids[args.traj_idx]
    mask = test_dataset.trajectory_id == target_id
    x_traj = test_dataset.x[mask]
    u_traj = test_dataset.u[mask]
    t_traj = test_dataset.t[mask]

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
    if norm_stats and norm_stats["x_mean"] is not None:
        x_pred = x_pred_norm * norm_stats["x_std"] + norm_stats["x_mean"]
        x_true = x_true_norm * norm_stats["x_std"] + norm_stats["x_mean"]
    else:
        x_pred, x_true = x_pred_norm, x_true_norm

    rmse = float(np.sqrt(np.mean((x_pred - x_true) ** 2)))
    mae = float(np.mean(np.abs(x_pred - x_true)))
    print(f"Trajectory {args.traj_idx} (id={target_id}): RMSE={rmse:.6f}  MAE={mae:.6f}")

    n = x_true.shape[1]
    t = t_traj[P:]
    fig, axes = plt.subplots(n, 1, figsize=(14, 3 * n))
    if n == 1:
        axes = [axes]
    for i in range(n):
        ax = axes[i]
        ax.plot(t, x_true[:, i], "b-", label="True", linewidth=2)
        ax.plot(t, x_pred[:, i], "r--", label="Predicted", linewidth=2)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(f"State Dim {i + 1}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_title(f"Dim {i + 1}  RMSE: {rmse:.6f}  MAE: {mae:.6f}")
    plt.tight_layout()
    save_path = os.path.join(args.save_dir, f"trajectory_{args.traj_idx}.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Plot saved: {save_path}")


if __name__ == "__main__":
    main()
