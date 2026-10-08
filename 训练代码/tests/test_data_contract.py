"""The processed data must satisfy the contract ``KoopmanDataset`` relies on.

Regression guard for the class of defect where a module reads a config key or a
file/array name that no producer actually writes. The contract is fixed by
``src/patchtst_koopman/data/dataset.py``: each split file is an npz holding
``x``, ``u``, ``t`` and ``trajectory_id`` with equal lengths, and ``trajectory_id``
is the 0-based index of the recording inside that split.
"""
import numpy as np
import pytest

from conftest import PLATFORMS

REQUIRED_KEYS = {"x", "u", "t", "trajectory_id"}
SPLITS = ("train", "val", "test")

# Counts fixed by scripts/prepare_data.py SPLIT_PLAN.
EXPECTED_TRAJECTORIES = {
    "p1": {"train": 15, "val": 4, "test": 1},
    "p2": {"train": 70, "val": 20, "test": 10},
}


@pytest.mark.parametrize("platform", sorted(PLATFORMS))
@pytest.mark.parametrize("split", SPLITS)
def test_split_file_exists(platform, split):
    path = PLATFORMS[platform] / f"{split}.npz"
    assert path.is_file(), f"missing processed split: {path}"


@pytest.mark.parametrize("platform", sorted(PLATFORMS))
@pytest.mark.parametrize("split", SPLITS)
def test_split_keys_are_exactly_the_contract(platform, split):
    with np.load(PLATFORMS[platform] / f"{split}.npz") as data:
        assert set(data.files) == REQUIRED_KEYS, (
            f"{platform}/{split} keys={sorted(data.files)}; dataset.py expects "
            f"{sorted(REQUIRED_KEYS)}"
        )


@pytest.mark.parametrize("platform", sorted(PLATFORMS))
@pytest.mark.parametrize("split", SPLITS)
def test_arrays_have_equal_length(platform, split):
    with np.load(PLATFORMS[platform] / f"{split}.npz") as data:
        lengths = {k: len(data[k]) for k in REQUIRED_KEYS}
    assert len(set(lengths.values())) == 1, f"length mismatch: {lengths}"


@pytest.mark.parametrize("platform", sorted(PLATFORMS))
@pytest.mark.parametrize("split", SPLITS)
def test_trajectory_ids_are_contiguous_from_zero(platform, split):
    with np.load(PLATFORMS[platform] / f"{split}.npz") as data:
        ids = np.unique(data["trajectory_id"])
    assert ids[0] == 0, f"trajectory_id must start at 0, got {ids[0]}"
    assert list(ids) == list(range(len(ids))), f"trajectory_id has gaps: {ids}"


@pytest.mark.parametrize("platform", sorted(PLATFORMS))
@pytest.mark.parametrize("split", SPLITS)
def test_trajectory_count_matches_split_plan(platform, split):
    with np.load(PLATFORMS[platform] / f"{split}.npz") as data:
        found = len(np.unique(data["trajectory_id"]))
    assert found == EXPECTED_TRAJECTORIES[platform][split], (
        f"{platform}/{split}: {found} trajectories, "
        f"SPLIT_PLAN expects {EXPECTED_TRAJECTORIES[platform][split]}"
    )


@pytest.mark.parametrize("platform", sorted(PLATFORMS))
@pytest.mark.parametrize("split", SPLITS)
def test_state_and_control_dims_are_consistent(platform, split):
    with np.load(PLATFORMS[platform] / f"{split}.npz") as data:
        x, u = data["x"], data["u"]
    assert x.ndim == 2 and u.ndim == 2
    assert x.shape[1] == (6 if platform == "p1" else 2), f"{platform} state_dim {x.shape[1]}"
    assert u.shape[1] == (3 if platform == "p1" else 2), f"{platform} control_dim {u.shape[1]}"


@pytest.mark.parametrize("platform", sorted(PLATFORMS))
def test_time_is_rebased_per_trajectory(platform):
    """prepare_data.py rebases t to each recording's start (matches legacy data)."""
    with np.load(PLATFORMS[platform] / "train.npz") as data:
        t, ids = data["t"], data["trajectory_id"]
    for tid in np.unique(ids)[:5]:
        seg = t[ids == tid]
        assert seg[0] == pytest.approx(0.0, abs=1e-9), (
            f"{platform} trajectory {tid} starts at t={seg[0]}, expected 0"
        )
