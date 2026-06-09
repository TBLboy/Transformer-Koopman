"""Full PatchTST-Koopman model: encoder + Koopman + decoder."""
import torch
import torch.nn as nn

from .patchtst_encoder import PatchTSTEncoder
from .koopman_dynamics import KoopmanDynamics
from .linear_decoder import LinearDecoder


class PatchTSTKoopmanModel(nn.Module):
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

    def roll_out_latent(self, z_k, u_sequence):
        """Autoregressive Koopman rollout in latent space only.

        Unlike ``predict_multi_step``, this does **not** re-encode
        history windows — it just propagates ``z`` through ``A`` and ``B``.

        Args:
            z_k: ``[batch, d]`` initial latent state.
            u_sequence: ``[batch, H, m]`` control inputs.

        Returns:
            ``[batch, H, d]`` predicted latent states for steps 1..H.
        """
        z_seq = []
        z_cur = z_k
        for i in range(u_sequence.shape[1]):
            z_cur = self.koopman(z_cur, u_sequence[:, i, :])
            z_seq.append(z_cur)
        return torch.stack(z_seq, dim=1)

    def get_koopman_matrices(self):
        """Return ``A`` and ``B`` as numpy arrays (detached)."""
        return (
            self.koopman.A.detach().cpu().numpy(),
            self.koopman.B.detach().cpu().numpy(),
        )
