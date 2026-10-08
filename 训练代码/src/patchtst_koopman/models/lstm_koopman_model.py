"""LSTM-Koopman model (temporal baseline).

Structurally identical to :class:`PatchTSTKoopmanModel` and :class:`MLPKoopmanModel`
but with the :class:`LSTMEncoder` that processes raw temporal sequences without
patching. The Koopman dynamics and the (fixed) linear decoder are shared.
"""
import copy

import torch.nn as nn

from .lstm_encoder import LSTMEncoder
from .koopman_dynamics import KoopmanDynamics
from .linear_decoder import LinearDecoder
from .rollout import KoopmanRolloutMixin


class LSTMKoopmanModel(KoopmanRolloutMixin, nn.Module):
    """``x_next = decoder(koopman(LSTMEncoder(history), u))``."""

    def __init__(self, config):
        super().__init__()
        # The Koopman dynamics and the decoder read latent_dim from
        # encoder.latent_dim; patch a *copy* from lstm_koopman.latent_dim so a
        # separate baseline config entry stays self-contained without mutating
        # the caller's config (ALN-011).
        config = self._patched_config(config)

        self.encoder = LSTMEncoder(config)
        self.koopman = KoopmanDynamics(config)
        self.decoder = LinearDecoder(config)

    @staticmethod
    def _patched_config(config):
        """Return a copy of ``config`` with ``encoder.latent_dim`` aligned."""
        patched = copy.deepcopy(config)
        patched["encoder"]["latent_dim"] = patched["lstm_koopman"]["latent_dim"]
        return patched

    def forward(self, x_history, u_t):
        z_t = self.encoder(x_history)
        z_next = self.koopman(z_t, u_t)
        return self.decoder(z_next)
