"""Single source of truth for the sinusoidal :class:`PositionalEncoding` (ALN-010).

The legacy tree carried three copies: one in ``models/patchtst_encoder.py``, one
in ``ablation/positional_encoding.py`` and one in the standalone deploy model.
The first two are now this module; the deploy copy stays standalone (it must run
without the training package installed) but is pinned to this behaviour by
``tests/test_positional_encoding_consistency.py``.
"""
import math

import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    """Standard sinusoidal positional encoding (no dropout)."""

    def __init__(self, d_model, max_len=5000):
        super().__init__()
        dtype = torch.get_default_dtype()

        pe = torch.zeros(max_len, d_model, dtype=dtype)
        position = torch.arange(0, max_len, dtype=dtype).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=dtype) * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        self.register_buffer("pe", pe)

    def forward(self, x):
        return x + self.pe[:, : x.size(1), :]
