"""Ablation models and encoder variants.

The legacy project hid an ``nn.Module() + lambda`` anti-pattern inside the
factory functions. This package replaces it with a regular
:class:`AblationModel` subclass plus 10 factory helpers.
"""

from .positional_encoding import PositionalEncoding
from .models import AblationModel
from .platform_configs import PLATFORM_CONFIGS, get_platform_config
from .models import (
    create_full_model,
    create_no_attention,
    create_no_patch,
    create_no_positional,
    create_window_length,
    create_patch_size,
    create_readout,
    create_pure_feature,
)

__all__ = [
    "PositionalEncoding",
    "AblationModel",
    "PLATFORM_CONFIGS",
    "get_platform_config",
    "create_full_model",
    "create_no_attention",
    "create_no_patch",
    "create_no_positional",
    "create_window_length",
    "create_patch_size",
    "create_readout",
    "create_pure_feature",
]
