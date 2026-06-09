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
    torch.set_float32_matmul_precision(exp.get("float32_matmul_precision", "high"))

    if deterministic:
        torch.use_deterministic_algorithms(True, warn_only=True)
        if hasattr(torch.backends.cuda, "enable_flash_sdp"):
            torch.backends.cuda.enable_flash_sdp(False)
        if hasattr(torch.backends.cuda, "enable_mem_efficient_sdp"):
            torch.backends.cuda.enable_mem_efficient_sdp(False)
        if hasattr(torch.backends.cuda, "enable_math_sdp"):
            torch.backends.cuda.enable_math_sdp(True)

    print(
        "CUDA performance: "
        f"deterministic={deterministic}, "
        f"cudnn.benchmark={torch.backends.cudnn.benchmark}, "
        f"amp={use_amp}, "
        f"tf32={exp.get('allow_tf32', True)}, "
        f"matmul_precision={exp.get('float32_matmul_precision', 'high')}"
    )


def get_worker_init_fn(seed):
    """Return a ``worker_init_fn`` that seeds each DataLoader worker process.

    Each worker gets ``seed + worker_id`` so shuffles differ across workers
    but are reproducible across runs with the same base seed.
    """
    def _worker_init_fn(worker_id):
        worker_seed = seed + worker_id
        np.random.seed(worker_seed)
        random.seed(worker_seed)
        torch.manual_seed(worker_seed)
    return _worker_init_fn
