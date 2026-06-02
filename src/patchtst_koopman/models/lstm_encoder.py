"""LSTM encoder for LSTM-Koopman baseline.

Same interface as :class:`PatchTSTEncoder` and :class:`MLPEncoder`: takes
``x_history`` of shape ``[B, P, n]`` and produces ``z = [x_t; LSTM(x_history)]``
of shape ``[B, d]``.

Unlike PatchTST which uses patches and attention, LSTM processes the raw
temporal sequence step-by-step, providing a pure recurrent baseline for
temporal lifting.
"""
import torch
import torch.nn as nn


class LSTMEncoder(nn.Module):
    """Lift the current state ``x_t`` with LSTM-encoded history features."""

    def __init__(self, config):
        super().__init__()
        self.n = config["data"]["state_dim"]
        self.d = config["lstm_koopman"]["latent_dim"]
        self.d_hidden = self.d - self.n  # LSTM feature output dimension

        lstm_cfg = config["lstm_koopman"]
        self.hidden_size = lstm_cfg["hidden_size"]
        self.n_layers = lstm_cfg["n_layers"]
        dropout = lstm_cfg.get("dropout", 0.0)
        bidirectional = lstm_cfg.get("bidirectional", False)

        # LSTM processes the state history sequence
        self.lstm = nn.LSTM(
            input_size=self.n,
            hidden_size=self.hidden_size,
            num_layers=self.n_layers,
            dropout=dropout if self.n_layers > 1 else 0.0,
            bidirectional=bidirectional,
            batch_first=True,
        )

        # Linear projection from LSTM hidden to feature dimension
        lstm_output_size = self.hidden_size * (2 if bidirectional else 1)
        self.projection = nn.Linear(lstm_output_size, self.d_hidden)

    def forward(self, x_history):
        """
        Args:
            x_history: [B, P, n] state history window

        Returns:
            z: [B, d] lifted state = [x_t; h_t]
        """
        # Extract current state
        x_t = x_history[:, -1, :]  # [B, n]

        # Process full history through LSTM
        # x_history: [B, P, n] -> LSTM -> output: [B, P, hidden_size]
        lstm_out, (h_n, c_n) = self.lstm(x_history)

        # Take the last hidden state
        # h_n: [n_layers * num_directions, B, hidden_size]
        if self.lstm.bidirectional:
            # Concatenate forward and backward hidden states from last layer
            h_last = torch.cat([h_n[-2], h_n[-1]], dim=1)  # [B, hidden_size*2]
        else:
            h_last = h_n[-1]  # [B, hidden_size]

        # Project to feature dimension
        h_t = self.projection(h_last)  # [B, d_hidden]

        # Concatenate current state with LSTM features
        z = torch.cat([x_t, h_t], dim=1)  # [B, d]

        return z
