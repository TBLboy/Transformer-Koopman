"""Convert the raw per-platform recordings into the training data contract.

The training code consumes ``train.npz`` / ``val.npz`` / ``test.npz``, each holding
``x`` (states), ``u`` (controls), ``t`` (time) and ``trajectory_id`` (0-based index
of the recording inside that split). The raw recordings in ``数据备份/`` do not use
that layout, so this script performs the conversion.

Split rule (reconstructed, not invented):

* Recordings are ordered by **filename as a string** (so ``data10`` sorts before
  ``data2``). This mirrors the original pipeline, whose ``train.npz`` for the robot
  arm reproduces byte-for-byte from this ordering.
* The ordered list is cut into train / val / test by the counts in ``SPLIT_PLAN``.

Every path is derived from this file's location, so the script carries no
machine-specific absolute path.

Usage (from ``训练代码/``)::

    python scripts/prepare_data.py --platform all
    python scripts/prepare_data.py --platform p1 --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np

PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_DIR.parent
DATA_ROOT = REPO_ROOT / "数据备份"

# Explicit counts rather than ratios: auditable and stable if a recording is added.
SPLIT_PLAN = {
    # 20 robot-arm recordings; reproduces the original experiment_001 split exactly.
    "p1": {"raw": DATA_ROOT / "机械臂数据" / "原始数据",
           "out": DATA_ROOT / "机械臂数据" / "处理后的数据",
           "glob": "*.mat", "train": 15, "val": 4, "test": 1},
    # 100 soft-platform recordings; counts follow the upstream manifest that was
    # shipped alongside the previous processed data (70 / 20 / 10 trajectories).
    "p2": {"raw": DATA_ROOT / "软体平台数据" / "原始数据",
           "out": DATA_ROOT / "软体平台数据" / "处理后的数据",
           "glob": "*.npz", "train": 70, "val": 20, "test": 10},
}


def _string_sorted(paths):
    """Sort by filename as a string, matching the original pipeline's ordering."""
    return sorted(paths, key=lambda p: p.name)


def _natural_mix(paths):
    """Sort by trailing number when present, otherwise by name (for reference)."""
    def key(p):
        m = re.search(r"(\d+)", p.stem)
        return (0, int(m.group(1))) if m else (1, p.name)
    return sorted(paths, key=key)


def load_p1(path):
    """Robot arm: MATLAB struct with ``q`` (states), ``tau`` (controls), ``t``."""
    from scipy.io import loadmat

    struct = loadmat(str(path))[path.stem][0, 0]
    return (np.asarray(struct["q"], dtype=np.float64),
            np.asarray(struct["tau"], dtype=np.float64),
            np.asarray(struct["t"], dtype=np.float64).reshape(-1))


def load_p2(path):
    """Soft platform: npz with ``x`` (states), ``u`` (controls), ``t``."""
    with np.load(str(path), allow_pickle=True) as data:
        return (np.asarray(data["x"], dtype=np.float64),
                np.asarray(data["u"], dtype=np.float64),
                np.asarray(data["t"], dtype=np.float64).reshape(-1))


LOADERS = {"p1": load_p1, "p2": load_p2}


def build_split(plan_key, out_dir, dry_run=False):
    plan = SPLIT_PLAN[plan_key]
    loader = LOADERS[plan_key]

    files = _string_sorted(sorted(plan["raw"].glob(plan["glob"])))
    n_train, n_val, n_test = plan["train"], plan["val"], plan["test"]
    expected = n_train + n_val + n_test
    if len(files) != expected:
        raise SystemExit(
            f"[{plan_key}] expected {expected} recordings "
            f"({n_train}/{n_val}/{n_test}), found {len(files)} in {plan['raw']}"
        )

    groups = {"train": files[:n_train],
              "val": files[n_train:n_train + n_val],
              "test": files[n_train + n_val:]}

    print(f"[{plan_key}] {len(files)} recordings from {plan['raw']}")
    natural = _natural_mix(files)
    if [f.name for f in natural] != [f.name for f in files]:
        print(f"[{plan_key}] note: string order differs from numeric order "
              f"(string: {files[0].name} ... , numeric: {natural[0].name} ...)")

    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for split, group in groups.items():
        xs, us, ts, ids = [], [], [], []
        for local_id, path in enumerate(group):
            x, u, t = loader(path)
            if len(x) != len(u) or len(x) != len(t):
                raise SystemExit(f"[{plan_key}] {path.name}: length mismatch")
            # Rebase time to the start of each recording (per-trajectory elapsed
            # time). This reproduces the original pipeline exactly: with it, every
            # array of the robot-arm output is element-wise identical to the legacy
            # experiment_001 splits. For recordings already starting at t=0 it is a
            # no-op.
            t = t - t[0]
            xs.append(x)
            us.append(u)
            ts.append(t)
            ids.append(np.full(len(x), local_id, dtype=np.int32))
        payload = {"x": np.concatenate(xs, 0),
                   "u": np.concatenate(us, 0),
                   "t": np.concatenate(ts, 0),
                   "trajectory_id": np.concatenate(ids, 0)}
        target = out_dir / f"{split}.npz"
        summary[split] = (payload["x"].shape, len(group), str(target))
        if dry_run:
            print(f"  [dry-run] {split}: x={payload['x'].shape} "
                  f"trajectories={len(group)} -> {target}")
        else:
            np.savez(target, **payload)
            print(f"  {split}: x={payload['x'].shape} trajectories={len(group)} "
                  f"-> {target}")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--platform", choices=["p1", "p2", "all"], default="all")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be written without writing")
    args = ap.parse_args(argv)

    keys = ["p1", "p2"] if args.platform == "all" else [args.platform]
    for key in keys:
        build_split(key, SPLIT_PLAN[key]["out"], dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
