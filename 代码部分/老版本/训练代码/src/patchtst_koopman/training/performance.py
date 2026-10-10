"""Shared GPU training defaults for long-running sweeps (ablation, etc.)."""
import copy


def apply_gpu_training_defaults(config):
    """Return a copy of ``config`` with GPU-friendly training settings filled in.

    The caller's config is left untouched (ALN-011); callers must use the
    returned value.
    """
    result = copy.deepcopy(config)
    exp = result.setdefault("experiment", {})
    exp.setdefault("deterministic", False)
    exp.setdefault("cudnn_benchmark", True)
    exp.setdefault("amp", True)
    exp.setdefault("allow_tf32", True)

    training = result.setdefault("training", {})
    training.setdefault("num_workers", 4)
    training.setdefault("prefetch_factor", 4)

    return result
