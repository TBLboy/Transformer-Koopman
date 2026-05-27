"""Ablation variant: pure-feature output (no state embedding).

The main encoder outputs ``z = [x_t; h_t]`` so the linear decoder
``C = [I_n | 0]`` is exact. This variant drops the state-embedding and
emits a pure learned feature vector ``z = h``. Used to expose the value of
the state-embedded design choice.
"""
import torch.nn as nn

from ..positional_encoding import PositionalEncoding


class PureFeatureEncoder(nn.Module):
    """Pure-feature encoder — output is purely learned, no ``x_t`` in the head.

    The ablation training pipeline detects this via the boolean flag
    ``use_state_embedding`` and replaces the fixed decoder with a learned
    linear projection.
    """

    def __init__(self, config):
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

        self.patch_embedding = nn.Linear(
            self.patch_length * self.state_dim,
            self.d_model,
        )
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
        self.output_projection = nn.Linear(self.d_model, self.latent_dim)

        # Signal to AblationModel that we need a learnable decoder.
        self.use_state_embedding = False

    def forward(self, x):
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

        return self.output_projection(x)
