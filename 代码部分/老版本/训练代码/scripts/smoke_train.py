"""End-to-end smoke run of the M1 (EDMD) path on a small contiguous slice.

Purpose: a fast anchor that exercises the real pipeline - config load, dataset
construction, model build, EDMD stages 0/1/2 - without a full training run. It is
the safety net the migration is validated against; a full run is a separate job.

The slice is taken from inside a single recording so that history windows and
multi-step targets stay within one trajectory, exactly as ``KoopmanDataset``
requires.

Usage (from ``训练代码/``)::

    python scripts/smoke_train.py
    python scripts/smoke_train.py --config configs/platform1.yaml --rows 1500
"""
from __future__ import annotations

import argparse
import copy
import sys
import tempfile
from pathlib import Path

import numpy as np

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))


def make_slice_split(src_path, dst_path, rows):
    """Write a single-trajectory slice of ``src_path`` to ``dst_path``."""
    with np.load(src_path) as data:
        x, u, t, tid = data["x"], data["u"], data["t"], data["trajectory_id"]
    first = int(tid[0])
    keep = (tid == first)
    n = min(rows, int(keep.sum()))
    payload = {
        "x": x[keep][:n].copy(),
        "u": u[keep][:n].copy(),
        "t": t[keep][:n].copy(),
        "trajectory_id": np.zeros(n, dtype=np.int32),
    }
    np.savez(dst_path, **payload)
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="configs/platform1.yaml")
    ap.add_argument("--rows", type=int, default=2000)
    ap.add_argument("--val-rows", type=int, default=800)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args(argv)

    import torch

    from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
    from patchtst_koopman.training.edmd_trainer import EDMDTrainer
    from patchtst_koopman.utils.config_loader import load_config
    from patchtst_koopman.utils.data_prep import prepare_datasets
    from patchtst_koopman.utils.device import resolve_device
    from patchtst_koopman.utils.seed import set_seed

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = PROJECT_DIR / config_path
    config = load_config(str(config_path))

    datasets_dir = PROJECT_DIR / "data" if False else None  # keep paths explicit below
    data_dir = (PROJECT_DIR / config["data"]["data_dir"]).resolve()

    with tempfile.TemporaryDirectory(prefix="koopman_smoke_") as tmp:
        tmp_path = Path(tmp)
        n_train = make_slice_split(data_dir / config["data"]["train_file"],
                                   tmp_path / "train.npz", args.rows)
        n_val = make_slice_split(data_dir / config["data"]["val_file"],
                                 tmp_path / "val.npz", args.val_rows)
        n_test = make_slice_split(data_dir / config["data"]["test_file"],
                                  tmp_path / "test.npz", min(args.val_rows, 400))
        print(f"[smoke] slice: train={n_train} rows, val={n_val} rows, "
              f"test={n_test} rows (single trajectory each)")

        config = copy.deepcopy(config)
        config["data"]["data_dir"] = str(tmp_path)
        config["experiment"]["device"] = resolve_device(args.device)
        config["experiment"]["amp"] = False
        config["experiment"]["num_workers"] = 0
        config["training"]["edmd"]["pretrain"]["num_epochs"] = args.epochs
        config["training"]["edmd"]["pretrain"]["early_stopping"] = False
        config["experiment"]["save_dir"] = str(tmp_path / "models")

        set_seed(config["experiment"]["seed"])
        torch.set_default_dtype(torch.float64 if config["experiment"].get("precision") == "float64"
                                else torch.float32)

        train_ds, val_ds, _, _ = prepare_datasets(config)
        print(f"[smoke] datasets: train={len(train_ds)} val={len(val_ds)} samples")

        model = PatchTSTKoopmanModel(config).to(config["experiment"]["device"])
        trainer = EDMDTrainer(model, config)
        trainer.train(train_ds, val_ds)

        A = getattr(model.koopman, "A", None)
        if A is None:
            print("[smoke] model.koopman.A not present")
        else:
            A = A.detach().cpu().numpy()
            rho = float(np.max(np.abs(np.linalg.eigvals(A))))
            print(f"[smoke] Koopman A shape={A.shape} finite={np.isfinite(A).all()} "
                  f"spectral_radius={rho:.6f} (INV1 requires <= 1)")
        print("[smoke] PASS: M1 path completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
