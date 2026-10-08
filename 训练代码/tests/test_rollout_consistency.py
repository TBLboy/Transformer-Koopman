"""ALN-010 regression guard: one rollout implementation, shared by every model.

``PatchTSTKoopmanModel``, ``MLPKoopmanModel``, ``LSTMKoopmanModel`` and the
ablation ``AblationModel`` each carried a byte-identical ``predict_multi_step``
and ``get_koopman_matrices`` (and the full model a private ``roll_out_latent``).
They now inherit ``models.rollout.KoopmanRolloutMixin``. These tests pin the
single implementation and its behaviour.
"""
import importlib

import numpy as np
import pytest
import torch
import torch.nn as nn
import yaml

from conftest import CONFIG_DIR

from patchtst_koopman.models.rollout import KoopmanRolloutMixin

MODEL_CLASSES = [
    ("patchtst_koopman.models.full_model", "PatchTSTKoopmanModel"),
    ("patchtst_koopman.models.mlp_koopman_model", "MLPKoopmanModel"),
    ("patchtst_koopman.models.lstm_koopman_model", "LSTMKoopmanModel"),
    ("patchtst_koopman.ablation.models", "AblationModel"),
]

PLATFORMS = ["platform1.yaml", "platform2.yaml"]


def _class(module_name, class_name):
    return getattr(importlib.import_module(module_name), class_name)


def load_yaml(name):
    return yaml.safe_load((CONFIG_DIR / name).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# The four models share one implementation
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("module_name,class_name", MODEL_CLASSES)
def test_rollout_methods_come_from_the_mixin(module_name, class_name):
    cls = _class(module_name, class_name)
    assert cls.predict_multi_step is KoopmanRolloutMixin.predict_multi_step
    assert cls.get_koopman_matrices is KoopmanRolloutMixin.get_koopman_matrices
    assert cls.roll_out_latent is KoopmanRolloutMixin.roll_out_latent


def test_all_models_share_the_same_function_objects():
    for method in ("predict_multi_step", "get_koopman_matrices", "roll_out_latent"):
        funcs = {getattr(_class(m, c), method) for m, c in MODEL_CLASSES}
        assert len(funcs) == 1, f"{method} is not shared across the models"


# --------------------------------------------------------------------------- #
# Behaviour of the shared implementation
# --------------------------------------------------------------------------- #

class _StubKoopman(nn.Module):
    """Identity ``A`` and zero ``B`` so the rollout is analytically known."""

    def __init__(self, d, m):
        super().__init__()
        self.A = nn.Parameter(torch.eye(d))
        self.B = nn.Parameter(torch.zeros(d, m))

    def forward(self, z, u):
        return z @ self.A.T + u @ self.B.T


class _StubModel(KoopmanRolloutMixin, nn.Module):
    """Deterministic model: ``x_next = last state of the window + u``."""

    def __init__(self, n=2, m=1, d=3):
        super().__init__()
        self.koopman = _StubKoopman(d, m)

    def forward(self, x_history, u_t):
        return x_history[:, -1, :] + u_t


def test_predict_multi_step_rolls_the_window():
    model = _StubModel()
    x_history = torch.zeros(1, 3, 2)
    x_history[0, -1] = torch.tensor([1.0, 2.0])
    u = torch.ones(1, 3, 1)  # H=3, m=1

    out = model.predict_multi_step(x_history, u)

    assert out.shape == (1, 3, 2)
    expected = torch.tensor([[[2.0, 3.0], [3.0, 4.0], [4.0, 5.0]]])
    torch.testing.assert_close(out, expected)


def test_roll_out_latent_propagates_through_koopman():
    model = _StubModel(d=2, m=1)
    z0 = torch.tensor([[1.0, 0.0]])
    u = torch.zeros(1, 3, 1)

    out = model.roll_out_latent(z0, u)

    assert out.shape == (1, 3, 2)
    # A = I, B = 0 => the latent state is constant
    torch.testing.assert_close(out, z0.unsqueeze(1).expand(1, 3, 2))


def test_get_koopman_matrices_returns_detached_numpy():
    model = _StubModel(d=3, m=2)
    A, B = model.get_koopman_matrices()
    assert isinstance(A, np.ndarray) and isinstance(B, np.ndarray)
    assert A.shape == (3, 3) and B.shape == (3, 2)
    np.testing.assert_allclose(A, np.eye(3))


# --------------------------------------------------------------------------- #
# The real models still expose the shared API
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("platform", PLATFORMS)
def test_real_model_exposes_koopman_matrices(platform):
    config = load_yaml(platform)
    model = _class(*MODEL_CLASSES[0])(config)
    A, B = model.get_koopman_matrices()
    assert A.shape == (model.koopman.d, model.koopman.d)
    assert B.shape == (model.koopman.d, model.koopman.m)


@pytest.mark.parametrize("platform", PLATFORMS)
def test_real_model_predict_multi_step_shape(platform):
    config = load_yaml(platform)
    model = _class(*MODEL_CLASSES[0])(config)
    model.eval()

    P = config["encoder"]["history_length"]
    n = config["data"]["state_dim"]
    m = config["data"]["control_dim"]
    H = 4
    x_history = torch.randn(2, P, n)
    u = torch.randn(2, H, m)

    with torch.no_grad():
        out = model.predict_multi_step(x_history, u)

    assert out.shape == (2, H, n)


@pytest.mark.parametrize("platform", PLATFORMS)
def test_ablation_model_exposes_rollout(platform):
    """The ablation path (``train_ablation.py``) relies on the same helpers."""
    from patchtst_koopman.ablation.models import create_no_patch

    config = load_yaml(platform)
    model = create_no_patch(config)
    model.eval()

    A, B = model.get_koopman_matrices()
    assert A.shape == (model.koopman.d, model.koopman.d)
    assert B.shape == (model.koopman.d, model.koopman.m)

    P = config["encoder"]["history_length"]
    n = config["data"]["state_dim"]
    m = config["data"]["control_dim"]
    with torch.no_grad():
        out = model.predict_multi_step(torch.randn(2, P, n), torch.randn(2, 3, m))
    assert out.shape == (2, 3, n)


@pytest.mark.parametrize("platform", PLATFORMS)
def test_iterative_prediction_matches_predict_multi_step(platform):
    """The evaluation helper must use the same rollout as the models."""
    from patchtst_koopman.utils.evaluation import iterative_prediction

    config = load_yaml(platform)
    model = _class(*MODEL_CLASSES[0])(config)
    model.eval()

    P = config["encoder"]["history_length"]
    n = config["data"]["state_dim"]
    m = config["data"]["control_dim"]
    H = 5
    x_history = torch.randn(P, n)
    u = torch.randn(H, m)

    with torch.no_grad():
        batched = model.predict_multi_step(x_history.unsqueeze(0), u.unsqueeze(0))
    batched = batched.squeeze(0).numpy()

    single = iterative_prediction(model, x_history, u, "cpu")

    assert single.shape == (H, n)
    np.testing.assert_allclose(single, batched, rtol=1e-5, atol=1e-6)
