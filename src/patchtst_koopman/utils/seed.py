"""Reproducibility seeding and CUDA performance tuning."""
import random

import numpy as np
import torch


def set_seed(seed, deterministic=None):
    """Seed python/numpy/torch (and CUDA when available).

    When ``deterministic`` is ``None``, only RNG seeds are set and existing
    cuDNN flags are left unchanged (call :func:`configure_cuda_performance`
    afterwards for training throughput).
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        if deterministic is not None:
            torch.backends.cudnn.deterministic = deterministic
            torch.backends.cudnn.benchmark = not deterministic

    print(f"Random seed set to: {seed}")


def configure_cuda_performance(config):
    """Apply CUDA throughput settings from ``experiment`` config."""
    exp = config.get("experiment", {})
    device = exp.get("device", "cpu")
    if device != "cuda" or not torch.cuda.is_available():
        return

    deterministic = exp.get("deterministic", False)
    cudnn_benchmark = exp.get("cudnn_benchmark", not deterministic)
    use_amp = exp.get("amp", True) and exp.get("precision", "float32") == "float32"

    torch.backends.cudnn.deterministic = deterministic
    torch.backends.cudnn.benchmark = cudnn_benchmark and not deterministic
    torch.backends.cuda.matmul.allow_tf32 = exp.get("allow_tf32", True)
    torch.backends.cudnn.allow_tf32 = exp.get("allow_tf32", True)

    print(
        "CUDA performance: "
        f"deterministic={deterministic}, "
        f"cudnn.benchmark={torch.backends.cudnn.benchmark}, "
        f"amp={use_amp}, "
        f"tf32={exp.get('allow_tf32', True)}"
    )
