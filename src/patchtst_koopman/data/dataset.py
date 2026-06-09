"""PyTorch Dataset that respects trajectory boundaries.

A history window of length ``P`` must lie entirely inside a single trajectory,
otherwise the (one-step) prediction target is meaningless. Indices that span
two trajectories are filtered out at construction time.
"""
import os

import numpy as np
import torch
from torch.utils.data import Dataset


class KoopmanDataset(Dataset):
    """Returns one ``(x_history, u_t, x_next)`` sample per index.

    Args:
        data_dir: Directory containing ``train.npz`` / ``val.npz`` / ``test.npz``.
        config: Project config dict.
        split: ``"train"``, ``"val"``, or ``"test"``.
        norm_stats: Normalisation statistics from the training set (used by
            val/test splits so they do not recompute the mean/std).
    """

    def __init__(self, data_dir, config, split="train", norm_stats=None):
        if split == "train":
            file_path = os.path.join(data_dir, config["data"]["train_file"])
        elif split == "val":
            file_path = os.path.join(data_dir, config["data"]["val_file"])
        else:
            file_path = os.path.join(data_dir, config["data"]["test_file"])

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file does not exist: {file_path}")

        data = np.load(file_path)

        precision = config["experiment"].get("precision", "float32")
        if precision == "float64":
            self.dtype_np = np.float64
            self.dtype_torch = torch.float64
        else:
            self.dtype_np = np.float32
            self.dtype_torch = torch.float32

        self.x = data["x"].astype(self.dtype_np)
        self.u = data["u"].astype(self.dtype_np)
        self.t = data["t"].astype(self.dtype_np)
        self.trajectory_id = data["trajectory_id"].astype(np.int32)

        self.P = config["encoder"]["history_length"]
        self.n = config["data"]["state_dim"]
        self.m = config["data"]["control_dim"]
        self.split = split

        self.N_L = (
            config.get("training", {})
            .get("edmd", {})
            .get("pretrain", {})
            .get("multi_step", {})
            .get("horizon", 0)
        )

        self.valid_indices = self._compute_valid_indices()

        self.x_mean = None
        self.x_std = None
        self.u_mean = None
        self.u_std = None

        if split == "train":
            if config["data"]["normalize_state"]:
                self._normalize_state()
            if config["data"]["normalize_control"]:
                self._normalize_control()
        else:
            if norm_stats is not None:
                if "x_mean" in norm_stats and config["data"]["normalize_state"]:
                    self.x_mean = norm_stats["x_mean"]
                    self.x_std = norm_stats["x_std"]
                    self.x = (self.x - self.x_mean) / self.x_std
                    print("  State normalised (using training-set statistics)")

                if "u_mean" in norm_stats and config["data"]["normalize_control"]:
                    self.u_mean = norm_stats["u_mean"]
                    self.u_std = norm_stats["u_std"]
                    self.u = (self.u - self.u_mean) / self.u_std
                    print("  Control normalised (using training-set statistics)")

        # Convert once up front. Creating tensors inside __getitem__ is a major
        # CPU bottleneck for small batches / short sequences on Windows.
        self.x_tensor = torch.from_numpy(np.ascontiguousarray(self.x)).to(self.dtype_torch)
        self.u_tensor = torch.from_numpy(np.ascontiguousarray(self.u)).to(self.dtype_torch)

        print(f"Dataset [{split}]:")
        print(f"  Total points: {len(self.x)}")
        print(f"  Valid samples: {len(self.valid_indices)}")
        print(f"  Trajectories: {len(np.unique(self.trajectory_id))}")

    def _compute_valid_indices(self):
        """Indices ``i`` where the history window and the prediction target
        both lie inside one trajectory."""
        valid_indices = []
        N = len(self.x)
        required_future = max(1, self.N_L)

        for i in range(self.P - 1, N - required_future):
            window_traj_ids = self.trajectory_id[i - self.P + 1 : i + 1]
            history_valid = np.all(window_traj_ids == window_traj_ids[0])

            future_traj_ids = self.trajectory_id[i : i + required_future + 1]
            target_valid = np.all(future_traj_ids == future_traj_ids[0])

            if history_valid and target_valid:
                valid_indices.append(i)

        return np.array(valid_indices)

    def _normalize_state(self):
        self.x_mean = np.mean(self.x, axis=0)
        self.x_std = np.std(self.x, axis=0) + 1e-8
        self.x = (self.x - self.x_mean) / self.x_std
        print(f"  State normalised: mean={self.x_mean}, std={self.x_std}")

    def _normalize_control(self):
        self.u_mean = np.mean(self.u, axis=0)
        self.u_std = np.std(self.u, axis=0) + 1e-8
        self.u = (self.u - self.u_mean) / self.u_std
        print(f"  Control normalised: mean={self.u_mean}, std={self.u_std}")

    def get_norm_stats(self):
        return {
            "x_mean": self.x_mean,
            "x_std": self.x_std,
            "u_mean": self.u_mean,
            "u_std": self.u_std,
        }

    def __len__(self):
        return len(self.valid_indices)

    def __getitem__(self, idx):
        i = self.valid_indices[idx]
        x_history = self.x_tensor[i - self.P + 1 : i + 1]
        u_t = self.u_tensor[i]
        x_next = self.x_tensor[i + 1]

        result = {
            "x_history": x_history,
            "u_t": u_t,
            "x_next": x_next,
            "_idx": idx,
            "_raw_idx": int(i),
        }

        if self.N_L > 0:
            result["x_future"] = self.x_tensor[i + 1 : i + 1 + self.N_L]
            result["u_future"] = self.u_tensor[i : i + self.N_L]
            windows = []
            for j in range(1, self.N_L + 1):
                win = self.x_tensor[i + j - self.P + 1 : i + j + 1]
                windows.append(win)
            result["x_history_future"] = torch.stack(windows, dim=0)

        return result
