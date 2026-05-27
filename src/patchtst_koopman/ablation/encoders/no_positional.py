"""Ablation variant: encoder without positional encoding.

Full patch + Transformer architecture, but the sinusoidal positional
encoding step is removed. Tests whether self-attention alone can recover
temporal ordering.
"""
import torch
import torch.nn as nn


class NoPositionalEncoder(nn.Module):
    """Patch-based encoder that skips positional encoding."""

    def __init__(self, config):
        super().__init__()

        self.history_length = config["encoder"]["history_length"]
        self.state_dim = config["data"]["state_dim"]
        self.patch_length = config["encoder"]["patch_length"]
        self.num_patches = self.history_length // self.patch_length
        self.latent_dim = config["encoder"]["latent_dim"]
        self.d_model = config["encoder"]["d_model"]
        self.n_layers = config["encoder"]["n_layers"]
        self.n_heads = config["encoder"]["n_heads"]
        self.d_ff = config["encoder"]["d_ff"]
        self.dropout = config["encoder"]["dropout"]

        self.d_history = self.latent_dim - self.state_dim

        self.patch_embedding = nn.Linear(self.patch_length * self.state_dim, self.d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.d_model,
            nhead=self.n_heads,
            dim_feedforward=self.d_ff,
            dropout=self.dropout,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=self.n_layers)

        self.readout_method = config["encoder"].get("readout_method", "mean")
        self.projection = nn.Linear(self.d_model, self.d_history)

    def _create_patches(self, x_history):
        batch_size = x_history.shape[0]
        patches = x_history.reshape(batch_size, self.num_patches, self.patch_length, self.state_dim)
        patches = patches.reshape(batch_size, self.num_patches, self.patch_length * self.state_dim)
        return patches

    def forward(self, x_history):
        x_t = x_history[:, -1, :]

        patches = self._create_patches(x_history)
        embedded = self.patch_embedding(patches)
        # No positional encoding step here.
        encoded = self.transformer(embedded)

        if self.readout_method == "mean":
            pooled = torch.mean(encoded, dim=1)
        elif self.readout_method == "max":
            pooled = torch.max(encoded, dim=1)[0]
        elif self.readout_method == "last":
            pooled = encoded[:, -1, :]
        else:
            raise ValueError(f"Unknown readout method: {self.readout_method}")

        h_t = self.projection(pooled)
        return torch.cat([x_t, h_t], dim=1)
