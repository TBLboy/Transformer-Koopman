"""Shared GPU training defaults for long-running sweeps (ablation, etc.)."""


def apply_gpu_training_defaults(config):
    """Fill in GPU-friendly training settings when absent from YAML."""
    exp = config.setdefault("experiment", {})
    exp.setdefault("deterministic", False)
    exp.setdefault("cudnn_benchmark", True)
    exp.setdefault("amp", True)
    exp.setdefault("allow_tf32", True)

    training = config.setdefault("training", {})
    training.setdefault("num_workers", 4)
    training.setdefault("prefetch_factor", 4)

    return config
