"""Export Platform 2 baseline controller assets to FlexibleArmControl34."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = PROJECT_ROOT / "experiment1"
DEFAULT_TARGET_DIR = Path(
    r"C:\Users\Windows\Desktop\FlexibleArmControl34\algorithms\tk_assets\model_assets"
)

NEURAL_MODELS = {
    "transformer": {
        "source": Path("Transformer-Koopman/platform2/model.pth"),
        "target": "platform2_transformer_model.pth",
    },
    "mlp": {
        "source": Path("MLP-Koopman/platform2/model.pth"),
        "target": "platform2_mlp_model.pth",
    },
    "lstm": {
        "source": Path("LSTM-Koopman/platform2/model.pth"),
        "target": "platform2_lstm_model.pth",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Platform 2 baseline controller assets")
    parser.add_argument("--source-root", type=str, default=str(DEFAULT_SOURCE_ROOT))
    parser.add_argument("--target-dir", type=str, default=str(DEFAULT_TARGET_DIR))
    return parser.parse_args()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)


def _as_list(array) -> list[float]:
    return np.asarray(array, dtype=np.float64).reshape(-1).tolist()


def export_neural_checkpoint(model_name: str, source: Path, target: Path) -> dict:
    if not source.exists():
        raise FileNotFoundError(f"Missing {model_name} checkpoint: {source}")

    shutil.copy2(source, target)
    checkpoint = torch.load(target, map_location="cpu", weights_only=False)
    normalization = checkpoint["normalization"]
    config = checkpoint["config"]

    metadata = {
        "model_name": model_name,
        "source_checkpoint": str(source),
        "target_checkpoint": str(target),
        "A_shape": list(np.asarray(checkpoint["koopman_A"]).shape),
        "B_shape": list(np.asarray(checkpoint["koopman_B"]).shape),
        "state_dim": config["data"]["state_dim"],
        "control_dim": config["data"]["control_dim"],
        "history_length": config["encoder"]["history_length"],
        "latent_dim": config["encoder"]["latent_dim"],
        "normalization_keys": list(normalization.keys()),
    }
    _write_json(target.with_name(f"platform2_{model_name}_metadata.json"), metadata)
    return {"config": config, "normalization": normalization}


def export_normalization(target_dir: Path, normalization: dict) -> None:
    payload = {
        "x_mean": _as_list(normalization["x_mean"]),
        "x_std": _as_list(normalization["x_std"]),
        "u_mean": _as_list(normalization["u_mean"]),
        "u_std": _as_list(normalization["u_std"]),
    }
    _write_json(target_dir / "platform2_normalization.json", payload)


def export_edmd_assets(source_root: Path, target_dir: Path, normalization: dict) -> None:
    source_dir = source_root / "EDMD-Koopman" / "platform2"
    if not source_dir.exists():
        raise FileNotFoundError(f"Missing EDMD asset directory: {source_dir}")

    target_dir.mkdir(parents=True, exist_ok=True)
    for filename in ["A_matrix.npy", "B_matrix.npy", "C_matrix.npy", "lifting_meta.npz", "results.npy"]:
        shutil.copy2(source_dir / filename, target_dir / filename)

    A = np.load(target_dir / "A_matrix.npy")
    B = np.load(target_dir / "B_matrix.npy")
    C = np.load(target_dir / "C_matrix.npy")
    meta = np.load(target_dir / "lifting_meta.npz", allow_pickle=True)
    metadata = {
        "model_name": "edmd",
        "source_dir": str(source_dir),
        "target_dir": str(target_dir),
        "A_shape": list(A.shape),
        "B_shape": list(B.shape),
        "C_shape": list(C.shape),
        "lifting_type": str(meta["lifting_type"]),
        "n_input": int(meta["n_input"]),
        "n_features": int(meta["n_features"]),
        "degree": int(meta["degree"]),
        "normalization_keys": list(normalization.keys()),
    }
    _write_json(target_dir / "platform2_edmd_metadata.json", metadata)


def main() -> None:
    args = parse_args()
    source_root = Path(args.source_root)
    target_dir = Path(args.target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    exported = {}
    transformer_payload = None
    for model_name, spec in NEURAL_MODELS.items():
        payload = export_neural_checkpoint(
            model_name,
            source_root / spec["source"],
            target_dir / spec["target"],
        )
        exported[model_name] = str(target_dir / spec["target"])
        if model_name == "transformer":
            transformer_payload = payload

    if transformer_payload is None:
        raise RuntimeError("Transformer payload missing; cannot export normalization")

    export_normalization(target_dir, transformer_payload["normalization"])
    export_edmd_assets(source_root, target_dir / "platform2_edmd", transformer_payload["normalization"])
    exported["edmd"] = str(target_dir / "platform2_edmd")

    _write_json(
        target_dir / "platform2_asset_export_summary.json",
        {
            "source_root": str(source_root),
            "target_dir": str(target_dir),
            "exported": exported,
        },
    )

    print("Exported baseline controller assets:")
    for name, path in exported.items():
        print(f"  {name}: {path}")
    print(f"  normalization: {target_dir / 'platform2_normalization.json'}")


if __name__ == "__main__":
    main()
