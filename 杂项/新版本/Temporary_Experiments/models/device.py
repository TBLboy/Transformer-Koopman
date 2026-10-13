# -*- coding: utf-8 -*-
"""Device specifications for the temporary modelling / control experiment.

The Gate 1-5 harness was written for Platform 2 (soft platform: 2-D state, 2-D
control, dt = 0.2 s).  Re-running the SAME methods on the 3-joint robotic arm
(6-D state, 3-D control, dt = 0.004 s) requires the protocol, the model library
and the controller to be parameterised by the device -- otherwise the
cross-device comparison would silently mix in implementation differences.

Selection order (highest priority first):
  1. ``device.bootstrap_from_argv()`` / ``device.set_device(name)`` called BEFORE
     ``protocol`` / ``library`` are imported (they freeze the constants at import);
  2. the environment variable ``TK_DEVICE``;
  3. ``soft_platform`` -- the default, which keeps the original behaviour intact.

Frozen facts per device (see reports/data_audit.md and reports/data_audit_arm.md):
  * ``x_mean/x_std/u_mean/u_std`` are train-only, computed once and frozen here so
    every run uses identical normalisation constants.
  * ``u_limit_phys`` is the control box constraint.  For the soft platform it is
    the legacy deployment value 100 (Q3, pending user confirmation).  For the arm
    it is the train empirical range times 1.05 (DEC-086, user-confirmed
    2026-10-11) and is an ASSUMPTION, not an actuator rating.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(EXP_DIR)))

DEFAULT_DEVICE = "soft_platform"


# ============================================================ soft platform
SOFT_PLATFORM = {
    "name": "soft_platform",
    "label": "Platform 2 (soft platform)",
    "state_names": ["x1", "x2"],
    "control_names": ["u1", "u2"],
    # architecture (configs/modeling_protocol.yaml, frozen by TASK-045)
    "n_state": 2,
    "n_ctrl": 2,
    "history_P": 8,
    "patch": 2,
    "latent_dim": 10,            # n + n_psi, n_psi = 8
    "ctx_dim": 16,
    "ctx_hidden": 64,
    # prediction task
    "horizons": {"short": 5, "mid": 25, "long": 100},
    "starts_per_traj": {"short": 4, "mid": 3, "long": 2},
    "selection_horizon": 25,
    # data
    "dt": 0.2,
    "trajectory_length": 300,
    "n_traj": {"train": 70, "val": 20, "test": 10},
    "data_dir": os.path.join(REPO, "数据备份", "软体平台数据", "处理后的数据"),
    "x_mean": [-0.696318, 0.048996],
    "x_std": [3.243583, 3.415089],
    "u_mean": [0.238027, -0.091383],
    "u_std": [27.962413, 28.133323],
    # control
    "u_limit_phys": {"lower": [-100.0, -100.0], "upper": [100.0, 100.0]},
    "u_limit_source": "legacy deployment config u_limit = 100 (Q3, NOT user-confirmed)",
    "u_limit_is_assumption": True,
    "mpc_N": 10,
    "mpc_N_sensitivity": [5, 20],
    "gate5_u_bound": 3.5,        # symmetric Gate-5 comparison box (inside the frozen box)
    # control scenarios: all channels are positions (the state IS a screen position)
    "pos_channels": [0, 1],
    "pos_to_vel": {0: None, 1: None},
    "scenario_setpoint_steps": 100,
    "scenario_tracking_steps": 200,
    # output layout (unchanged for the soft platform: evidence continuity)
    "results_root": "results",
    "checkpoints": "checkpoints",
    "report_prefix": "",
}

# ============================================================ 3-joint arm
ARM_3LINK = {
    "name": "arm_3link",
    "label": "3-joint robotic arm",
    "state_names": ["q1", "dq1", "q2", "dq2", "q3", "dq3"],
    "control_names": ["tau1", "tau2", "tau3"],
    # architecture: protocol rule preserved -> n_psi = 8, d = n + 8
    "n_state": 6,
    "n_ctrl": 3,
    "history_P": 8,              # matches legacy configs/platform1.yaml history_length: 8
    "patch": 2,
    "latent_dim": 14,            # n + n_psi with n_psi = 8 (same rule as the soft platform)
    "ctx_dim": 16,
    "ctx_hidden": 64,
    # prediction task: protocol step horizons kept, physical-time horizons added
    # (at 250 Hz, H=25 is only 0.1 s; H=500/1000 are 2 s / 4 s)
    "horizons": {"short": 5, "mid": 25, "long": 100, "long2": 500, "long3": 1000},
    "starts_per_traj": {"short": 4, "mid": 3, "long": 2, "long2": 2, "long3": 1},
    "selection_horizon": 25,
    # data
    "dt": 0.004,
    "trajectory_length": 4976,
    "n_traj": {"train": 15, "val": 4, "test": 1},
    "data_dir": os.path.join(REPO, "数据备份", "机械臂数据", "处理后的数据"),
    "x_mean": [0.097531, -0.015824, 0.673393, 0.001894, 0.224119, -0.001332],
    "x_std": [0.428247, 2.980478, 0.216930, 1.934337, 0.119379, 1.570696],
    "u_mean": [0.034564, 3.111360, 1.380698],
    "u_std": [0.918609, 0.918556, 0.546100],
    # control: train empirical range x 1.05 (DEC-086)
    "u_limit_phys": {"lower": [-2.770553, -0.217663, -1.237823],
                     "upper": [3.678861, 5.994418, 3.113232]},
    "u_limit_source": "train empirical range x 1.05 (DEC-086, user-confirmed); ASSUMPTION, not an actuator rating",
    "u_limit_is_assumption": True,
    "mpc_N": 50,                 # 0.2 s; N=10 would be only 40 ms at 250 Hz
    "mpc_N_sensitivity": [25, 100],
    "gate5_u_bound": 3.0,        # symmetric Gate-5 comparison box (the arm's box is asymmetric)
    # control scenarios: q1/q2/q3 are the position channels; velocities tracked to 0
    "pos_channels": [0, 2, 4],
    "pos_to_vel": {0: 1, 2: 3, 4: 5},
    "scenario_setpoint_steps": 400,     # 1.6 s
    "scenario_tracking_steps": 800,     # 3.2 s (slow period 400 steps = 1.6 s)
    # output layout: device-scoped so the soft-platform artefacts are untouched
    "results_root": os.path.join("results", "arm"),
    "checkpoints": os.path.join("checkpoints", "arm"),
    "report_prefix": "arm_",
}

DEVICES = {d["name"]: d for d in (SOFT_PLATFORM, ARM_3LINK)}

_CURRENT = None


def available():
    return sorted(DEVICES)


def _lookup(name):
    if name not in DEVICES:
        raise KeyError("unknown device %r (available: %s)" % (name, ", ".join(available())))
    return DEVICES[name]


def set_device(name):
    """Select the device.  Must be called before ``protocol``/``library`` import."""
    global _CURRENT
    _CURRENT = _lookup(name)
    os.environ["TK_DEVICE"] = _CURRENT["name"]
    return _CURRENT


def current():
    """The active device spec (resolved lazily from ``TK_DEVICE``)."""
    global _CURRENT
    if _CURRENT is None:
        _CURRENT = _lookup(os.environ.get("TK_DEVICE", DEFAULT_DEVICE))
    return _CURRENT


def bootstrap_from_argv(argv=None):
    """Honour ``--device NAME`` / ``-d NAME`` in ``sys.argv`` before other imports.

    Scripts call this at the very top so that ``protocol`` and ``library`` freeze
    the right constants at import time.
    """
    if argv is None:
        argv = sys.argv[1:]
    name = None
    for i, a in enumerate(argv):
        if a in ("--device", "-d") and i + 1 < len(argv):
            name = argv[i + 1]
        elif a.startswith("--device="):
            name = a.split("=", 1)[1]
    if name:
        return set_device(name)
    return current()


# ---- derived helpers -------------------------------------------------------
def n_state():
    return int(current()["n_state"])


def n_ctrl():
    return int(current()["n_ctrl"])


def horizons():
    return dict(current()["horizons"])


def horizon_key(horizon):
    """Inverse map: horizon value -> protocol key."""
    for k, v in current()["horizons"].items():
        if int(v) == int(horizon):
            return k
    raise KeyError("horizon %r is not a frozen horizon of device %r" % (horizon, current()["name"]))


def u_limits_normalised():
    """The frozen control box in normalised units."""
    import numpy as np
    d = current()
    lo = (np.asarray(d["u_limit_phys"]["lower"], dtype=float) - np.asarray(d["u_mean"])) / np.asarray(d["u_std"])
    hi = (np.asarray(d["u_limit_phys"]["upper"], dtype=float) - np.asarray(d["u_mean"])) / np.asarray(d["u_std"])
    return lo, hi


def results_dir(*parts):
    return os.path.join(EXP_DIR, current()["results_root"], *parts)


def checkpoints_dir():
    return os.path.join(EXP_DIR, current()["checkpoints"])


def report_path(name):
    """Device-scoped report path (the soft platform keeps its original names)."""
    return os.path.join(EXP_DIR, "reports", current()["report_prefix"] + name)


def figure_path(name):
    return os.path.join(EXP_DIR, "figures", current()["report_prefix"] + name)


if __name__ == "__main__":
    d = current()
    print("device = %s  (%s)" % (d["name"], d["label"]))
    print("  n_state=%d n_ctrl=%d P=%d d=%d patch=%d ctx_dim=%d"
          % (d["n_state"], d["n_ctrl"], d["history_P"], d["latent_dim"], d["patch"], d["ctx_dim"]))
    print("  horizons=%s" % d["horizons"])
    print("  dt=%s s  traj_len=%s  n_traj=%s" % (d["dt"], d["trajectory_length"], d["n_traj"]))
    print("  data_dir=%s" % d["data_dir"])
    print("  exists=%s" % os.path.isdir(d["data_dir"]))
    print("  u_limit_phys=%s" % d["u_limit_phys"])
    print("  u_limit_source=%s" % d["u_limit_source"])
    print("  pos_channels=%s" % d["pos_channels"])
    print("  results_root=%s" % d["results_root"])
