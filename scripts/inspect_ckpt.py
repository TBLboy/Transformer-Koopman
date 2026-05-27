"""Inspect what's in the checkpoint."""
import torch
import numpy as np

PATH = r"C:\Users\Windows\Desktop\论文4\code-projectv2\results\models\model_20260527_154535.pth"
ckpt = torch.load(PATH, map_location="cpu", weights_only=False)

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
