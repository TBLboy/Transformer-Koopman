"""Fixed linear decoder for the state-embedded encoder.

``z = [x_t; h_t]`` so the decoder is simply ``C = [I_n | 0]`` — no trainable
parameters. This guarantees ``x = C z`` holds exactly and removes one source
of fitting error from the pipeline.
"""
import torch.nn as nn


class LinearDecoder(nn.Module):
    """Extract the first ``n`` dimensions of ``z`` as ``x``."""

    def __init__(self, config):
        super().__init__()
        self.d = config["encoder"]["latent_dim"]
        self.n = config["data"]["state_dim"]

    def forward(self, z):
        return z[:, : self.n]
