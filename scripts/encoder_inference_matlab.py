"""Encoder-only inference adapter for MATLAB / Simulink integration.

Data flow:
    MATLAB matrix [P, n]  ->  NumPy [P, n] (float64)
        ->  PyTorch tensor [1, P, n] (configurable dtype)
        ->  encoder forward  ->  PyTorch tensor [1, d]
        ->  NumPy [d] (float64)  ->  MATLAB column vector [d, 1]

Usage from MATLAB::

    pyrun("from scripts.encoder_inference_matlab import init_encoder, lift")
    pyrun("init_encoder('results/models/encoder_20260321.pth', 'configs/platform2.yaml')")
    z = pyrun("lift(x_history)", "z", x_history=mat);
"""
import os

import numpy as np
import torch

from patchtst_koopman.models.patchtst_encoder import PatchTSTEncoder
from patchtst_koopman.utils.config_loader import load_config


class EncoderInference:
    """Stateless encoder wrapper that produces a single lifted vector per call."""

    def __init__(self, encoder_path, config_path):
        print("[EncoderInference] initialising...")
        self.config = load_config(config_path)
        self.device = "cpu"
        precision = self.config["experiment"].get("precision", "float32")
        self.dtype = torch.float64 if precision == "float64" else torch.float32

        print(f"  Device:    {self.device}")
        print(f"  Precision: {precision}")

        checkpoint = torch.load(encoder_path, map_location=self.device, weights_only=False)
        self.encoder = PatchTSTEncoder(self.config)
        self.encoder.load_state_dict(checkpoint["encoder_state_dict"])
        self.encoder.to(self.device).eval()

        self.history_length = checkpoint["history_length"]
        self.input_dim = checkpoint["input_dim"]
        self.output_dim = checkpoint["output_dim"]
        self.norm_stats = checkpoint.get("norm_stats")

        print(f"  History length: {self.history_length}")
        print(f"  Input dim:      {self.input_dim}")
        print(f"  Output dim:     {self.output_dim}")
        print(f"  Parameters:     {sum(p.numel() for p in self.encoder.parameters()):,}")
        print("[EncoderInference] ready")

    def lift(self, x_history):
        """Lift a single history window to a feature vector ``z`` of shape ``[d]``."""
        if isinstance(x_history, list):
            x_history = np.array(x_history, dtype=np.float64)
        elif isinstance(x_history, np.ndarray):
            x_history = x_history.astype(np.float64)
        else:
            raise TypeError(f"Unsupported input type: {type(x_history)}")

        if x_history.ndim != 2:
            raise ValueError(f"Expected a 2D array, got {x_history.ndim}D")
        if x_history.shape[0] != self.history_length:
            raise ValueError(
                f"History length mismatch: expected {self.history_length}, got {x_history.shape[0]}"
            )
        if x_history.shape[1] != self.input_dim:
            raise ValueError(
                f"State dim mismatch: expected {self.input_dim}, got {x_history.shape[1]}"
            )

        x_tensor = torch.tensor(
            x_history, dtype=self.dtype, device=self.device
        ).unsqueeze(0)

        with torch.no_grad():
            z_tensor = self.encoder(x_tensor)

        return z_tensor.squeeze(0).cpu().numpy().astype(np.float64)


_encoder_instance = None


def init_encoder(encoder_path, config_path):
    """Initialise the global encoder used by :func:`lift`."""
    global _encoder_instance
    _encoder_instance = EncoderInference(encoder_path, config_path)


def lift(x_history):
    """Lift ``x_history`` using the global encoder. Raises until ``init_encoder``."""
    if _encoder_instance is None:
        raise RuntimeError(
            "Encoder not initialised; call init_encoder(encoder_path, config_path) first"
        )
    return _encoder_instance.lift(x_history)


def get_encoder_info():
    """Return metadata about the loaded encoder."""
    if _encoder_instance is None:
        raise RuntimeError("Encoder not initialised")
    return {
        "history_length": _encoder_instance.history_length,
        "input_dim": _encoder_instance.input_dim,
        "output_dim": _encoder_instance.output_dim,
        "dtype": str(_encoder_instance.dtype),
        "device": _encoder_instance.device,
    }


def _self_test(encoder_path, config_path):
    """Round-trip a random window through the encoder; for debugging only."""
    init_encoder(encoder_path, config_path)
    info = get_encoder_info()
    print(f"\nEncoder info: {info}")

    P, n = info["history_length"], info["input_dim"]
    x_np = np.random.randn(P, n).astype(np.float64)
    z_from_np = lift(x_np)
    z_from_list = lift(x_np.tolist())

    print(f"  output shape: {z_from_np.shape}, range [{z_from_np.min():.6f}, {z_from_np.max():.6f}]")
    print(f"  np vs list max diff: {np.abs(z_from_np - z_from_list).max():.2e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Self-test the encoder inference adapter")
    parser.add_argument("--encoder", type=str, required=True, help="Path to encoder checkpoint")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config")
    args = parser.parse_args()
    if not os.path.exists(args.encoder):
        raise SystemExit(f"Encoder checkpoint not found: {args.encoder}")
    _self_test(args.encoder, args.config)
