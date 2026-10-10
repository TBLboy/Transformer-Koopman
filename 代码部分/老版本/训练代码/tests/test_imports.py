"""The training code must import cleanly before anything else can be trusted."""
import importlib

import pytest

MODULES = [
    "patchtst_koopman",
    "patchtst_koopman.data.dataset",
    "patchtst_koopman.models.full_model",
    "patchtst_koopman.models.patchtst_encoder",
    "patchtst_koopman.models.koopman_dynamics",
    "patchtst_koopman.models.linear_decoder",
    "patchtst_koopman.lifting.polynomial",
    "patchtst_koopman.lifting.robot_lifting",
    "patchtst_koopman.training.edmd_trainer",
    "patchtst_koopman.utils.config_loader",
    "patchtst_koopman.utils.data_prep",
    "patchtst_koopman.utils.device",
    "patchtst_koopman.utils.evaluation",
    "patchtst_koopman.utils.seed",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module):
    importlib.import_module(module)


def test_model_class_is_constructible():
    from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
    assert PatchTSTKoopmanModel is not None


def test_edmd_trainer_class_exists():
    from patchtst_koopman.training.edmd_trainer import EDMDTrainer
    assert EDMDTrainer is not None
