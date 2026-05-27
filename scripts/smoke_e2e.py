"""Quick end-to-end smoke test using relative paths."""
import copy
import os

import torch

from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
from patchtst_koopman.training.edmd_trainer import EDMDTrainer
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.data_prep import prepare_datasets
from patchtst_koopman.utils.device import resolve_device
from patchtst_koopman.utils.seed import set_seed

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    config = load_config(os.path.join(PROJECT, "configs", "platform2.yaml"))
    config = copy.deepcopy(config)
    config["experiment"]["device"] = resolve_device("cpu")
    config["experiment"]["save_dir"] = os.path.join(PROJECT, "results", "smoke_e2e")
    config["experiment"]["log_dir"] = os.path.join(PROJECT, "results", "logs")
    config["training"]["method"] = "end_to_end"
    config["training"]["end_to_end"]["num_epochs"] = 1
    config["training"]["end_to_end"]["early_stopping"] = False
    config["training"]["end_to_end"]["batch_size"] = 128

    set_seed(config["experiment"]["seed"])
    torch.set_default_dtype(torch.float32)

    # Resolve data path
    config["data"]["data_dir"] = os.path.join(PROJECT, config["data"]["data_dir"])

    train_ds, val_ds, _, _ = prepare_datasets(config)
    model = PatchTSTKoopmanModel(config).float().to("cpu")
    trainer = EDMDTrainer(model, config)
    trainer.train(train_ds, val_ds)
    print("End-to-End 1-epoch smoke test PASSED")


if __name__ == "__main__":
    main()
