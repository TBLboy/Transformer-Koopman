"""Ablation variant: encoder without self-attention.

Replaces the Transformer encoder with a stack of fully-connected layers.
Used to expose the contribution of self-attention to temporal modelling.
"""
import torch
import torch.nn as nn

from ..positional_encoding import PositionalEncoding


class NoAttentionEncoder(nn.Module):
    """Encoder where attention is replaced by FC layers."""

    def __init__(self, config):
        super().__init__()

        self.history_length = config["encoder"]["history_length"]
        self.state_dim = config["data"]["state_dim"]
        self.patch_length = config["encoder"]["patch_length"]
        self.n_patches = self.history_length // self.patch_length
        self.latent_dim = config["encoder"]["latent_dim"]
        self.d_model = config["encoder"]["d_model"]

        self.d_history = self.latent_dim - self.state_dim

        self.patch_embedding = nn.Linear(
            self.patch_length * self.state_dim,
            self.d_model,
        )
        self.pos_encoder = PositionalEncoding(d_model=self.d_model)

        self.fc_layers = nn.Sequential(
            nn.Linear(self.d_model, self.d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(self.d_model, self.d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
        )

        self.readout_method = config["encoder"].get("readout_method", "mean")
        self.output_projection = nn.Linear(self.d_model, self.d_history)

    def forward(self, x):
        x_t = x[:, -1, :]
        batch_size = x.shape[0]

        x = x.reshape(batch_size, self.n_patches, -1)
        x = self.patch_embedding(x)
        x = self.pos_encoder(x)
        x = self.fc_layers(x)

        if self.readout_method == "mean":
            x = x.mean(dim=1)
        elif self.readout_method == "max":
            x = x.max(dim=1)[0]
        elif self.readout_method == "last":
            x = x[:, -1, :]

        h_t = self.output_projection(x)
        return torch.cat([x_t, h_t], dim=1)
