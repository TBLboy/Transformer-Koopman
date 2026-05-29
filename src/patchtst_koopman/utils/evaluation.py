"""Shared rollout-prediction + plotting helpers.

The legacy project duplicated the iterative prediction loop and the
matplotlib comparison plot in 4+ training scripts. This module centralises
them so each script only knows about its own training flow.
"""
import os

import matplotlib.pyplot as plt
import numpy as np
import torch


def iterative_prediction(model, x_history_init, u_sequence, device, use_amp=False):
    """Run open-loop rollout: encode -> Koopman step -> decode -> slide window.

    Args:
        model: A model exposing ``encoder``, ``koopman``, ``decoder`` modules.
        x_history_init: ``[P, n]`` initial history window (on ``device``).
        u_sequence: ``[H, m]`` control inputs (on ``device``).
        device: Torch device string.
        use_amp: Use autocast on CUDA when True.

    Returns:
        ``[H, n]`` numpy array of predicted states (still normalised).
    """
    H = u_sequence.shape[0]
    x_history = x_history_init.clone()
    x_predictions = []
    amp_enabled = use_amp and device == "cuda"

    model.eval()
    with torch.no_grad():
        for h in range(H):
            u_t = u_sequence[h : h + 1, :]
            if amp_enabled:
                with torch.amp.autocast("cuda"):
                    z_t = model.encoder(x_history.unsqueeze(0))
                    z_next = model.koopman(z_t, u_t)
                    x_next = model.decoder(z_next)
            else:
                z_t = model.encoder(x_history.unsqueeze(0))
                z_next = model.koopman(z_t, u_t)
                x_next = model.decoder(z_next)

            x_step = x_next.squeeze(0)
            x_predictions.append(x_step.detach().cpu().numpy())
            x_history = torch.cat([x_history[1:, :], x_step.unsqueeze(0)], dim=0)

    return np.array(x_predictions)


def evaluate_on_first_trajectory(model, test_dataset, config, norm_stats):
    """Pick the first trajectory in ``test_dataset`` and compute rollout RMSE/MAE.

    Returns a dict with keys ``x_true``, ``x_pred``, ``t``, ``rmse``, ``mae``,
    ``trajectory_id``.
    """
    device = config["experiment"]["device"]
    precision = config["experiment"].get("precision", "float32")
    dtype = torch.float64 if precision == "float64" else torch.float32
    P = config["encoder"]["history_length"]

    unique_traj_ids = np.unique(test_dataset.trajectory_id)
    target_traj_id = unique_traj_ids[0]

    mask = test_dataset.trajectory_id == target_traj_id
    x_traj = test_dataset.x[mask]
    u_traj = test_dataset.u[mask]
    t_traj = test_dataset.t[mask]

    T = len(x_traj)
    print(f"Trajectory length: {T} steps (predicting {T - P})")

    x_history = torch.tensor(x_traj[:P, :], dtype=dtype).to(device)
    u_sequence = torch.tensor(u_traj[P - 1 : -1, :], dtype=dtype).to(device)
    x_true_norm = x_traj[P:, :]

    x_pred_norm = iterative_prediction(
        model,
        x_history,
        u_sequence,
        device,
        use_amp=config["experiment"].get("amp", False) and precision == "float32",
    )

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


def plot_trajectory_comparison(result, save_path=None, title_prefix=""):
    """Plot per-dimension True vs Predicted curves (with optional 2D phase plot).

    Args:
        result: Dict returned by :func:`evaluate_on_first_trajectory`.
        save_path: If provided, save the figure here (PNG, dpi 300).
        title_prefix: Prepended to subplot titles.
    """
    x_true = result["x_true"]
    x_pred = result["x_pred"]
    t = result["t"]
    rmse = result["rmse"]
    mae = result["mae"]

    n = x_true.shape[1]
    rows = n + (1 if n == 2 else 0)
    fig, axes = plt.subplots(rows, 1, figsize=(14, 4 * rows))
    if rows == 1:
        axes = [axes]

    for i in range(n):
        ax = axes[i]
        ax.plot(t, x_true[:, i], "b-", label="True", linewidth=2, alpha=0.7)
        ax.plot(t, x_pred[:, i], "r--", label="Predicted", linewidth=2, alpha=0.7)
        error = np.abs(x_pred[:, i] - x_true[:, i])
        ax.fill_between(
            t,
            x_true[:, i] - error,
            x_true[:, i] + error,
            color="red",
            alpha=0.2,
            label="Error",
        )
        ax.set_xlabel("Time (s)", fontsize=12)
        ax.set_ylabel(f"State Dim {i + 1}", fontsize=12)
        ax.legend(loc="best", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_title(
            f"{title_prefix}Dim {i + 1} - RMSE: {rmse:.6f}, MAE: {mae:.6f}",
            fontsize=12,
        )

    # 2D phase-portrait subplot when state is 2-dimensional
    if n == 2:
        ax = axes[n]
        ax.plot(
            x_true[:, 0],
            x_true[:, 1],
            "b-",
            label="True",
            linewidth=2,
            alpha=0.7,
            marker="o",
            markersize=3,
            markevery=10,
        )
        ax.plot(
            x_pred[:, 0],
            x_pred[:, 1],
            "r--",
            label="Predicted",
            linewidth=2,
            alpha=0.7,
            marker="s",
            markersize=3,
            markevery=10,
        )
        ax.plot(x_true[0, 0], x_true[0, 1], "go", markersize=10, label="Start")
        ax.plot(x_true[-1, 0], x_true[-1, 1], "mo", markersize=10, label="End")
        ax.set_xlabel("State Dim 1", fontsize=12)
        ax.set_ylabel("State Dim 2", fontsize=12)
        ax.legend(loc="best", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_title(f"{title_prefix}2D Trajectory Comparison", fontsize=12)
        ax.axis("equal")

    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved: {save_path}")
    else:
        plt.show()

    plt.close()
