"""Platform-specific baselines and ablation ranges.

Used by ``scripts/ablation/train_ablation.py`` to build the variant grid.
Extracted from the legacy ``train_ablation.py`` so the same constants can
be shared by the test/plot scripts.
"""


PLATFORM_CONFIGS = {
    "platform1": {
        "name": "Platform 1 (Flexible Manipulator)",
        "state_dim": 6,
        "control_dim": 3,
        "baseline": {
            "history_length": 16,
            "patch_length": 4,
            "latent_dim": 64,
            "d_model": 128,
        },
        "patch_ablations": [2, 8],
        "history_ablations": [8, 32],
        "n_layers_ablations": [1, 2, 4],
        "latent_dim_ablations": [32, 128],
    },
    "platform2": {
        "name": "Platform 2 (Soft Robot)",
        "state_dim": 2,
        "control_dim": 2,
        "baseline": {
            "history_length": 4,
            "patch_length": 2,
            "latent_dim": 10,
            "d_model": 16,
        },
        "patch_ablations": [1, 4],
        "history_ablations": [2, 8],
        "n_layers_ablations": [1, 2],
        "latent_dim_ablations": [4, 32],
    },
}


def get_platform_config(platform):
    """Lookup helper, raises ``ValueError`` for unknown platforms."""
    if platform not in PLATFORM_CONFIGS:
        raise ValueError(
            f"Unknown platform '{platform}'. Available: {list(PLATFORM_CONFIGS.keys())}"
        )
    return PLATFORM_CONFIGS[platform]
