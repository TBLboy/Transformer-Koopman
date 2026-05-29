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

    edmd = training.setdefault("edmd", {})
    pretrain = edmd.setdefault("pretrain", {})
    if pretrain.get("batch_size", 128) < 512:
        pretrain["batch_size"] = 1024

    compute = edmd.setdefault("compute", {})
    compute.setdefault("batch_size", 1024)
    compute.setdefault("batch_encode", True)

    e2e = training.setdefault("end_to_end", {})
    if e2e.get("batch_size", 128) < 512:
        e2e["batch_size"] = 1024

    return config
