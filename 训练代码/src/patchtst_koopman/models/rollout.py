"""Shared rollout helpers for the Koopman models (ALN-010).

``PatchTSTKoopmanModel``, ``MLPKoopmanModel``, ``LSTMKoopmanModel`` and the
ablation ``AblationModel`` all carried byte-identical copies of
``predict_multi_step`` and ``get_koopman_matrices`` (and the full model a
private ``roll_out_latent``). They now inherit :class:`KoopmanRolloutMixin`, so
the rollout semantics live in exactly one place and cannot drift apart.

The mixin assumes the host class exposes:

* ``forward(x_history, u_t) -> x_next``
* ``koopman`` with ``.A`` / ``.B`` parameters
"""
import torch


class KoopmanRolloutMixin:
    """History-window rollout and detached Koopman-matrix access."""

    def predict_multi_step(self, x_history, u_sequence):
        """Roll the model out for ``H = u_sequence.shape[1]`` steps.

        Each step re-encodes the sliding history window, so this is the
        "physical" rollout used for the multi-step prediction loss.

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

        Unlike :meth:`predict_multi_step`, this does **not** re-encode history
        windows — it just propagates ``z`` through ``A`` and ``B``.

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
