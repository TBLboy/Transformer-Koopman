"""MLP-Koopman model (control baseline).

Structurally identical to :class:`PatchTSTKoopmanModel` but with the
:class:`MLPEncoder` swapped in for the PatchTST encoder. The Koopman dynamics
and the (fixed) linear decoder are shared.
"""
import copy

import torch.nn as nn

from .mlp_encoder import MLPEncoder
from .koopman_dynamics import KoopmanDynamics
from .linear_decoder import LinearDecoder
from .rollout import KoopmanRolloutMixin


class MLPKoopmanModel(KoopmanRolloutMixin, nn.Module):
    """``x_next = decoder(koopman(MLPEncoder(history), u))``."""

    def __init__(self, config):
        super().__init__()
        # The Koopman dynamics and the decoder read latent_dim from
        # encoder.latent_dim; patch a *copy* from mlp_koopman.latent_dim so a
        # separate baseline config entry stays self-contained without mutating
        # the caller's config (ALN-011).
        config = self._patched_config(config)

        self.encoder = MLPEncoder(config)
        self.koopman = KoopmanDynamics(config)
        self.decoder = LinearDecoder(config)

    @staticmethod
    def _patched_config(config):
        """Return a copy of ``config`` with ``encoder.latent_dim`` aligned."""
        patched = copy.deepcopy(config)
        patched["encoder"]["latent_dim"] = patched["mlp_koopman"]["latent_dim"]
        return patched

    def forward(self, x_history, u_t):
        z_t = self.encoder(x_history)
        z_next = self.koopman(z_t, u_t)
        return self.decoder(z_next)
