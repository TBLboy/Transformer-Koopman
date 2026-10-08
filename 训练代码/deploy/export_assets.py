"""Export Platform 2 Transformer-Koopman assets for upper-computer deployment.

Copies a trained checkpoint into ``deploy/algorithms/tk_assets/model_assets/``
and writes a ``platform2_metadata.json`` summary file.

Usage:
    python deploy/export_assets.py \\
        --source results/models/ablation_platform2/<run_id>/full_model/full_model_model.pth
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import torch


def parse_args():
    parser = argparse.ArgumentParser(description="Export Platform 2 controller assets")
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Path to the trained checkpoint (*.pth)",
    )
    parser.add_argument(
        "--asset_dir",
        type=str,
        default=None,
        help="Destination directory (default: deploy/algorithms/tk_assets/model_assets/ next to this script)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    source = Path(args.source)
    if not source.exists():
        raise FileNotFoundError(f"Missing checkpoint: {source}")

    if args.asset_dir:
        asset_dir = Path(args.asset_dir)
    else:
        asset_dir = Path(__file__).resolve().parent / "algorithms" / "tk_assets" / "model_assets"

    asset_dir.mkdir(parents=True, exist_ok=True)
    target_checkpoint = asset_dir / "platform2_full_model.pth"

    shutil.copy2(source, target_checkpoint)
    checkpoint = torch.load(target_checkpoint, map_location="cpu", weights_only=False)

    metadata = {
        "source_checkpoint": str(source),
        "target_checkpoint": str(target_checkpoint),
        "A_shape": list(checkpoint["koopman_A"].shape),
        "B_shape": list(checkpoint["koopman_B"].shape),
        "state_dim": checkpoint["config"]["data"]["state_dim"],
        "control_dim": checkpoint["config"]["data"]["control_dim"],
        "history_length": checkpoint["config"]["encoder"]["history_length"],
        "patch_length": checkpoint["config"]["encoder"]["patch_length"],
        "latent_dim": checkpoint["config"]["encoder"]["latent_dim"],
        "d_model": checkpoint["config"]["encoder"]["d_model"],
        "n_layers": checkpoint["config"]["encoder"]["n_layers"],
        "n_heads": checkpoint["config"]["encoder"]["n_heads"],
        "normalization_keys": list(checkpoint["normalization"].keys()),
    }
    metadata_path = asset_dir / "platform2_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

    print("Exported controller assets:")
    print(f"  {target_checkpoint}")
    print(f"  {metadata_path}")


if __name__ == "__main__":
    main()
