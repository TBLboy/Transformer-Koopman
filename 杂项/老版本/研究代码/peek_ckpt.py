import os, sys, json
import numpy as np, torch
REPO = r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码"
sys.path.insert(0, os.path.join(REPO, "src"))
CKPT = os.path.join(REPO, "deploy", "algorithms", "tk_assets", "model_assets", "platform2_full_model.pth")
sd = torch.load(CKPT, map_location="cpu", weights_only=False)
print("top keys:", list(sd.keys()))
for k, v in sd.items():
    if hasattr(v, "shape"):
        print(" ", k, tuple(v.shape))
    elif isinstance(v, dict):
        print(" ", k, "dict:", {kk: (tuple(vv.shape) if hasattr(vv, "shape") else vv) for kk, vv in list(v.items())[:8]})
