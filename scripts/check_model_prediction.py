"""Quick model sanity check: open-loop 10-step rollout on test data."""
import os
from pathlib import Path

import numpy as np
import torch

from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
from patchtst_koopman.utils.checkpoint import load_model
from patchtst_koopman.utils.config_loader import load_config

MODEL_PATH = r"C:\Users\Windows\Desktop\论文4\code-projectv2\results\models\model_20260527_154535.pth"
CONFIG_PATH = r"C:\Users\Windows\Desktop\论文4\code-projectv2\configs\platform2.yaml"
DATA_DIR = r"C:\Users\Windows\Desktop\论文4\code-projectv2\data\experiment_006"

# ── Load model ───────────────────────────────────────────────────────────
print("=" * 60)
print("Loading model...")
print(f"  Checkpoint: {MODEL_PATH}")
model, config, ckpt = load_model(MODEL_PATH, device="cpu")
device = "cpu"
n = config["data"]["state_dim"]
m = config["data"]["control_dim"]
P = config["encoder"]["history_length"]
print(f"  State dim: {n}, Control dim: {m}, History length: {P}")

# ── Load test data ────────────────────────────────────────────────────────
data = np.load(os.path.join(DATA_DIR, "test.npz"))
x_raw = data["x"].astype(np.float64)
u_raw = data["u"].astype(np.float64)
traj_id = data["trajectory_id"]

# ── Load normalization (from checkpoint) ──────────────────────────────────
norm = ckpt["normalization"]
x_mean = np.asarray(norm["x_mean"], dtype=np.float64).reshape(1, n)
x_std = np.asarray(norm["x_std"], dtype=np.float64).reshape(1, n)
u_mean = np.asarray(norm["u_mean"], dtype=np.float64).reshape(1, m)
u_std = np.asarray(norm["u_std"], dtype=np.float64).reshape(1, m)

x_norm = (x_raw - x_mean) / x_std
u_norm = (u_raw - u_mean) / u_std

# ── Pick trajectory 0 ─────────────────────────────────────────────────────
mask = traj_id == 0
if mask.sum() < P + 10:
    # try longer trajectory
    unique_ids, counts = np.unique(traj_id, return_counts=True)
    best_idx = unique_ids[np.argmax(counts)]
    mask = traj_id == best_idx
    print(f"  Using trajectory {best_idx} ({mask.sum()} points)")

x_traj = x_norm[mask]
u_traj = u_norm[mask]
print(f"  Trajectory length: {len(x_traj)} points")

# ── 10-step rollout ──────────────────────────────────────────────────────
history = torch.tensor(x_traj[:P], dtype=torch.float32, device=device).unsqueeze(0)
u_seq = torch.tensor(u_traj[P:P+10], dtype=torch.float32, device=device).unsqueeze(0)

predictions = []
current_history = history.clone()
model.eval()
with torch.no_grad():
    for h in range(10):
        u_t = u_seq[:, h, :]
        x_pred = model(current_history, u_t).unsqueeze(1)
        predictions.append(x_pred)
        current_history = torch.cat(
            [current_history[:, 1:, :], x_pred], dim=1
        )

preds = torch.cat(predictions, dim=1).squeeze(0).cpu().numpy()  # (10, 2)
targets = x_traj[P:P+10]

# ── Denormalise ───────────────────────────────────────────────────────────
preds_phys = preds * x_std + x_mean
targets_phys = targets * x_std + x_mean

# ── Metrics ──────────────────────────────────────────────────────────────
errors = targets_phys - preds_phys
rmse_per_step = np.sqrt(np.mean(errors**2, axis=1))
rmse_total = float(np.sqrt(np.mean(errors**2)))
mae_total = float(np.mean(np.abs(errors)))

print()
print("=" * 60)
print("10-step rollout results")
print("=" * 60)
print(f"  Total RMSE: {rmse_total:.4f}")
print(f"  Total MAE:  {mae_total:.4f}")
print()
print(f"  {'Step':>5} | {'RMSE':>10} | {'x1_pred':>8} {'x1_true':>8} | {'x2_pred':>8} {'x2_true':>8}")
print("  " + "-" * 60)
for i in range(10):
    print(f"  {i+1:>5} | {rmse_per_step[i]:>10.4f} | "
          f"{preds_phys[i,0]:>8.3f} {targets_phys[i,0]:>8.3f} | "
          f"{preds_phys[i,1]:>8.3f} {targets_phys[i,1]:>8.3f}")

print()
if rmse_total < 1.0:
    print("  RESULT: Model looks GOOD (avg error < 1.0 on physical units)")
elif rmse_total < 2.0:
    print("  RESULT: Model looks OK (avg error between 1.0 and 2.0)")
else:
    print("  RESULT: Model predictions are poor (avg error > 2.0)")
