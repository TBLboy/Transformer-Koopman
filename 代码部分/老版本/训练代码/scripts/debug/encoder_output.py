"""Dump statistics of the encoder output ``z`` over a chunk of the training set.

Useful for spotting collapsed latents (std -> 0), exploding components, or
unevenly utilised dimensions.
"""
import argparse

import numpy as np
import torch

from patchtst_koopman.data.dataset import KoopmanDataset
from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.device import resolve_device


def parse_args():
    parser = argparse.ArgumentParser(description="Inspect encoder output statistics")
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--num_samples", type=int, default=1000)
    return parser.parse_args()


def main():
    args = parse_args()
    device = resolve_device(args.device)
    config = load_config(args.config)
    precision = config["experiment"].get("precision", "float32")
    if precision == "float64":
        torch.set_default_dtype(torch.float64)

    train_dataset = KoopmanDataset(config["data"]["data_dir"], config, "train")

    checkpoint = torch.load(args.model_path, map_location=device, weights_only=False)
    model = PatchTSTKoopmanModel(config)
    if precision == "float64":
        model = model.double()
    model.load_state_dict(checkpoint["model_state_dict"], strict=False)
    model = model.to(device).eval()

    print(f"\nInspecting encoder output over {args.num_samples} samples")
    n = min(args.num_samples, len(train_dataset))
    z_list = []
    with torch.no_grad():
        for i in range(n):
            sample = train_dataset[i]
            x_history = sample["x_history"].unsqueeze(0).to(device)
            z = model.encoder(x_history)
            z_list.append(z.cpu().numpy())
    Z = np.concatenate(z_list, axis=0)

    print(f"\nEncoder output z statistics:")
    print(f"  shape: {Z.shape}")
    print(f"  mean:  {Z.mean():.6f}")
    print(f"  std:   {Z.std():.6f}")
    print(f"  range: [{Z.min():.6f}, {Z.max():.6f}]")

    print("\nPer-dim std (sorted ascending):")
    per_dim_std = Z.std(axis=0)
    order = np.argsort(per_dim_std)
    for i in order[:10]:
        print(f"  dim {i:3d}: std={per_dim_std[i]:.6e}  mean={Z[:, i].mean():.6e}")
    print("  ...")
    for i in order[-5:]:
        print(f"  dim {i:3d}: std={per_dim_std[i]:.6e}  mean={Z[:, i].mean():.6e}")


if __name__ == "__main__":
    main()
