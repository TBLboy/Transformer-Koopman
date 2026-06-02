"""LSTM-Koopman model (temporal baseline).

Structurally identical to :class:`PatchTSTKoopmanModel` and :class:`MLPKoopmanModel`
but with the :class:`LSTMEncoder` that processes raw temporal sequences without
patching. The Koopman dynamics and the (fixed) linear decoder are shared.
"""
import torch
import torch.nn as nn

from .lstm_encoder import LSTMEncoder
from .koopman_dynamics import KoopmanDynamics
from .linear_decoder import LinearDecoder


class LSTMKoopmanModel(nn.Module):
    """``x_next = decoder(koopman(LSTMEncoder(history), u))``."""

    def __init__(self, config):
        super().__init__()
        # The Koopman dynamics reads latent_dim from encoder.latent_dim;
        # patch it from lstm_koopman.latent_dim so a separate baseline config
        # entry stays self-contained.
        self._patch_config(config)

        self.encoder = LSTMEncoder(config)
        self.koopman = KoopmanDynamics(config)
        self.decoder = LinearDecoder(config)

    @staticmethod
    def _patch_config(config):
        config["encoder"]["latent_dim"] = config["lstm_koopman"]["latent_dim"]

    def forward(self, x_history, u_t):
        z_t = self.encoder(x_history)
        z_next = self.koopman(z_t, u_t)
        return self.decoder(z_next)

    def predict_multi_step(self, x_history, u_sequence):
        """Roll the model out for ``H`` steps.

        Args:
            x_history: ``[batch, P, n]`` initial history window.
            u_sequence: ``[batch, H, m]`` control inputs.

        Returns:
            ``[batch, H, n]`` predicted states.
        """
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
        """Return ``A`` and ``B`` as numpy arrays (detached)."""
        return (
            self.koopman.A.detach().cpu().numpy(),
            self.koopman.B.detach().cpu().numpy(),
        )
