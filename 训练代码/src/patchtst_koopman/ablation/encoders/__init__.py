"""Encoder variants used by ablation studies."""

from .no_patch import NoPatchEncoder
from .no_attention import NoAttentionEncoder
from .no_positional import NoPositionalEncoder
from .window import WindowAblationEncoder
from .patch_size import PatchSizeAblationEncoder
from .readout import ReadoutAblationEncoder
from .pure_feature import PureFeatureEncoder

__all__ = [
    "NoPatchEncoder",
    "NoAttentionEncoder",
    "NoPositionalEncoder",
    "WindowAblationEncoder",
    "PatchSizeAblationEncoder",
    "ReadoutAblationEncoder",
    "PureFeatureEncoder",
]
