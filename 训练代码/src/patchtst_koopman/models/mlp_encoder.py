"""MLP encoder used by the MLP-Koopman baseline.

Same interface as :class:`PatchTSTEncoder`: takes ``x_history`` of shape
``[B, P, n]`` and produces ``z = [x_t; MLP(x_t)]`` of shape ``[B, d]``.
Only the last frame of the history window is consumed — the temporal
dependency that PatchTST exploits is intentionally dropped to expose the
contribution of the patched attention encoder.
"""
import torch
import torch.nn as nn


class MLPEncoder(nn.Module):
    """Lift the current state ``x_t`` with an MLP, keep ``x_t`` in the head."""

    def __init__(self, config):
        super().__init__()
        self.n = config["data"]["state_dim"]
        self.d = config["mlp_koopman"]["latent_dim"]
        self.d_hidden = self.d - self.n  # MLP output dimension

        mlp_cfg = config["mlp_koopman"]
        hidden_dims = mlp_cfg["hidden_dims"]
        activation = mlp_cfg.get("activation", "relu")
        dropout = mlp_cfg.get("dropout", 0.0)

        act_map = {"relu": nn.ReLU, "tanh": nn.Tanh, "elu": nn.ELU}
        Act = act_map.get(activation, nn.ReLU)

        layers = []
        in_dim = self.n
        for h_dim in hidden_dims:
            layers += [nn.Linear(in_dim, h_dim), Act()]
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            in_dim = h_dim
        layers.append(nn.Linear(in_dim, self.d_hidden))

        self.mlp = nn.Sequential(*layers)

    def forward(self, x_history):
        x_t = x_history[:, -1, :]
        h_t = self.mlp(x_t)
        return torch.cat([x_t, h_t], dim=1)
