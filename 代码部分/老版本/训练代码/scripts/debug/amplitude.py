"""Diagnose amplitude / normalisation issues in a trained checkpoint.

Reports per-row norms of the decoder ``C`` matrix, spectral radius of ``A``,
and statistics of one-step predicted vs ground-truth states.
"""
import argparse

import numpy as np
import torch

from patchtst_koopman.data.dataset import KoopmanDataset
from patchtst_koopman.utils.checkpoint import load_model
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.device import resolve_device


def parse_args():
    parser = argparse.ArgumentParser(description="Diagnose amplitude / normalisation issues")
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--num_samples", type=int, default=200)
    return parser.parse_args()


def main():
    args = parse_args()
    device = resolve_device(args.device)

    print(f"Loading model: {args.model_path}")
    model, config, checkpoint = load_model(args.model_path, device=device)

    config = load_config(args.config)
    config["experiment"]["device"] = device
    norm_stats = checkpoint.get("normalization")
    test_dataset = KoopmanDataset(config["data"]["data_dir"], config, "test", norm_stats=norm_stats)

    print("\n" + "=" * 80)
    print("Koopman matrices A, B")
    print("=" * 80)
    A = model.koopman.A.data.cpu().numpy()
    B = model.koopman.B.data.cpu().numpy()
    print(f"  A shape: {A.shape}  norm: {np.linalg.norm(A):.6f}")
    print(f"  Spectral radius: {np.max(np.abs(np.linalg.eigvals(A))):.6f}")
    print(f"  B shape: {B.shape}  norm: {np.linalg.norm(B):.6f}")

    print("\n" + "=" * 80)
    print("One-step prediction stats (first {} samples)".format(args.num_samples))
    print("=" * 80)
    preds, trues = [], []
    n = min(args.num_samples, len(test_dataset))
    with torch.no_grad():
        for i in range(n):
            sample = test_dataset[i]
            x_history = sample["x_history"].unsqueeze(0).to(device)
            u_t = sample["u_t"].unsqueeze(0).to(device)
            x_next = sample["x_next"].numpy()
            x_pred = model(x_history, u_t).squeeze(0).cpu().numpy()
            preds.append(x_pred)
            trues.append(x_next)

    P = np.array(preds)
    T = np.array(trues)
    print(f"  Predicted: mean={P.mean():.6f}  std={P.std():.6f}  range=[{P.min():.6f},{P.max():.6f}]")
    print(f"  True:      mean={T.mean():.6f}  std={T.std():.6f}  range=[{T.min():.6f},{T.max():.6f}]")
    print(f"  Per-dim RMSE: {np.sqrt(np.mean((P - T) ** 2, axis=0))}")


if __name__ == "__main__":
    main()
