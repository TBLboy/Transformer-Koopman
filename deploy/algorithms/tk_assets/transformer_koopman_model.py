"""Standalone PatchTST-Koopman model used by the upper-computer runtime.

These classes mirror the training-time implementation in
``patchtst_koopman.models`` so a saved checkpoint can be loaded directly
inside ``FlexibleArmControl34`` without depending on the full training
package being installed there.
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1), :]


class PatchTSTEncoder(nn.Module):
    def __init__(self, config: dict):
        super().__init__()
        self.P = config["encoder"]["history_length"]
        self.p = config["encoder"]["patch_length"]
        self.n = config["data"]["state_dim"]
        self.d = config["encoder"]["latent_dim"]
        self.d_model = config["encoder"]["d_model"]
        self.n_layers = config["encoder"]["n_layers"]
        self.n_heads = config["encoder"]["n_heads"]
        self.d_ff = config["encoder"]["d_ff"]
        self.dropout = config["encoder"].get("dropout", 0.1)

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

        readout_method = config["encoder"].get("readout_method", "mean")
        if readout_method == "mean":
            self.readout = lambda x: torch.mean(x, dim=1)
        elif readout_method == "max":
            self.readout = lambda x: torch.max(x, dim=1)[0]
        elif readout_method == "last":
            self.readout = lambda x: x[:, -1, :]
        else:
            raise ValueError(f"Unknown readout method: {readout_method}")

        self.projection = nn.Linear(self.d_model, self.d_history)

    def _create_patches(self, x_history: torch.Tensor) -> torch.Tensor:
        batch_size = x_history.shape[0]
        patches = x_history.reshape(batch_size, self.num_patches, self.p, self.n)
        patches = patches.reshape(batch_size, self.num_patches, self.p * self.n)
        return patches

    def forward(self, x_history: torch.Tensor) -> torch.Tensor:
        x_t = x_history[:, -1, :]
        patches = self._create_patches(x_history)
        embedded = self.patch_embedding(patches)
        embedded = self.positional_encoding(embedded)
        encoded = self.transformer(embedded)
        pooled = self.readout(encoded)
        h_t = self.projection(pooled)
        return torch.cat([x_t, h_t], dim=1)


class KoopmanDynamics(nn.Module):
    def __init__(self, config: dict):
        super().__init__()
        self.d = config["encoder"]["latent_dim"]
        self.m = config["data"]["control_dim"]
        self.rho_max = config["koopman"].get("rho_max", 0.9999)
        self.A = nn.Parameter(torch.eye(self.d))
        self.B = nn.Parameter(torch.zeros(self.d, self.m))

    def forward(self, z_t: torch.Tensor, u_t: torch.Tensor) -> torch.Tensor:
        return torch.matmul(z_t, self.A.T) + torch.matmul(u_t, self.B.T)


class LinearDecoder(nn.Module):
    def __init__(self, config: dict):
        super().__init__()
        self.n = config["data"]["state_dim"]

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return z[:, : self.n]


class PatchTSTKoopmanModel(nn.Module):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.encoder = PatchTSTEncoder(config)
        self.koopman = KoopmanDynamics(config)
        self.decoder = LinearDecoder(config)

    def forward(self, x_history: torch.Tensor, u_t: torch.Tensor) -> torch.Tensor:
        z_t = self.encoder(x_history)
        z_next = self.koopman(z_t, u_t)
        return self.decoder(z_next)
