"""Runtime lifting utilities for the Transformer-Koopman controller."""
from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Union

import numpy as np
import torch

from algorithms.tk_assets.transformer_koopman_model import PatchTSTKoopmanModel


class StateHistoryBuffer:
    """Fixed-length buffer that always returns a full ``P x n`` window.

    During start-up the buffer is shorter than ``history_length``; we
    left-pad with the earliest available state so the encoder still sees
    the expected tensor shape.
    """

    def __init__(self, history_length: int, state_dim: int):
        self.history_length = history_length
        self.state_dim = state_dim
        self._buffer: deque[np.ndarray] = deque(maxlen=history_length)

    def reset(self) -> None:
        self._buffer.clear()

    def push(self, x_norm: np.ndarray) -> None:
        x = np.asarray(x_norm, dtype=np.float32).reshape(self.state_dim)
        self._buffer.append(x)

    def get_window(self) -> np.ndarray:
        if not self._buffer:
            raise RuntimeError("History buffer is empty.")
        values = list(self._buffer)
        if len(values) < self.history_length:
            pad_count = self.history_length - len(values)
            values = [values[0]] * pad_count + values
        return np.stack(values[-self.history_length :], axis=0).astype(np.float32)


class TransformerKoopmanLifter:
    """Loads a trained checkpoint and exposes the online lifting interface."""

    def __init__(self, asset_dir: Union[str, Path], device: str = "cuda"):
        self.asset_dir = Path(asset_dir)
        self.checkpoint_path = self.asset_dir / "platform2_full_model.pth"
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(
                f"Transformer-Koopman checkpoint not found: {self.checkpoint_path}"
            )

        self.device = self._resolve_device(device)
        checkpoint = torch.load(
            self.checkpoint_path, map_location=self.device, weights_only=False
        )

        self.config = checkpoint["config"]
        self.config["experiment"]["device"] = self.device
        self.model = PatchTSTKoopmanModel(self.config)
        self.model.load_state_dict(checkpoint["model_state_dict"], strict=False)
        self.model = self.model.to(self.device).float()
        self.model.eval()

        self.A = np.asarray(checkpoint["koopman_A"], dtype=np.float32)
        self.B = np.asarray(checkpoint["koopman_B"], dtype=np.float32)

        norm = checkpoint["normalization"]
        self.x_mean = np.asarray(norm["x_mean"], dtype=np.float32).reshape(-1)
        self.x_std = np.asarray(norm["x_std"], dtype=np.float32).reshape(-1)
        self.u_mean = np.asarray(norm["u_mean"], dtype=np.float32).reshape(-1)
        self.u_std = np.asarray(norm["u_std"], dtype=np.float32).reshape(-1)

        self.P = int(self.config["encoder"]["history_length"])
        self.n = int(self.config["data"]["state_dim"])
        self.d = int(self.config["encoder"]["latent_dim"])
        self.m = int(self.config["data"]["control_dim"])
        self.buffer = StateHistoryBuffer(self.P, self.n)

    @staticmethod
    def _resolve_device(requested_device: str) -> str:
        if requested_device == "cuda" and torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def reset(self) -> None:
        self.buffer.reset()

    def normalize_state(self, x) -> np.ndarray:
        x_arr = np.asarray(x, dtype=np.float32).reshape(self.n)
        return (x_arr - self.x_mean) / self.x_std

    def denormalize_control(self, u_norm: np.ndarray) -> np.ndarray:
        u_arr = np.asarray(u_norm, dtype=np.float32).reshape(self.m)
        return u_arr * self.u_std + self.u_mean

    def push_current_state(self, current_pos) -> np.ndarray:
        x_norm = self.normalize_state(current_pos)
        self.buffer.push(x_norm)
        return self.buffer.get_window()

    def lift_window_norm(self, window_norm: np.ndarray) -> np.ndarray:
        window = np.asarray(window_norm, dtype=np.float32).reshape(self.P, self.n)
        with torch.no_grad():
            x_tensor = torch.tensor(
                window, dtype=torch.float32, device=self.device
            ).unsqueeze(0)
            z = self.model.encoder(x_tensor)
        return z.squeeze(0).detach().cpu().numpy().astype(np.float32)

    def lift_current(self, current_pos) -> np.ndarray:
        window = self.push_current_state(current_pos)
        return self.lift_window_norm(window)

    def build_reference_window(self, trajectory_sequence, current_step, shift: int = 0) -> np.ndarray:
        if not trajectory_sequence:
            raise ValueError("trajectory_sequence is empty.")
        end_idx = current_step + shift
        refs = []
        for idx in range(end_idx - self.P + 1, end_idx + 1):
            clamped = min(max(idx, 0), len(trajectory_sequence) - 1)
            refs.append(self.normalize_state(trajectory_sequence[clamped]))
        return np.stack(refs, axis=0).astype(np.float32)

    def lift_reference(self, trajectory_sequence, current_step, shift: int = 0) -> np.ndarray:
        window = self.build_reference_window(trajectory_sequence, current_step, shift=shift)
        return self.lift_window_norm(window)
