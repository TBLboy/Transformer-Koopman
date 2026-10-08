"""ALN-011 regression guard: constructing a model must not mutate the config.

The legacy code patched ``config["encoder"]["latent_dim"]`` in place so the
baseline models could reuse the shared Koopman dynamics / decoder. That made the
in-memory config diverge from the YAML file, so a run could not be explained by
its config. These tests assert the caller's config survives untouched.
"""
import copy
import json

import pytest
import yaml

from conftest import CONFIG_DIR

CONFIGS = {"p1": "platform1.yaml", "p2": "platform2.yaml"}


def load_yaml(name):
    return yaml.safe_load((CONFIG_DIR / name).read_text(encoding="utf-8"))


def snapshot(config):
    """A stable, comparable representation of the config."""
    return json.dumps(config, sort_keys=True, default=str)


@pytest.mark.parametrize("platform", sorted(CONFIGS))
def test_mlp_model_does_not_mutate_config(platform):
    from patchtst_koopman.models.mlp_koopman_model import MLPKoopmanModel

    config = load_yaml(CONFIGS[platform])
    before = snapshot(config)
    model = MLPKoopmanModel(config)
    assert snapshot(config) == before, (
        f"MLPKoopmanModel mutated the caller's config ({CONFIGS[platform]})"
    )
    # the model itself must still see the baseline latent_dim
    assert model.koopman.d == config["mlp_koopman"]["latent_dim"]


@pytest.mark.parametrize("platform", sorted(CONFIGS))
def test_lstm_model_does_not_mutate_config(platform):
    from patchtst_koopman.models.lstm_koopman_model import LSTMKoopmanModel

    config = load_yaml(CONFIGS[platform])
    before = snapshot(config)
    model = LSTMKoopmanModel(config)
    assert snapshot(config) == before, (
        f"LSTMKoopmanModel mutated the caller's config ({CONFIGS[platform]})"
    )
    assert model.koopman.d == config["lstm_koopman"]["latent_dim"]


@pytest.mark.parametrize("platform", sorted(CONFIGS))
def test_patchtst_model_does_not_mutate_config(platform):
    from patchtst_koopman.models.full_model import PatchTSTKoopmanModel

    config = load_yaml(CONFIGS[platform])
    before = snapshot(config)
    PatchTSTKoopmanModel(config)
    assert snapshot(config) == before, (
        f"PatchTSTKoopmanModel mutated the caller's config ({CONFIGS[platform]})"
    )


@pytest.mark.parametrize("platform", sorted(CONFIGS))
def test_gpu_defaults_do_not_mutate_config(platform):
    from patchtst_koopman.training.performance import apply_gpu_training_defaults

    config = load_yaml(CONFIGS[platform])
    before = snapshot(config)
    result = apply_gpu_training_defaults(config)
    assert snapshot(config) == before, (
        "apply_gpu_training_defaults mutated the caller's config; it must return "
        "a copy (ALN-011)"
    )
    assert result is not config
    # the returned copy carries the defaults
    assert result["training"]["num_workers"] == 4


def test_patched_config_is_a_deep_copy():
    """The patch must not alias nested structures of the input."""
    from patchtst_koopman.models.mlp_koopman_model import MLPKoopmanModel

    config = load_yaml(CONFIGS["p2"])
    patched = MLPKoopmanModel._patched_config(config)
    assert patched is not config
    assert patched["encoder"] is not config["encoder"]
    assert patched["encoder"]["latent_dim"] == config["mlp_koopman"]["latent_dim"]
    assert config["encoder"]["latent_dim"] != config["mlp_koopman"]["latent_dim"], (
        "this test is only meaningful while the two values differ"
    )
