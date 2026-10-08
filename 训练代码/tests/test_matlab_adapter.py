"""MATLAB / Simulink encoder adapter must consume the real checkpoint format.

Regression guard for clarification ALN-007: ``scripts/encoder_inference_matlab.py``
expected a standalone encoder checkpoint (``encoder_state_dict`` /
``history_length`` / ``input_dim`` / ``output_dim`` / ``norm_stats``) that no
writer ever produced. ``utils/checkpoint.py:save_model`` writes a full-model
checkpoint (``model_state_dict`` / ``config`` / ``model_info`` /
``normalization``), so the adapter could never load a trained model.

The tests below round-trip a checkpoint through the *real* ``save_model`` and
assert the adapter lifts identically to the encoder it wraps.
"""
import copy
import importlib.util

import numpy as np
import pytest
import torch
import yaml

from conftest import CONFIG_DIR, PROJECT_DIR
from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
from patchtst_koopman.models.patchtst_encoder import PatchTSTEncoder
from patchtst_koopman.utils.checkpoint import save_model


def load_adapter():
    spec = importlib.util.spec_from_file_location(
        "encoder_inference_matlab_under_test",
        PROJECT_DIR / "scripts" / "encoder_inference_matlab.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTER = load_adapter()
CONFIG_PATH = CONFIG_DIR / "platform1.yaml"


def _config():
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _norm_stats(config):
    n = config["data"]["state_dim"]
    m = config["data"]["control_dim"]
    return {
        "x_mean": np.zeros(n), "x_std": np.ones(n),
        "u_mean": np.zeros(m), "u_std": np.ones(m),
    }


def _lift_reference(encoder, x):
    with torch.no_grad():
        return encoder(torch.tensor(x, dtype=torch.float32).unsqueeze(0)).squeeze(0).numpy()


def test_adapter_loads_real_save_model_output(tmp_path):
    """The adapter must read what ``save_model`` actually writes (ALN-007)."""
    config = copy.deepcopy(_config())
    config["experiment"]["save_dir"] = str(tmp_path)

    torch.manual_seed(0)
    model = PatchTSTKoopmanModel(config).eval()
    path = save_model(model, config, norm_stats=_norm_stats(config), filename="model.pth")

    adapter = ADAPTER.EncoderInference(path, str(CONFIG_PATH))
    assert adapter.history_length == config["encoder"]["history_length"]
    assert adapter.input_dim == config["data"]["state_dim"]
    assert adapter.output_dim == config["encoder"]["latent_dim"]
    assert adapter.norm_stats is not None

    rng = np.random.RandomState(0)
    x = rng.randn(adapter.history_length, adapter.input_dim)
    np.testing.assert_allclose(
        adapter.lift(x), _lift_reference(model.encoder, x), rtol=1e-5, atol=1e-6
    )


def test_adapter_still_accepts_legacy_encoder_checkpoint(tmp_path):
    """A hand-made encoder-only checkpoint keeps working."""
    config = _config()
    torch.manual_seed(0)
    encoder = PatchTSTEncoder(config).eval()
    path = tmp_path / "encoder_only.pth"
    torch.save(
        {
            "encoder_state_dict": encoder.state_dict(),
            "history_length": config["encoder"]["history_length"],
            "input_dim": config["data"]["state_dim"],
            "output_dim": config["encoder"]["latent_dim"],
            "norm_stats": None,
        },
        path,
    )

    adapter = ADAPTER.EncoderInference(str(path), str(CONFIG_PATH))
    assert adapter.history_length == config["encoder"]["history_length"]
    assert adapter.input_dim == config["data"]["state_dim"]
    assert adapter.output_dim == config["encoder"]["latent_dim"]

    rng = np.random.RandomState(1)
    x = rng.randn(adapter.history_length, adapter.input_dim)
    np.testing.assert_allclose(
        adapter.lift(x), _lift_reference(encoder, x), rtol=1e-5, atol=1e-6
    )


def test_adapter_rejects_checkpoint_without_encoder_weights(tmp_path):
    path = tmp_path / "bad.pth"
    torch.save({"model_state_dict": {"koopman.A": torch.zeros(1)}}, path)
    with pytest.raises(KeyError):
        ADAPTER.EncoderInference(str(path), str(CONFIG_PATH))


def test_adapter_guards_the_legacy_key_read():
    """The never-written keys may only be read behind an explicit guard."""
    source = (PROJECT_DIR / "scripts" / "encoder_inference_matlab.py").read_text(
        encoding="utf-8"
    )
    assert 'if "encoder_state_dict" in checkpoint:' in source
    assert 'checkpoint["model_state_dict"]' in source
