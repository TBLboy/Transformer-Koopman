"""Verify multi-step rollout loss works correctly (1 epoch smoke tests)."""
import copy
import os
import sys

import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
from patchtst_koopman.training.edmd_trainer import EDMDTrainer
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.data_prep import prepare_datasets
from patchtst_koopman.utils.device import resolve_device
from patchtst_koopman.utils.seed import set_seed

CONFIG_PATH = os.path.join(ROOT, "configs", "platform2.yaml")

# ── Test 1: H=5 multi-step rollout ────────────────────────────────────────
print("=" * 60)
print("Test 1: H=5 multi-step rollout loss")
print("=" * 60)

def test_h5():
    cfg1 = load_config(CONFIG_PATH)
    cfg1 = copy.deepcopy(cfg1)
    cfg1["experiment"]["device"] = resolve_device("cpu")
    cfg1["experiment"]["save_dir"] = os.path.join(ROOT, "results", "smoke_rollout")
    cfg1["experiment"]["log_dir"] = os.path.join(ROOT, "results", "logs")
    cfg1["training"]["edmd"]["pretrain"]["num_epochs"] = 1
    cfg1["training"]["edmd"]["pretrain"]["early_stopping"] = False
    cfg1["training"]["edmd"]["pretrain"]["batch_size"] = 128

    if "rollout" not in cfg1["training"]["edmd"]:
        cfg1["training"]["edmd"]["rollout"] = {}
    cfg1["training"]["edmd"]["rollout"]["horizon"] = 5
    cfg1["training"]["edmd"]["rollout"]["gamma"] = 0.95

    set_seed(cfg1["experiment"]["seed"])
    torch.set_default_dtype(torch.float32)

    train_ds, val_ds, _, _ = prepare_datasets(cfg1)
    model1 = PatchTSTKoopmanModel(cfg1).float().to("cpu")
    trainer1 = EDMDTrainer(model1, cfg1)
    trainer1.train(train_ds, val_ds)
    print("Test 1 (H=5): PASSED\n")

# ── Test 2: H=1 (backward compatible) ──────────────────────────────────────
def test_h1():
    print("=" * 60)
    print("Test 2: H=1 single-step (backward compatible)")
    print("=" * 60)

    cfg2 = load_config(CONFIG_PATH)
    cfg2 = copy.deepcopy(cfg2)
    cfg2["experiment"]["device"] = resolve_device("cpu")
    cfg2["experiment"]["save_dir"] = os.path.join(ROOT, "results", "smoke_rollout_h1")
    cfg2["experiment"]["log_dir"] = os.path.join(ROOT, "results", "logs")
    cfg2["training"]["edmd"]["pretrain"]["num_epochs"] = 1
    cfg2["training"]["edmd"]["pretrain"]["early_stopping"] = False
    cfg2["training"]["edmd"]["pretrain"]["batch_size"] = 128

    if "rollout" not in cfg2["training"]["edmd"]:
        cfg2["training"]["edmd"]["rollout"] = {}
    cfg2["training"]["edmd"]["rollout"]["horizon"] = 1

    set_seed(cfg2["experiment"]["seed"])
    torch.set_default_dtype(torch.float32)

    train_ds2, val_ds2, _, _ = prepare_datasets(cfg2)
    model2 = PatchTSTKoopmanModel(cfg2).float().to("cpu")
    trainer2 = EDMDTrainer(model2, cfg2)
    trainer2.train(train_ds2, val_ds2)
    print("Test 2 (H=1): PASSED\n")


if __name__ == "__main__":
    test_h5()
    test_h1()
    print("=" * 60)
    print("ALL SMOKE TESTS PASSED")
    print("=" * 60)
