"""数据：读取轨迹、归一化、构造训练窗口与评测分段。

窗口的统一表示（k 为窗口的"当前时刻"）：
    seg_x = x[k-P_h+1 .. k+H]      共 P_h+H 行
    seg_u = u[k-P_h+1 .. k+H-1]    共 P_h-1+H 行
由 split_window 拆成 X_k、v_k、u_{k:k+H-1} 和目标 x_{k+1:k+H}。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

from .config import ROOT

Traj = tuple[np.ndarray, np.ndarray]  # (x [T, n], u [T, m])


def data_dir(cfg: dict) -> Path:
    path = Path(cfg["data"]["dir"])
    return path if path.is_absolute() else ROOT / path


def load_split(directory: Path, split: str) -> list[Traj]:
    """读取一个划分，按 trajectory_id 还原成轨迹列表。"""
    with np.load(Path(directory) / f"{split}.npz") as f:
        x, u, tid = f["x"], f["u"], f["trajectory_id"]
    bounds = [0, *(np.flatnonzero(np.diff(tid)) + 1), len(tid)]
    ids = tid[bounds[:-1]]
    if len(set(ids.tolist())) != len(ids):
        raise ValueError(f"{split}.npz 中同一 trajectory_id 的样本不连续")
    return [(x[a:b].astype(np.float64), u[a:b].astype(np.float64)) for a, b in zip(bounds[:-1], bounds[1:])]


@dataclass
class Normalizer:
    """逐通道标准化。统计量只由训练集计算。"""

    x_mean: np.ndarray
    x_std: np.ndarray
    u_mean: np.ndarray
    u_std: np.ndarray

    @classmethod
    def fit(cls, train: list[Traj]) -> "Normalizer":
        x = np.concatenate([t[0] for t in train])
        u = np.concatenate([t[1] for t in train])
        return cls(x.mean(0), x.std(0), u.mean(0), u.std(0))

    def apply(self, trajs: list[Traj]) -> list[Traj]:
        return [((x - self.x_mean) / self.x_std, (u - self.u_mean) / self.u_std) for x, u in trajs]

    def to_dict(self) -> dict:
        return {k: getattr(self, k).tolist() for k in ("x_mean", "x_std", "u_mean", "u_std")}

    @classmethod
    def from_dict(cls, d: dict) -> "Normalizer":
        return cls(*(np.asarray(d[k], dtype=np.float64) for k in ("x_mean", "x_std", "u_mean", "u_std")))


def train_starts(T: int, P_h: int, H: int) -> list[int]:
    """训练窗口的起点：步长 1 的全部可用时刻。"""
    return list(range(P_h - 1, T - H))


def eval_starts(T: int, P_h: int, H: int) -> list[int]:
    """评测分段的起点：前 P_h 个测量只作预热，其后按 H 不重叠切分，尾部不足 H 步的余段丢弃。"""
    return [P_h - 1 + j * H for j in range((T - P_h) // H)]


def windows(trajs: list[Traj], P_h: int, H: int, starts) -> tuple[torch.Tensor, torch.Tensor]:
    """按 starts(T, P_h, H) 给出的起点切窗口，返回 seg_x [N, P_h+H, n] 和 seg_u [N, P_h-1+H, m]。"""
    view = np.lib.stride_tricks.sliding_window_view
    xs, us = [], []
    for x, u in trajs:
        rows = np.asarray(starts(len(x), P_h, H), dtype=np.int64) - (P_h - 1)
        if len(rows) == 0:
            continue
        xs.append(view(x, P_h + H, axis=0)[rows].transpose(0, 2, 1))
        us.append(view(u, P_h + H - 1, axis=0)[rows].transpose(0, 2, 1))
    if not xs:
        n, m = trajs[0][0].shape[1], trajs[0][1].shape[1]
        return torch.empty(0, P_h + H, n), torch.empty(0, P_h + H - 1, m)
    return torch.from_numpy(np.concatenate(xs)).float(), torch.from_numpy(np.concatenate(us)).float()


def split_window(seg_x: torch.Tensor, seg_u: torch.Tensor, P_h: int):
    """返回 X_k [N, P_h, n]、v_k [N, P_h-1, m]、U [N, H, m]、目标 Y [N, H, n]。"""
    return seg_x[:, :P_h], seg_u[:, : P_h - 1], seg_u[:, P_h - 1 :], seg_x[:, P_h:]


def eval_windows(trajs: list[Traj], P_h: int, horizon) -> list[tuple[int, torch.Tensor, torch.Tensor]]:
    """评测分段。horizon 为 "full" 时每条轨迹一段，覆盖全部 T - P_h 步（按轨迹长度分组）。"""
    if horizon == "full":
        groups: dict[int, list[Traj]] = {}
        for tr in trajs:
            groups.setdefault(len(tr[0]) - P_h, []).append(tr)
        return [(H, *windows(g, P_h, H, eval_starts)) for H, g in sorted(groups.items()) if H >= 1]
    return [(int(horizon), *windows(trajs, P_h, int(horizon), eval_starts))]


@dataclass
class TrainData:
    """训练可见的全部数据：只有训练集和验证集（已归一化）。"""

    train: list[Traj]
    val: list[Traj]
    normalizer: Normalizer
    n: int
    m: int


def load_train_data(cfg: dict) -> TrainData:
    directory = data_dir(cfg)
    train = load_split(directory, "train")
    val = load_split(directory, "val")
    norm = Normalizer.fit(train)
    return TrainData(norm.apply(train), norm.apply(val), norm, train[0][0].shape[1], train[0][1].shape[1])
