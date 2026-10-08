# -*- coding: utf-8 -*-
"""P2 soft-robot: OLD (fixed time-invariant Koopman) vs NEW (history-conditioned A(c)).

Open-loop rollout with true inputs on the TEST set (10 trajectories x 300 steps).
Multiple rollouts per trajectory (several start indices); produces:
  - 杂项/图表/p2_old_vs_new_trajectories.png   (per-trajectory phase plots)
  - 杂项/图表/p2_old_vs_new_curves.png         (RMSE vs horizon + per-trajectory bars)
  - 杂项/实验结果/p2_old_vs_new_rollout.json   (numbers)

Self-contained: uses checkpoints in 杂项/模型检查点 and model classes in 杂项/研究代码.
"""
import os, sys, json
import numpy as np
import torch

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gate_context_koopman import CtxKoopman, build_split, H_EVAL, H_MAX, REPO, DEV  # noqa: E402
from gate14_stabilize import BudgetedCtxKoopman  # noqa: E402
from patchtst_koopman.utils.config_loader import load_config  # noqa: E402

ROOT = r"D:\Project\Transformer-Koopman\Transformer-Koopman"
CKPT = os.path.join(ROOT, "杂项", "模型检查点")
FIGDIR = os.path.join(ROOT, "杂项", "图表")
RESDIR = os.path.join(ROOT, "杂项", "实验结果")
os.makedirs(FIGDIR, exist_ok=True); os.makedirs(RESDIR, exist_ok=True)

SPLIT = "test"
H = H_MAX                     # rollout horizon
STRIDE = 20                   # start-index stride -> many rollouts per trajectory

cfg = load_config(os.path.join(REPO, "configs", "platform2.yaml"))
data_dir = os.path.abspath(os.path.join(REPO, cfg["data"]["data_dir"]))
P = cfg["encoder"]["history_length"]

# normalization from the training split (same for both models)
_, _, _, _, norm = build_split(data_dir, "train", cfg)

# ---- load models ----
old = CtxKoopman(cfg, "fixed", r=3).to(DEV)
old.load_state_dict(torch.load(os.path.join(CKPT, "fixed.pt"), map_location=DEV)); old.eval()

new = BudgetedCtxKoopman(cfg, r=2, delta_A=0.07).to(DEV)
missing, unexpected = new.load_state_dict(
    torch.load(os.path.join(CKPT, "A_stab_openloop_lam0.0_rho0.99.pt"), map_location=DEV), strict=False)
new.eval()
print(f"[load] old=fixed.pt  new=A_stab_openloop_lam0.0_rho0.99.pt  (missing={len(missing)}, unexpected={len(unexpected)})")
print(f"[data] {SPLIT}: dir={data_dir}  P={P}  H={H}  stride={STRIDE}  device={DEV}")


def denorm(z):
    return z * norm["x_std"] + norm["x_mean"]


def rollout(model, xx, uu, k, H):
    """Open-loop rollout with true inputs; history buffer updated with predicted states."""
    xh = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
    uh = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
    preds = []
    with torch.no_grad():
        for h in range(1, H + 1):
            ut = torch.tensor(uu[k + h - 1], dtype=torch.float32).unsqueeze(0).to(DEV)
            xn = model(xh, uh, ut)
            xh = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
            uh = torch.cat([uh[:, 1:, :], ut.unsqueeze(1)], dim=1)
            preds.append(xn.squeeze(0).cpu().numpy())
    return np.array(preds)


# ---- load test set ----
d = np.load(os.path.join(data_dir, f"{SPLIT}.npz"))
x = (d["x"].astype(np.float64) - norm["x_mean"]) / norm["x_std"]
u = (d["u"].astype(np.float64) - norm["u_mean"]) / norm["u_std"]
tid = d["trajectory_id"]

per_traj = {}
err_old = {h: [] for h in range(1, H + 1)}
err_new = {h: [] for h in range(1, H + 1)}
example = {}   # one rollout per trajectory for the visual

for t in np.unique(tid):
    idx = np.where(tid == t)[0]
    xx, uu = x[idx], u[idx]
    eo = {h: [] for h in range(1, H + 1)}
    en = {h: [] for h in range(1, H + 1)}
    for k in range(P - 1, len(xx) - H - 1, STRIDE):
        po = rollout(old, xx, uu, k, H)
        pn = rollout(new, xx, uu, k, H)
        gt = xx[k + 1:k + 1 + H]
        for h in range(1, H + 1):
            eo[h].append(np.linalg.norm(po[h - 1] - gt[h - 1]))
            en[h].append(np.linalg.norm(pn[h - 1] - gt[h - 1]))
        if t not in example:
            example[t] = (k, denorm(gt), denorm(po), denorm(pn))
    ro = {h: float(np.sqrt(np.mean(np.square(eo[h])))) for h in eo}
    rn = {h: float(np.sqrt(np.mean(np.square(en[h])))) for h in en}
    per_traj[str(int(t))] = {"n_rollouts": len(eo[1]), "old": ro, "new": rn}
    for h in range(1, H + 1):
        err_old[h].extend(eo[h]); err_new[h].extend(en[h])
    print(f"  traj {int(t):2d}: rollouts={len(eo[1]):2d}  RMSE@H20  old={ro[H]:.4f}  new={rn[H]:.4f}  ({ro[H]/rn[H]:.2f}x)")

agg_old = {h: float(np.sqrt(np.mean(np.square(err_old[h])))) for h in range(1, H + 1)}
agg_new = {h: float(np.sqrt(np.mean(np.square(err_new[h])))) for h in range(1, H + 1)}

print("\n=== aggregate open-loop rollout RMSE over TEST set (normalized) ===")
print("  H      old(fixed)   new(A(c))   old/new")
for h in [1, 5, 10, 20]:
    print(f"  {h:<4}   {agg_old[h]:.5f}    {agg_new[h]:.5f}    {agg_old[h]/agg_new[h]:.2f}x")

# ---- plots ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Figure 1: per-trajectory phase plots
tids = [int(t) for t in np.unique(tid)]
ncol = 5; nrow = int(np.ceil(len(tids) / ncol))
fig, axes = plt.subplots(nrow, ncol, figsize=(4.0 * ncol, 3.6 * nrow))
axes = np.atleast_2d(axes)
for j, t in enumerate(tids):
    ax = axes[j // ncol, j % ncol]
    k, gt, po, pn = example[t]
    ax.plot(gt[:, 0], gt[:, 1], "k-", lw=2.2, label="ground truth")
    ax.plot(po[:, 0], po[:, 1], "--s", color="tab:red", ms=3, lw=1.5, label="old: fixed A")
    ax.plot(pn[:, 0], pn[:, 1], "-^", color="tab:blue", ms=3, lw=1.5, label="new: A(c)")
    ax.scatter([gt[0, 0]], [gt[0, 1]], s=70, facecolors="none", edgecolors="k", zorder=5)
    ax.set_title(f"test traj {t} (H={H})", fontsize=9)
    ax.grid(alpha=0.3); ax.set_aspect("equal", adjustable="datalim")
    if j == 0:
        ax.legend(fontsize=7)
for j in range(len(tids), nrow * ncol):
    axes[j // ncol, j % ncol].axis("off")
fig.suptitle("P2 soft-robot, TEST set: open-loop rollout (old fixed Koopman vs new history-conditioned A(c))", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.97])
f1 = os.path.join(FIGDIR, "p2_old_vs_new_trajectories.png")
fig.savefig(f1, dpi=140); plt.close(fig)
print("saved:", f1)

# Figure 2: aggregate curves + per-trajectory bars
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
haxis = np.arange(1, H + 1)
axes[0].semilogy(haxis, [agg_old[h] for h in haxis], "--s", color="tab:red", ms=4, label="old: fixed A")
axes[0].semilogy(haxis, [agg_new[h] for h in haxis], "-^", color="tab:blue", ms=4, label="new: A(c)")
axes[0].set_title("Aggregate rollout RMSE vs horizon (TEST set, 10 trajectories)")
axes[0].set_xlabel("horizon step h"); axes[0].set_ylabel("RMSE (normalized, log)")
axes[0].legend(fontsize=9); axes[0].grid(alpha=0.3, which="both")

xo = [per_traj[str(t)]["old"][H] for t in tids]
xn = [per_traj[str(t)]["new"][H] for t in tids]
w = 0.38; xs = np.arange(len(tids))
axes[1].bar(xs - w / 2, xo, w, color="tab:red", alpha=0.8, label="old: fixed A")
axes[1].bar(xs + w / 2, xn, w, color="tab:blue", alpha=0.8, label="new: A(c)")
axes[1].set_xticks(xs); axes[1].set_xticklabels([str(t) for t in tids])
axes[1].set_title(f"Per-trajectory RMSE at H={H} (TEST)")
axes[1].set_xlabel("test trajectory id"); axes[1].set_ylabel(f"RMSE@H={H} (normalized)")
axes[1].legend(fontsize=9); axes[1].grid(alpha=0.3, axis="y")
fig.tight_layout()
f2 = os.path.join(FIGDIR, "p2_old_vs_new_curves.png")
fig.savefig(f2, dpi=140); plt.close(fig)
print("saved:", f2)

# ---- JSON ----
summary = {
    "split": SPLIT, "H": H, "stride": STRIDE, "n_trajectories": len(tids),
    "old_model": "fixed.pt (fixed time-invariant Koopman)",
    "new_model": "A_stab_openloop_lam0.0_rho0.99.pt (history-conditioned A(c), rollout-trained)",
    "aggregate_rmse_normalized": {"old": {str(h): agg_old[h] for h in [1, 5, 10, 20]},
                                  "new": {str(h): agg_new[h] for h in [1, 5, 10, 20]},
                                  "improvement_x": {str(h): agg_old[h] / agg_new[h] for h in [1, 5, 10, 20]}},
    "per_trajectory": per_traj,
}
jf = os.path.join(RESDIR, "p2_old_vs_new_rollout.json")
with open(jf, "w", encoding="utf-8", newline="") as fh:
    json.dump(summary, fh, ensure_ascii=False, indent=2)
print("saved:", jf)
