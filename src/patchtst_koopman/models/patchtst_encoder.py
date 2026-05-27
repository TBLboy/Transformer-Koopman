"""PatchTST encoder.

Splits a history window of states into patches, embeds them via a linear layer,
adds sinusoidal positional encoding, runs a Transformer encoder, applies a
readout (mean/max/last), and projects to ``d_history = latent_dim - state_dim``.
The final output ``z`` is the *state-embedded* form ``[x_t; h_t]`` so the
decoder can be the fixed projection ``x = z[:, :n]``.
"""
import math

import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    """Standard sinusoidal positional encoding (no dropout)."""

    def __init__(self, d_model, max_len=5000):
        super().__init__()

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        self.register_buffer("pe", pe)

    def forward(self, x):
        return x + self.pe[:, : x.size(1), :]


class PatchTSTEncoder(nn.Module):
    """PatchTST encoder producing state-embedded latent ``z = [x_t; h_t]``.

    Input:  ``x_history`` of shape ``[batch, P, n]``
    Output: ``z`` of shape ``[batch, d]`` where ``d = latent_dim``
    """

    def __init__(self, config):
        super().__init__()
        self.P = config["encoder"]["history_length"]
        self.p = config["encoder"]["patch_length"]
        self.n = config["data"]["state_dim"]
        self.d = config["encoder"]["latent_dim"]
        self.d_model = config["encoder"]["d_model"]
        self.n_layers = config["encoder"]["n_layers"]
        self.n_heads = config["encoder"]["n_heads"]
        self.d_ff = config["encoder"]["d_ff"]
        self.dropout = config["encoder"]["dropout"]

        self.d_history = self.d - self.n
        self.num_patches = self.P // self.p

        self.patch_embedding = nn.Linear(self.p * self.n, self.d_model)
        self.positional_encoding = PositionalEncoding(self.d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.d_model,
            nhead=self.n_heads,
            dim_feedforward=self.d_ff,
            dropout=self.dropout,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=self.n_layers)

        readout_method = config["encoder"]["readout_method"]
        if readout_method == "mean":
            self.readout = lambda x: torch.mean(x, dim=1)
        elif readout_method == "max":
            self.readout = lambda x: torch.max(x, dim=1)[0]
        elif readout_method == "last":
            self.readout = lambda x: x[:, -1, :]
        else:
            raise ValueError(f"Unknown readout method: {readout_method}")

        self.projection = nn.Linear(self.d_model, self.d_history)

    def _create_patches(self, x_history):
        batch_size = x_history.shape[0]
        patches = x_history.reshape(batch_size, self.num_patches, self.p, self.n)
        patches = patches.reshape(batch_size, self.num_patches, self.p * self.n)
        return patches

    def forward(self, x_history):
        x_t = x_history[:, -1, :]  # current state pulled out for state embedding

        patches = self._create_patches(x_history)
        embedded = self.patch_embedding(patches)
        embedded = self.positional_encoding(embedded)
        encoded = self.transformer(embedded)
        pooled = self.readout(encoded)
        h_t = self.projection(pooled)

        return torch.cat([x_t, h_t], dim=1)
