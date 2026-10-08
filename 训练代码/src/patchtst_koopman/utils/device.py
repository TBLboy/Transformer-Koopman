"""Robust CUDA-availability resolver.

``torch.cuda.is_available()`` returning ``True`` does not guarantee that
kernels actually run — RTX 50-series GPUs need a CUDA build with ``sm_120``
support, and older PyTorch wheels silently fail at kernel launch time. This
helper does a real matmul and falls back to CPU on failure.
"""
import torch


def resolve_device(requested_device):
    """Return ``"cuda"`` only if a CUDA matmul actually executes."""
    if requested_device != "cuda":
        return requested_device

    if not torch.cuda.is_available():
        print("WARNING: device='cuda' requested but torch.cuda.is_available() is False; falling back to CPU")
        return "cpu"

    print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    print(f"PyTorch CUDA version: {torch.version.cuda}")

    try:
        x = torch.randn(128, 128, device="cuda")
        _ = x @ x
        torch.cuda.synchronize()
    except Exception as exc:
        print("WARNING: CUDA is visible but the kernel failed to launch.")
        print(f"  Error: {exc}")
        print("  Falling back to CPU; install a PyTorch build that supports this GPU.")
        return "cpu"

    return "cuda"
