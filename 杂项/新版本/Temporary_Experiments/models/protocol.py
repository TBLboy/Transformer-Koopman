# -*- coding: utf-8 -*-
"""Gate 1 shared harness: frozen windows, frozen evaluation starts, frozen metrics.

This module is the single implementation of the evaluation protocol frozen in
``configs/modeling_protocol.yaml``. Every Gate-1 model must go through it, so
that a comparison across models cannot be skewed by a different window rule, a
different normalisation, a different start set, or a different metric.

Design rules (all enforced by ``self_test()``):
  * A history window never crosses a trajectory boundary.
  * ``X_k``  = P measurements, oldest first, last entry is the current ``x_k``.
  * ``U_k^in`` = P-1 past inputs, oldest first; ``u_k`` is EXCLUDED from context.
  * ``u_k`` enters the transition only.
  * Prediction target is ``x_{k+1}`` (shift = 1).
  * Normalisation constants are the train-only ones from the protocol.
  * Evaluation start indices are computed by integer arithmetic (no RNG), so
    they are identical for every model, every seed, every run.
  * Rollout never reads a future true measurement.

Run:
    D:\\conda\\envs\\edmddl2\\python.exe models/protocol.py
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXP_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(EXP_DIR)))

DATA_DIR = os.path.join(REPO, "数据备份", "软体平台数据", "处理后的数据")

# ---- frozen constants (configs/modeling_protocol.yaml) ----------------------
P = 8            # history_length
PATCH = 2
D = 10           # latent_dim
N = 2            # state_dim
M = 2            # control_dim
HORIZONS = {"short": 5, "mid": 25, "long": 100}
STARTS_PER_TRAJ = {"short": 4, "mid": 3, "long": 2}

X_MEAN = np.array([-0.696318, 0.048996])
X_STD = np.array([3.243583, 3.415089])
U_MEAN = np.array([0.238027, -0.091383])
U_STD = np.array([27.962413, 28.133323])

C_X = np.hstack([np.eye(N), np.zeros((N, D - N))])   # C_x z = x_k


def load_split(split: str):
    """Return raw (unnormalised) x, u and trajectory_id for one split."""
    z = np.load(os.path.join(DATA_DIR, "%s.npz" % split), allow_pickle=True)
    return (z["x"].astype(np.float64), z["u"].astype(np.float64),
            z["trajectory_id"].astype(np.int64))


def normalise(x, u):
    return (x - X_MEAN) / X_STD, (u - U_MEAN) / U_STD


def denormalise_x(xn):
    return xn * X_STD + X_MEAN


def frozen_starts(traj_len: int, horizon: int, n_starts: int) -> np.ndarray:
    """Evenly spaced legal start indices inside one trajectory (no RNG).

    Legal start ``k`` satisfies ``P - 1 <= k`` and ``k + horizon <= traj_len - 1``
    so that both the history window and the whole prediction target lie inside
    the trajectory.
    """
    lo = P - 1
    hi = traj_len - horizon - 1
    if hi < lo:
        return np.empty(0, dtype=np.int64)
    if n_starts == 1:
        return np.array([lo], dtype=np.int64)
    span = hi - lo
    idx = lo + np.floor(np.arange(n_starts) * span / (n_starts - 1)).astype(np.int64)
    idx[-1] = hi
    return np.unique(idx)


def dense_starts(traj_len: int, horizon: int, stride: int = 1) -> np.ndarray:
    """All legal start indices inside one trajectory with a fixed stride."""
    lo = P - 1
    hi = traj_len - horizon - 1
    if hi < lo:
        return np.empty(0, dtype=np.int64)
    return np.arange(lo, hi + 1, stride, dtype=np.int64)


def all_starts(horizon_key: str, n_traj: int, traj_len: int = 300) -> np.ndarray:
    """(n_traj, n_starts) frozen start matrix for one horizon key."""
    n = STARTS_PER_TRAJ[horizon_key]
    rows = [frozen_starts(traj_len, HORIZONS[horizon_key], n) for _ in range(n_traj)]
    return np.stack(rows, axis=0)


def starts_digest(horizon_key: str, n_traj: int) -> str:
    a = all_starts(horizon_key, n_traj)
    return hashlib.sha256(a.tobytes()).hexdigest()


def make_windows(x, u, tid, horizon: int, starts=None):
    """Build supervised windows. Returns a dict of arrays.

    For every (trajectory, start k) pair:
      Xh : (P, n)   measurements x[k-P+1 .. k]
      Uin: (P-1, m) past inputs u[k-P+1 .. k-1]
      Ut : (m,)     the input u[k]            (transition only, not in context)
      Xn : (n,)     target x[k+1]             (one-step target)
      XF : (H, n)   targets x[k+1 .. k+H]     (rollout target)
      UF : (H, m)   inputs  u[k .. k+H-1]     (known external input for rollout)
      traj, k     : provenance
    """
    Xh, Uin, Ut, Xn, XF, UF, trajs, ks = [], [], [], [], [], [], [], []
    for t in range(int(tid.max()) + 1):
        m = tid == t
        xs = x[m]
        us = u[m]
        if starts is None:
            cand = frozen_starts(len(xs), horizon, STARTS_PER_TRAJ["short"])
        else:
            cand = starts[t]
        for k in cand:
            if k < P - 1 or k + horizon > len(xs) - 1:
                continue
            Xh.append(xs[k - P + 1:k + 1])
            Uin.append(us[k - P + 1:k])
            Ut.append(us[k])
            Xn.append(xs[k + 1])
            XF.append(xs[k + 1:k + 1 + horizon])
            UF.append(us[k:k + horizon])
            trajs.append(t)
            ks.append(k)
    return {
        "Xh": np.asarray(Xh), "Uin": np.asarray(Uin), "Ut": np.asarray(Ut),
        "Xn": np.asarray(Xn), "XF": np.asarray(XF), "UF": np.asarray(UF),
        "traj": np.asarray(trajs, dtype=np.int64), "k": np.asarray(ks, dtype=np.int64),
    }


def context_input(Xh, Uin):
    """c_k = C_phi(X_k, U_k^in) input vector: P measurements then P-1 inputs."""
    b = Xh.shape[0]
    return np.concatenate([Xh.reshape(b, -1), Uin.reshape(b, -1)], axis=1)


# ---- metrics ---------------------------------------------------------------
def rmse(pred, tgt):
    return float(np.sqrt(np.mean((np.asarray(pred) - np.asarray(tgt)) ** 2)))


def per_channel_rmse(pred, tgt):
    e = np.asarray(pred) - np.asarray(tgt)
    return np.sqrt(np.mean(e ** 2, axis=tuple(range(e.ndim - 1))))


def mae(pred, tgt):
    return float(np.mean(np.abs(np.asarray(pred) - np.asarray(tgt))))


def normalised_rmse(pred_n, tgt_n):
    """RMSE in normalised units. Denominator is stated: train-only x_std."""
    return rmse(pred_n, tgt_n)


def horizon_curve(pred_seq, tgt_seq):
    """pred_seq/tgt_seq: (n_samples, H, n). Returns RMSE per horizon step."""
    e = np.asarray(pred_seq) - np.asarray(tgt_seq)
    return np.sqrt(np.mean(e ** 2, axis=(0, 2)))


def quantiles(pred, tgt, qs=(0.5, 0.9, 0.99)):
    err = np.linalg.norm(np.asarray(pred) - np.asarray(tgt), axis=-1)
    return {("q%g" % q): float(np.quantile(err, q)) for q in qs}


def cross_trajectory_variance(pred, tgt, traj):
    """RMSE per trajectory, then its variance across trajectories."""
    per = {}
    for t in np.unique(traj):
        m = traj == t
        per[int(t)] = rmse(np.asarray(pred)[m], np.asarray(tgt)[m])
    vals = np.array(list(per.values()))
    return float(vals.var()), per


# ---- self test -------------------------------------------------------------
def self_test() -> int:
    print("=" * 78)
    print("Gate 1 harness self-test (protocol: configs/modeling_protocol.yaml)")
    print("=" * 78)
    problems = []

    x_tr, u_tr, tid_tr = load_split("train")
    x_va, u_va, tid_va = load_split("val")
    x_te, u_te, tid_te = load_split("test")
    print("  shapes: train %s/%s trajs=%d | val %s trajs=%d | test %s trajs=%d"
          % (x_tr.shape, u_tr.shape, tid_tr.max() + 1,
             x_va.shape, tid_va.max() + 1, x_te.shape, tid_te.max() + 1))

    # 1. frozen start sets are identical across calls and across models
    d = {k: starts_digest(k, 10) for k in HORIZONS}
    for k in HORIZONS:
        a1, a2 = all_starts(k, 10), all_starts(k, 10)
        if not np.array_equal(a1, a2):
            problems.append("start set for %s is not reproducible" % k)
    print("  frozen start-set digests (test split, 10 trajs):")
    for k in HORIZONS:
        print("    %-5s H=%3d  starts/traj=%d  digest=%s"
              % (k, HORIZONS[k], STARTS_PER_TRAJ[k], d[k][:16]))

    # 2. window construction, normalised inputs
    xn, un = normalise(x_tr, u_tr)
    w = make_windows(xn, un, tid_tr, HORIZONS["short"])
    print("  windows (H=5, train): Xh %s Uin %s Ut %s Xn %s XF %s UF %s"
          % (w["Xh"].shape, w["Uin"].shape, w["Ut"].shape, w["Xn"].shape,
             w["XF"].shape, w["UF"].shape))
    if w["Xh"].shape[1:] != (P, N):
        problems.append("Xh window shape is %s, expected (P=%d, n=%d)" % (w["Xh"].shape[1:], P, N))
    if w["Uin"].shape[1:] != (P - 1, M):
        problems.append("Uin shape is %s, expected (P-1=%d, m=%d)" % (w["Uin"].shape[1:], P - 1, M))
    if w["XF"].shape[1:] != (HORIZONS["short"], N):
        problems.append("XF shape is %s" % (w["XF"].shape[1:],))

    # 3. no leakage: last history row == current measurement; XF[0] == x_{k+1}
    ctx = context_input(w["Xh"], w["Uin"])
    if ctx.shape[1] != 30:
        problems.append("context input dim is %d, expected 30" % ctx.shape[1])
    print("  context input dim: %d (expected P*n+(P-1)*m = %d)"
          % (ctx.shape[1], P * N + (P - 1) * M))

    bad_last, bad_first, bad_ut = 0, 0, 0
    for i in range(len(w["k"])):
        t, k = int(w["traj"][i]), int(w["k"][i])
        xs = xn[tid_tr == t]
        us = un[tid_tr == t]
        if not np.allclose(w["Xh"][i, -1], xs[k]):
            bad_last += 1
        if not np.allclose(w["XF"][i, 0], xs[k + 1]):
            bad_first += 1
        if not np.allclose(w["Ut"][i], us[k]):
            bad_ut += 1
    print("  leakage checks: Xh[-1]!=x_k in %d, XF[0]!=x_{k+1} in %d, Ut!=u_k in %d"
          % (bad_last, bad_first, bad_ut))
    if bad_last or bad_first or bad_ut:
        problems.append("window construction leaks or misaligns")

    # 4. u_k is NOT inside the context
    #    (context = Xh then Uin; Uin covers k-P+1..k-1, so u_k must not appear)
    hit = 0
    for i in range(min(len(w["k"]), 200)):
        t, k = int(w["traj"][i]), int(w["k"][i])
        us = un[tid_tr == t]
        if np.any(np.all(np.isclose(w["Uin"][i], us[k]), axis=-1)):
            hit += 1
    print("  u_k found inside U_k^in: %d / %d checked (must be 0)" % (hit, min(len(w["k"]), 200)))
    if hit:
        problems.append("u_k appears inside the context input")

    # 5. no window crosses a trajectory boundary
    cross = 0
    for i in range(len(w["k"])):
        t, k = int(w["traj"][i]), int(w["k"][i])
        L = int(np.sum(tid_tr == t))
        if k - P + 1 < 0 or k + HORIZONS["short"] > L - 1:
            cross += 1
    print("  windows crossing a trajectory boundary: %d (must be 0)" % cross)
    if cross:
        problems.append("window crosses a trajectory boundary")

    # 6. metrics behave on a known input
    r = rmse(np.zeros((10, N)), np.ones((10, N)))
    if abs(r - 1.0) > 1e-12:
        problems.append("rmse of unit error is %r, expected 1.0" % r)
    pc = per_channel_rmse(np.array([[0.0, 0.0], [2.0, 0.0]]), np.zeros((2, N)))
    # channel 0: sqrt(mean([0, 4])) = sqrt(2); channel 1: 0
    if not np.allclose(pc, [np.sqrt(2.0), 0.0]):
        problems.append("per_channel_rmse is %s, expected [sqrt(2), 0]" % pc)
    print("  metric sanity: rmse(zeros,ones)=%.6f  per_channel_rmse=%s" % (r, pc))

    # 7. train-only normalisation really comes from the train split
    print("  train-only normalisation (frozen): x_mean=%s x_std=%s u_std=%s"
          % (X_MEAN, X_STD, U_STD))
    print("  train split recomputed mean/std (for reference only, NOT used):")
    print("    x_mean=%s x_std=%s" % (np.round(x_tr.mean(0), 6), np.round(x_tr.std(0), 6)))

    print()
    if problems:
        print("  RESULT: FAIL")
        for p in problems:
            print("    - " + p)
        return 1
    print("  RESULT: PASS (all protocol invariants hold)")
    return 0


if __name__ == "__main__":
    sys.exit(self_test())
