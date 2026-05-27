"""Ablation variant: configurable readout (mean / max / last)."""
import torch
import torch.nn as nn

from ..positional_encoding import PositionalEncoding


class ReadoutAblationEncoder(nn.Module):
    """PatchTST encoder with overridable readout method."""

    def __init__(self, config, readout_method=None):
        super().__init__()

        self.history_length = config["encoder"]["history_length"]
        self.state_dim = config["data"]["state_dim"]
        self.patch_length = config["encoder"]["patch_length"]
        self.n_patches = self.history_length // self.patch_length
        self.latent_dim = config["encoder"]["latent_dim"]
        self.d_model = config["encoder"]["d_model"]
        self.n_layers = config["encoder"]["n_layers"]
        self.n_heads = config["encoder"]["n_heads"]
        self.d_ff = config["encoder"]["d_ff"]
        self.dropout = config["encoder"]["dropout"]

        self.readout_method = readout_method or config["encoder"].get("readout_method", "mean")
        self.d_history = self.latent_dim - self.state_dim

        self.patch_embedding = nn.Linear(self.patch_length * self.state_dim, self.d_model)
        self.pos_encoder = PositionalEncoding(d_model=self.d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.d_model,
            nhead=self.n_heads,
            dim_feedforward=self.d_ff,
            dropout=self.dropout,
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=self.n_layers)

        self.output_projection = nn.Linear(self.d_model, self.d_history)

    def set_readout_method(self, method):
        self.readout_method = method

    def forward(self, x):
        x_t = x[:, -1, :]
        batch_size = x.shape[0]

        x = x.reshape(batch_size, self.n_patches, -1)
        x = self.patch_embedding(x)
        x = self.pos_encoder(x)
        x = self.transformer_encoder(x)

        if self.readout_method == "mean":
            x = x.mean(dim=1)
        elif self.readout_method == "max":
            x = x.max(dim=1)[0]
        elif self.readout_method == "last":
            x = x[:, -1, :]

        h_t = self.output_projection(x)
        return torch.cat([x_t, h_t], dim=1)
