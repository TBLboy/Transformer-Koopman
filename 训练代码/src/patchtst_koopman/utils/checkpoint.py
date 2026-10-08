"""Model checkpointing utilities.

In addition to ``state_dict`` we save the config, Koopman matrices, spectral
radius, normalisation statistics, and a few diagnostic fields. The loader is
backwards-compatible with the *original* project's old key names (``pos_encoder``,
``transformer_encoder``, ``output_projection``) so legacy checkpoints can be
loaded into the new code without retraining.
"""
import json
import os
from datetime import datetime

import numpy as np
import torch


def _map_legacy_keys(state_dict):
    """Rename old encoder key paths used by the original code base."""
    new_state_dict = {}
    for key, value in state_dict.items():
        new_key = key
        if "pos_encoder" in new_key:
            new_key = new_key.replace("pos_encoder", "positional_encoding")
        if "transformer_encoder" in new_key:
            new_key = new_key.replace("transformer_encoder", "transformer")
        if "output_projection" in new_key:
            new_key = new_key.replace("output_projection", "projection")
        new_state_dict[new_key] = value
    return new_state_dict


def save_model(model, config, norm_stats=None, filename=None):
    """Save a checkpoint with full diagnostic metadata."""
    save_dir = config["experiment"]["save_dir"]
    os.makedirs(save_dir, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"model_{timestamp}.pth"

    save_path = os.path.join(save_dir, filename)

    A, B = model.get_koopman_matrices()
    eigenvalues = np.linalg.eigvals(A)
    spectral_radius = float(np.max(np.abs(eigenvalues)))

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "config": config,
        "koopman_A": A,
        "koopman_B": B,
        "spectral_radius": spectral_radius,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model_info": {
            "state_dim": config["data"]["state_dim"],
            "control_dim": config["data"]["control_dim"],
            "latent_dim": config["encoder"]["latent_dim"],
            "history_length": config["encoder"]["history_length"],
            "patch_length": config["encoder"]["patch_length"],
        },
    }

    if norm_stats is not None:
        checkpoint["normalization"] = {
            "x_mean": norm_stats["x_mean"],
            "x_std": norm_stats["x_std"],
            "u_mean": norm_stats["u_mean"],
            "u_std": norm_stats["u_std"],
        }
        print("  Normalisation parameters saved")

    torch.save(checkpoint, save_path)

    print("\nModel saved:")
    print(f"  Path: {save_path}")
    print(f"  Spectral radius: {spectral_radius:.4f}")
    print(f"  Timestamp: {checkpoint['timestamp']}")

    return save_path


def load_model(model_path, device="cuda"):
    """Load a PatchTST-Koopman checkpoint (with legacy-key remapping)."""
    from patchtst_koopman.models.full_model import PatchTSTKoopmanModel

    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    config = checkpoint["config"]

    precision = config["experiment"].get("precision", "float32")
    if precision == "float64":
        torch.set_default_dtype(torch.float64)
    else:
        torch.set_default_dtype(torch.float32)

    model = PatchTSTKoopmanModel(config)
    model = model.double() if precision == "float64" else model.float()

    state_dict = _map_legacy_keys(checkpoint["model_state_dict"])
    model.load_state_dict(state_dict)
    model = model.to(device)
    model.eval()

    print("\nModel loaded:")
    print(f"  Path: {model_path}")
    print(f"  Spectral radius: {checkpoint['spectral_radius']:.4f}")
    print(f"  Trained at: {checkpoint['timestamp']}")
    print(f"  Precision: {precision}")

    if "normalization" in checkpoint:
        print("  Normalisation: present")
    else:
        print("  WARNING: no normalisation parameters in checkpoint")

    return model, config, checkpoint


def save_results(results, config, filename=None):
    """Save evaluation results as a timestamped JSON file."""
    save_dir = config["experiment"]["save_dir"]
    os.makedirs(save_dir, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results_{timestamp}.json"

    save_path = os.path.join(save_dir, filename)

    results["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results["config"] = {
        "method": config["training"]["method"],
        "state_dim": config["data"]["state_dim"],
        "control_dim": config["data"]["control_dim"],
        "latent_dim": config["encoder"]["latent_dim"],
    }

    with open(save_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved: {save_path}")
    return save_path
