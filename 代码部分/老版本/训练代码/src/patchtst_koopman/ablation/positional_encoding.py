"""Backwards-compatible re-export of the shared :class:`PositionalEncoding`.

The canonical implementation lives in
``patchtst_koopman.utils.positional_encoding`` (ALN-010). This module is kept so
the ablation encoders and ``ablation/__init__.py`` can keep importing from
``..positional_encoding`` unchanged.
"""
from patchtst_koopman.utils.positional_encoding import PositionalEncoding

__all__ = ["PositionalEncoding"]
