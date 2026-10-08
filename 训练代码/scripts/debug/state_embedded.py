"""Verify the ``z = [x_t; h_t]`` state-embedding holds for a trained encoder.

Loads a checkpoint and prints, per sample, the difference between
``z[:n]`` and the true ``x_t``. If non-zero it indicates a bug in the
encoder (the front of ``z`` should equal the current state exactly).
"""
import argparse

import numpy as np
import torch

from patchtst_koopman.data.dataset import KoopmanDataset
from patchtst_koopman.utils.checkpoint import load_model
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.device import resolve_device


def parse_args():
    parser = argparse.ArgumentParser(description="Verify the encoder's state-embedded output")
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--num_samples", type=int, default=10)
    return parser.parse_args()


def main():
    args = parse_args()
    device = resolve_device(args.device)
    print(f"Loading model: {args.model_path}")
    model, _, checkpoint = load_model(args.model_path, device=device)
    config = load_config(args.config)
    config["experiment"]["device"] = device

    norm_stats = checkpoint.get("normalization")
    test_dataset = KoopmanDataset(config["data"]["data_dir"], config, "test", norm_stats=norm_stats)

    n = config["data"]["state_dim"]
    max_diff_global = 0.0

    print("\n" + "=" * 80)
    print(f"Checking z[:n] == x_t for {args.num_samples} samples (state_dim={n})")
    print("=" * 80)
    for i in range(min(args.num_samples, len(test_dataset))):
        sample = test_dataset[i]
        x_history = sample["x_history"].unsqueeze(0).to(device)
        x_t_true = sample["x_history"][-1].numpy()

        with torch.no_grad():
            z = model.encoder(x_history)
        z = z.squeeze(0).cpu().numpy()
        diff = np.max(np.abs(z[:n] - x_t_true))
        max_diff_global = max(max_diff_global, diff)
        print(f"  sample {i:3d}: max |z[:n] - x_t| = {diff:.6e}")

    print(f"\nOverall max diff: {max_diff_global:.6e}")
    if max_diff_global < 1e-4:
        print("OK: state-embedding holds")
    else:
        print("WARNING: state-embedding violated; check encoder forward pass")


if __name__ == "__main__":
    main()
