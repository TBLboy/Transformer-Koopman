"""Config <-> code contract.

Two failure modes are guarded:

* ``test_required_paths_present``: a key the code reads but no config declares
  (the code would raise ``KeyError`` at some point mid-pipeline).
* ``test_no_new_unread_keys``: a key a config declares but no code ever reads
  (silently dead configuration, which is how the platforms drifted apart).

The second test pins the *known* unread set, so adding new dead config fails the
suite instead of accumulating silently.
"""
import re
from pathlib import Path

import pytest
import yaml

from conftest import CONFIG_DIR, PROJECT_DIR, SRC_DIR

CONFIGS = {"p1": "platform1.yaml", "p2": "platform2.yaml"}

# A config key counts as "read" when its name appears quoted in any of these
# trees. scripts/ and deploy/ are included because several keys (e.g.
# experiment.log_dir) are consumed by entry-point scripts rather than the package.
SOURCE_DIRS = [SRC_DIR, PROJECT_DIR / "scripts", PROJECT_DIR / "deploy"]

# Key paths the M1 (EDMD) training path reads. Each must exist and be non-None.
REQUIRED_PATHS = [
    "experiment.seed",
    "experiment.device",
    "experiment.precision",
    "data.data_dir",
    "data.train_file",
    "data.val_file",
    "data.test_file",
    "data.state_dim",
    "data.control_dim",
    "data.normalize_state",
    "data.normalize_control",
    "encoder.history_length",
    "encoder.patch_length",
    "encoder.latent_dim",
    "encoder.d_model",
    "encoder.n_layers",
    "encoder.n_heads",
    "encoder.d_ff",
    "encoder.dropout",
    "training.method",
    "training.edmd.pretrain.num_epochs",
    "training.edmd.pretrain.batch_size",
    "training.edmd.pretrain.learning_rate",
    "training.edmd.compute.regularization",
    "training.traditional_edmd.lifting_function.type",
]

# Leaf keys that the configs declare but no source file references. Pinned so a
# *new* dead key fails the suite. This is the live evidence for clarification
# ALN-005; note the detector is a heuristic (a key counts as read when its name
# appears quoted in src/, scripts/ or deploy/), so treat additions as
# "needs review", not as proof.
#
# ALN-005 (resolved): every previously-pinned dead key was deleted from both
# configs, so the pinned set is now empty. Any key that reappears here means a
# new dead config was introduced.
KNOWN_UNREAD = {
    "p1": set(),
    "p2": set(),
}


def load_yaml(name):
    return yaml.safe_load((CONFIG_DIR / name).read_text(encoding="utf-8"))


def leaf_paths(node, prefix=""):
    out = {}
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict) and value:
                out.update(leaf_paths(value, path))
            else:
                out[path] = key
    return out


def source_text():
    parts = []
    for directory in SOURCE_DIRS:
        if directory.is_dir():
            parts.extend(
                p.read_text(encoding="utf-8") for p in sorted(directory.rglob("*.py"))
            )
    return "\n".join(parts)


@pytest.mark.parametrize("platform", sorted(CONFIGS))
def test_config_parses(platform):
    data = load_yaml(CONFIGS[platform])
    assert isinstance(data, dict) and data, f"{CONFIGS[platform]} is not a mapping"


@pytest.mark.parametrize("platform", sorted(CONFIGS))
@pytest.mark.parametrize("path", REQUIRED_PATHS)
def test_required_paths_present(platform, path):
    node = load_yaml(CONFIGS[platform])
    cursor = node
    for part in path.split("."):
        assert isinstance(cursor, dict) and part in cursor, (
            f"{CONFIGS[platform]} is missing '{path}'; the M1 training path reads it"
        )
        cursor = cursor[part]
    assert cursor is not None, f"{CONFIGS[platform]}.{path} is declared but null"


@pytest.mark.parametrize("platform", sorted(CONFIGS))
def test_no_new_unread_keys(platform):
    text = source_text()
    leaves = leaf_paths(load_yaml(CONFIGS[platform]))
    unread = set()
    for path, token in leaves.items():
        if not re.search(rf"""["']{re.escape(str(token))}["']""", text):
            unread.add(path)
    known = KNOWN_UNREAD[platform]
    new = sorted(unread - known)
    stale = sorted(known - unread)
    assert not new, (
        f"{CONFIGS[platform]} declares {len(new)} key(s) that no source file reads: "
        f"{new}\nEither wire them up or add them to KNOWN_UNREAD with a reason."
    )
    assert not stale, (
        f"KNOWN_UNREAD lists {len(stale)} key(s) that are now read: {stale}\n"
        "Remove them from the pinned set so the guard stays honest."
    )


@pytest.mark.parametrize("platform", sorted(CONFIGS))
def test_stage1_loss_declares_five_terms(platform):
    """Paper eq:pretraining_loss defines five terms; see clarification ALN-001/002."""
    node = load_yaml(CONFIGS[platform])
    if platform == "p2":
        pytest.xfail(
            "known defect ALN-001/002: platform2.yaml has no multi_step key and only "
            "three loss weights; FIX-02 wires the five-term contract for p2"
        )
    weights = node["training"]["edmd"]["pretrain"]["loss_weights"]
    assert set(weights) == {
        "prediction", "latent", "consistency", "multi_step_physical", "multi_step_latent",
    }, f"unexpected loss weights: {sorted(weights)}"
    assert node["training"]["edmd"]["pretrain"]["multi_step"]["horizon"] > 0


# Keys that utils/seed.py reads via ``exp.get(name, default)``. Declaring them
# explicitly keeps platform behaviour visible instead of relying on a silent
# default (clarification ALN-004).
CUDA_PERFORMANCE_KEYS = [
    "experiment.deterministic",
    "experiment.cudnn_benchmark",
    "experiment.amp",
    "experiment.allow_tf32",
    "experiment.float32_matmul_precision",
]


@pytest.mark.parametrize("platform", sorted(CONFIGS))
@pytest.mark.parametrize("path", CUDA_PERFORMANCE_KEYS)
def test_cuda_performance_keys_are_explicit(platform, path):
    node = load_yaml(CONFIGS[platform])
    cursor = node
    for part in path.split("."):
        assert isinstance(cursor, dict) and part in cursor, (
            f"{CONFIGS[platform]} does not declare '{path}'; utils/seed.py would "
            "silently fall back to its default (ALN-004)"
        )
        cursor = cursor[part]
    assert cursor is not None, f"{CONFIGS[platform]}.{path} is declared but null"


@pytest.mark.parametrize("platform", sorted(CONFIGS))
def test_data_dir_points_at_generated_splits(platform):
    """data_dir must resolve to the directory prepare_data.py writes."""
    node = load_yaml(CONFIGS[platform])
    resolved = (CONFIG_DIR.parent / node["data"]["data_dir"]).resolve()
    for split in ("train", "val", "test"):
        assert (resolved / f"{split}.npz").is_file(), (
            f"{CONFIGS[platform]}.data.data_dir resolves to {resolved}, which lacks "
            f"{split}.npz; run scripts/prepare_data.py"
        )
