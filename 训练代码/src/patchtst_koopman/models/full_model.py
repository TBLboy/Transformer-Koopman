"""Full PatchTST-Koopman model: encoder + Koopman + decoder."""
import torch.nn as nn

from .patchtst_encoder import PatchTSTEncoder
from .koopman_dynamics import KoopmanDynamics
from .linear_decoder import LinearDecoder
from .rollout import KoopmanRolloutMixin


class PatchTSTKoopmanModel(KoopmanRolloutMixin, nn.Module):
    """End-to-end model wired as ``x_next = decoder(koopman(encoder(history), u))``."""

    def __init__(self, config):
        super().__init__()
        self.config = config

        self.encoder = PatchTSTEncoder(config)
        self.koopman = KoopmanDynamics(config)
        self.decoder = LinearDecoder(config)

    def forward(self, x_history, u_t):
        z_t = self.encoder(x_history)
        z_next = self.koopman(z_t, u_t)
        return self.decoder(z_next)
