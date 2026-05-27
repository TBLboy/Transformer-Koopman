"""Composite ablation models and factory functions.

The original project wired ablation variants like this:

.. code-block:: python

    model = nn.Module()                          # << bare nn.Module
    model.encoder = ...
    model.koopman = ...
    model.decoder = ...
    model.forward = lambda x, u: ...             # << lambda assigned in place

This works at runtime but breaks pickling, makes ``.state_dict()``
unreliable, and confuses tooling. This module replaces the pattern with a
single :class:`AblationModel` subclass plus 10 thin factory functions.
"""
import copy

import torch
import torch.nn as nn

from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
from patchtst_koopman.models.koopman_dynamics import KoopmanDynamics
from patchtst_koopman.models.linear_decoder import LinearDecoder

from .encoders import (
    NoAttentionEncoder,
    NoPatchEncoder,
    NoPositionalEncoder,
    PatchSizeAblationEncoder,
    PureFeatureEncoder,
    ReadoutAblationEncoder,
    WindowAblationEncoder,
)


class TrainableDecoder(nn.Module):
    """Learned linear decoder ``x = W z + b`` used by :class:`PureFeatureEncoder`.

    All other ablation variants stick with :class:`LinearDecoder`
    (``x = z[:, :n]``) because their encoders preserve the state-embedded
    structure.
    """

    def __init__(self, config):
        super().__init__()
        self.latent_dim = config["encoder"]["latent_dim"]
        self.state_dim = config["data"]["state_dim"]
        self.projection = nn.Linear(self.latent_dim, self.state_dim)

    def forward(self, z):
        return self.projection(z)


class AblationModel(nn.Module):
    """Generic ``encoder + koopman + decoder`` model used by every variant.

    Args:
        encoder: An ``nn.Module`` that maps ``[B, P, n]`` -> ``[B, d]``.
        koopman: An ``nn.Module`` with signature ``(z, u) -> z_next``.
        decoder: An ``nn.Module`` that maps ``[B, d]`` -> ``[B, n]``.
    """

    def __init__(self, encoder, koopman, decoder):
        super().__init__()
        self.encoder = encoder
        self.koopman = koopman
        self.decoder = decoder

    def forward(self, x_history, u_t):
        z_t = self.encoder(x_history)
        z_next = self.koopman(z_t, u_t)
        return self.decoder(z_next)

    def predict_multi_step(self, x_history, u_sequence):
        """Roll the model forward for ``u_sequence.shape[1]`` steps."""
        predictions = []
        current_history = x_history.clone()
        for h in range(u_sequence.shape[1]):
            x_next = self.forward(current_history, u_sequence[:, h, :])
            predictions.append(x_next)
            current_history = torch.cat(
                [current_history[:, 1:, :], x_next.unsqueeze(1)], dim=1
            )
        return torch.stack(predictions, dim=1)

    def get_koopman_matrices(self):
        return (
            self.koopman.A.detach().cpu().numpy(),
            self.koopman.B.detach().cpu().numpy(),
        )


def _deepcopy_config(config):
    return copy.deepcopy(config)


def _build_state_embedded(encoder, config):
    """Wrap an encoder with the shared Koopman + (fixed) linear decoder."""
    return AblationModel(
        encoder=encoder,
        koopman=KoopmanDynamics(config),
        decoder=LinearDecoder(config),
    )


# ── Factory functions ────────────────────────────────────────────────────


def create_full_model(config):
    """Baseline: the full PatchTST-Koopman model."""
    return PatchTSTKoopmanModel(config)


def create_no_patch(config):
    """Variant: drop the patch mechanism."""
    return _build_state_embedded(NoPatchEncoder(config), config)


def create_no_attention(config):
    """Variant: replace self-attention with FC layers."""
    return _build_state_embedded(NoAttentionEncoder(config), config)


def create_no_positional(config):
    """Variant: skip positional encoding."""
    return _build_state_embedded(NoPositionalEncoder(config), config)


def create_patch_size(config, patch_length):
    """Variant: use a different patch length."""
    cfg = _deepcopy_config(config)
    cfg["encoder"]["patch_length"] = patch_length
    encoder = PatchSizeAblationEncoder(cfg, patch_length=patch_length)
    return _build_state_embedded(encoder, cfg)


def create_window_length(config, history_length):
    """Variant: use a different history window length."""
    cfg = _deepcopy_config(config)
    cfg["encoder"]["history_length"] = history_length
    encoder = WindowAblationEncoder(cfg, history_length=history_length)
    return _build_state_embedded(encoder, cfg)


def create_readout(config, readout_method):
    """Variant: switch readout method (``mean`` / ``max`` / ``last``)."""
    encoder = ReadoutAblationEncoder(config, readout_method=readout_method)
    return _build_state_embedded(encoder, config)


def create_n_layers(config, n_layers):
    """Variant: change the number of Transformer encoder layers."""
    cfg = _deepcopy_config(config)
    cfg["encoder"]["n_layers"] = n_layers
    return PatchTSTKoopmanModel(cfg)


def create_latent_dim(config, latent_dim):
    """Variant: change the lifted (latent) dimension ``d``."""
    cfg = _deepcopy_config(config)
    cfg["encoder"]["latent_dim"] = latent_dim
    cfg["koopman"]["lifted_dim"] = latent_dim
    return PatchTSTKoopmanModel(cfg)


def create_pure_feature(config):
    """Variant: drop the state-embedded design and use a trainable decoder."""
    return AblationModel(
        encoder=PureFeatureEncoder(config),
        koopman=KoopmanDynamics(config),
        decoder=TrainableDecoder(config),
    )


ABLATION_MODELS = {
    "full_model": create_full_model,
    "no_patch": create_no_patch,
    "no_attention": create_no_attention,
    "no_positional": create_no_positional,
    "patch_L": create_patch_size,
    "history_P": create_window_length,
    "readout_max": lambda config: create_readout(config, "max"),
    "readout_last": lambda config: create_readout(config, "last"),
    "n_layers": create_n_layers,
    "latent_dim": create_latent_dim,
    "pure_feature": create_pure_feature,
}
