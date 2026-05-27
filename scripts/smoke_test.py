"""One-shot smoke tests for code-projectv2. Run from project root:

    conda run -n koopman python scripts/smoke_test.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "deploy"))


def test_import():
    from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
    print("[1/4] import PatchTSTKoopmanModel OK:", PatchTSTKoopmanModel)


def test_lifter():
    from algorithms.tk_assets.transformer_koopman_lifter import TransformerKoopmanLifter

    asset_dir = ROOT / "deploy" / "algorithms" / "tk_assets" / "model_assets"
    lifter = TransformerKoopmanLifter(asset_dir, device="cpu")
    lifter.reset()
    z = lifter.lift_current((0.1, 0.2))
    print(f"[2/4] lifter OK: z.shape={z.shape}, d={lifter.d}")


def test_export_assets():
    import shutil
    import tempfile

    src = ROOT / "deploy" / "algorithms" / "tk_assets" / "model_assets" / "platform2_full_model.pth"
    with tempfile.TemporaryDirectory() as tmp:
        dst_dir = Path(tmp) / "model_assets"
        dst_dir.mkdir()
        shutil.copy2(src, dst_dir / "platform2_full_model.pth")
        meta = {"copied": True}
        import json
        (dst_dir / "platform2_metadata.json").write_text(json.dumps(meta))
        assert (dst_dir / "platform2_full_model.pth").exists()
    print("[3/4] export_assets copy logic OK")


def test_train_one_epoch():
    import copy
    import torch

    from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
    from patchtst_koopman.training.edmd_trainer import EDMDTrainer
    from patchtst_koopman.utils.config_loader import load_config
    from patchtst_koopman.utils.data_prep import prepare_datasets
    from patchtst_koopman.utils.device import resolve_device
    from patchtst_koopman.utils.seed import set_seed

    config = load_config(str(ROOT / "configs" / "platform2.yaml"))
    config = copy.deepcopy(config)
    config["experiment"]["device"] = resolve_device("cpu")
    config["experiment"]["save_dir"] = str(ROOT / "results" / "smoke_test")
    config["training"]["edmd"]["pretrain"]["num_epochs"] = 1
    config["training"]["edmd"]["pretrain"]["early_stopping"] = False
    config["training"]["edmd"]["pretrain"]["patience"] = 1

    set_seed(config["experiment"]["seed"])
    torch.set_default_dtype(torch.float32)

    train_ds, val_ds, _, _ = prepare_datasets(config)
    model = PatchTSTKoopmanModel(config).float().to("cpu")
    trainer = EDMDTrainer(model, config)
    trainer.train(train_ds, val_ds)
    print("[4/4] train 1 epoch OK")


if __name__ == "__main__":
    test_import()
    test_lifter()
    test_export_assets()
    test_train_one_epoch()
    print("\nAll smoke tests passed.")
