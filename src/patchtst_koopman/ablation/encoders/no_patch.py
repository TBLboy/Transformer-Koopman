"""Ablation variant: encoder without the patch mechanism.

Replaces the patch embedding with a per-timestep linear projection, then
feeds the full ``P``-long sequence directly into the Transformer encoder.
Used to show the contribution of patch-averaging to noise robustness.
"""
import torch
import torch.nn as nn

from ..positional_encoding import PositionalEncoding


class NoPatchEncoder(nn.Module):
    """Encoder without patching — embeds every raw timestep individually.

    Output is state-embedded: ``z = [x_t; h_t]`` of shape ``[B, d]``.
    """

    def __init__(self, config):
        super().__init__()

        self.history_length = config["encoder"]["history_length"]
        self.state_dim = config["data"]["state_dim"]
        self.latent_dim = config["encoder"]["latent_dim"]
        self.d_model = config["encoder"]["d_model"]
        self.n_layers = config["encoder"]["n_layers"]
        self.n_heads = config["encoder"]["n_heads"]
        self.d_ff = config["encoder"]["d_ff"]
        self.dropout = config["encoder"]["dropout"]

        self.d_history = self.latent_dim - self.state_dim

        self.input_embedding = nn.Linear(self.state_dim, self.d_model)
        self.pos_encoder = PositionalEncoding(d_model=self.d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.d_model,
            nhead=self.n_heads,
            dim_feedforward=self.d_ff,
            dropout=self.dropout,
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=self.n_layers)

        self.readout_method = config["encoder"].get("readout_method", "mean")
        self.output_projection = nn.Linear(self.d_model, self.d_history)

    def forward(self, x):
        x_t = x[:, -1, :]

        x = self.input_embedding(x)
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
