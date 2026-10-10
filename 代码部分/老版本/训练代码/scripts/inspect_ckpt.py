"""Inspect what's in the checkpoint.

Usage (from 训练代码/):

    python scripts/inspect_ckpt.py --checkpoint results/models/model_XXXX.pth
"""
import argparse
from pathlib import Path

import numpy as np
import torch

PROJECT_DIR = Path(__file__).resolve().parents[1]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True,
                        help="path to a model_*.pth checkpoint")
    return parser.parse_args()


args = parse_args()
PATH = Path(args.checkpoint)
if not PATH.is_absolute():
    PATH = PROJECT_DIR / PATH
if not PATH.is_file():
    raise SystemExit(f"checkpoint not found: {PATH}")

ckpt = torch.load(str(PATH), map_location="cpu", weights_only=False)

print("Keys in checkpoint:")
for k in ckpt:
    v = ckpt[k]
    if isinstance(v, np.ndarray):
        print(f"  {k}: ndarray {v.shape}")
    elif isinstance(v, torch.Tensor):
        print(f"  {k}: tensor {v.shape}")
    elif isinstance(v, dict):
        print(f"  {k}: dict with keys {list(v.keys())}")
    elif isinstance(v, (int, float, str)):
        print(f"  {k}: {v}")
    else:
        print(f"  {k}: {type(v).__name__}")

print(f"\nEncoder config: P={ckpt['config']['encoder']['history_length']}, "
      f"p={ckpt['config']['encoder']['patch_length']}, "
      f"n={ckpt['config']['data']['state_dim']}, "
      f"d={ckpt['config']['encoder']['latent_dim']}")
