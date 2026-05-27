"""MLP-Koopman model (control baseline).

Structurally identical to :class:`PatchTSTKoopmanModel` but with the
:class:`MLPEncoder` swapped in for the PatchTST encoder. The Koopman dynamics
and the (fixed) linear decoder are shared.
"""
import torch
import torch.nn as nn

from .mlp_encoder import MLPEncoder
from .koopman_dynamics import KoopmanDynamics
from .linear_decoder import LinearDecoder


class MLPKoopmanModel(nn.Module):
    """``x_next = decoder(koopman(MLPEncoder(history), u))``."""

    def __init__(self, config):
        super().__init__()
        # The Koopman dynamics reads latent_dim from encoder.latent_dim;
        # patch it from mlp_koopman.latent_dim so a separate baseline config
        # entry stays self-contained.
        self._patch_config(config)

        self.encoder = MLPEncoder(config)
        self.koopman = KoopmanDynamics(config)
        self.decoder = LinearDecoder(config)

    @staticmethod
    def _patch_config(config):
        config["encoder"]["latent_dim"] = config["mlp_koopman"]["latent_dim"]

    def forward(self, x_history, u_t):
        z_t = self.encoder(x_history)
        z_next = self.koopman(z_t, u_t)
        return self.decoder(z_next)

    def predict_multi_step(self, x_history, u_sequence):
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
