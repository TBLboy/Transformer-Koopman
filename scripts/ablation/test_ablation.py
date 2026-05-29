"""Test all ablation variants in a results directory and compare against baseline."""
import argparse
import copy
import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

from patchtst_koopman.ablation.models import ABLATION_MODELS
from patchtst_koopman.data.dataset import KoopmanDataset
from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.device import resolve_device
from patchtst_koopman.utils.seed import configure_cuda_performance


def find_latest_results_dir(platform, results_root):
    base = Path(results_root) / f"ablation_{platform}"
    if not base.exists():
        raise FileNotFoundError(f"No ablation results found under {base}")
    dirs = sorted([d for d in base.iterdir() if d.is_dir()], reverse=True)
    if not dirs:
        raise FileNotFoundError(f"No timestamped run inside {base}")
    return str(dirs[0])


def create_model(variant_id, config):
    cfg = copy.deepcopy(config)
    if variant_id == "full_model":
        return PatchTSTKoopmanModel(cfg)
    if variant_id in ("no_patch", "no_attention", "no_positional"):
        return ABLATION_MODELS[variant_id](cfg)
    if variant_id.startswith("patch_L"):
        L_val = int(variant_id.replace("patch_L", ""))
        return ABLATION_MODELS["patch_L"](cfg, L_val)
    if variant_id.startswith("history_P"):
        P_val = int(variant_id.replace("history_P", ""))
        return ABLATION_MODELS["history_P"](cfg, P_val)
    if variant_id.startswith("n_layers_L"):
        L_val = int(variant_id.replace("n_layers_L", ""))
        return ABLATION_MODELS["n_layers"](cfg, L_val)
    if variant_id.startswith("latent_dim_d"):
        d_val = int(variant_id.replace("latent_dim_d", ""))
        return ABLATION_MODELS["latent_dim"](cfg, d_val)
    raise ValueError(f"Unknown variant id: {variant_id}")


def load_variant_checkpoint(variant_id, model_path, device, fallback_config):
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    saved_config = checkpoint.get("config", fallback_config)
    saved_config["experiment"]["device"] = device

    try:
        model = create_model(variant_id, saved_config)
    except Exception:
        model = create_model(variant_id, fallback_config)

    precision = saved_config["experiment"].get("precision", "float32")
    model = model.double() if precision == "float64" else model.float()
    model = model.to(device)
    model.load_state_dict(checkpoint.get("model_state_dict", checkpoint), strict=False)
    model.eval()

    return model, checkpoint.get("normalization", {}), saved_config


def evaluate_rollout(model, test_dataset, config, norm_stats, device):
    model.eval()
    P = config["encoder"]["history_length"]
    precision = config["experiment"].get("precision", "float32")
    dtype = torch.float64 if precision == "float64" else torch.float32

    target_id = np.unique(test_dataset.trajectory_id)[0]
    mask = test_dataset.trajectory_id == target_id
    x_traj = test_dataset.x[mask]
    u_traj = test_dataset.u[mask]

    if len(x_traj) - P < 1:
        return {"rmse": float("inf"), "mae": float("inf"), "per_dim_rmse": []}

    x_history = torch.tensor(x_traj[:P, :], dtype=dtype).to(device)
    u_sequence = torch.tensor(u_traj[P - 1 : -1, :], dtype=dtype).to(device)
    x_true_norm = x_traj[P:, :]

    preds = []
    with torch.no_grad():
        for h in range(len(u_sequence)):
            z_t = model.encoder(x_history.unsqueeze(0))
            z_next = model.koopman(z_t, u_sequence[h : h + 1, :])
            x_next = model.decoder(z_next)
            preds.append(x_next.squeeze(0).cpu().numpy())
            x_history = torch.cat([x_history[1:, :], x_next], dim=0)

    x_pred_norm = np.array(preds)
    x_mean, x_std = norm_stats.get("x_mean"), norm_stats.get("x_std")
    if x_mean is not None and x_std is not None:
        x_pred = x_pred_norm * x_std + x_mean
        x_true = x_true_norm * x_std + x_mean
    else:
        x_pred, x_true = x_pred_norm, x_true_norm

    rmse = float(np.sqrt(np.mean((x_pred - x_true) ** 2)))
    mae = float(np.mean(np.abs(x_pred - x_true)))
    per_dim_rmse = [
        float(np.sqrt(np.mean((x_pred[:, d] - x_true[:, d]) ** 2)))
        for d in range(x_true.shape[1])
    ]
    return {"rmse": rmse, "mae": mae, "per_dim_rmse": per_dim_rmse}


def main():
    parser = argparse.ArgumentParser(description="Test ablation variants")
    parser.add_argument("--platform", type=str, default="platform1", choices=["platform1", "platform2"])
    parser.add_argument("--results_dir", type=str, default=None, help="Timestamped run dir")
    parser.add_argument("--results_root", type=str, default="./results/models", help="Where ablation runs live")
    parser.add_argument("--config", type=str, default=None)
    args = parser.parse_args()

    results_dir = args.results_dir or find_latest_results_dir(args.platform, args.results_root)
    config_path = args.config or f"configs/{args.platform}.yaml"

    print("=" * 70)
    print(f"Testing ablation variants for {args.platform}")
    print(f"  Run dir: {results_dir}")
    print(f"  Config:  {config_path}")
    print("=" * 70)

    results_file = os.path.join(results_dir, "ablation_results.json")
    if not os.path.exists(results_file):
        raise FileNotFoundError(f"Cannot find {results_file}")

    with open(results_file, "r", encoding="utf-8") as f:
        results_data = json.load(f)

    base_config = load_config(config_path)
    device = resolve_device(base_config["experiment"].get("device", "cuda"))
    base_config["experiment"]["device"] = device
    configure_cuda_performance(base_config)
    base_config["data"]["platform"] = args.platform

    test_metrics = {}
    for variant_id, result in results_data["results"].items():
        if result.get("status") != "success":
            print(f"  Skipping {variant_id}: training failed")
            continue
        model_path = result["model_path"]
        if not os.path.isabs(model_path):
            # Try resolving relative to results_dir first, then CWD
            for candidate in [
                os.path.join(results_dir, variant_id, f"{variant_id}_model.pth"),
                model_path,
            ]:
                if os.path.exists(candidate):
                    model_path = candidate
                    break
        if not os.path.exists(model_path):
            print(f"  Skipping {variant_id}: checkpoint not found ({model_path})")
            continue

        print(f"  Loading {variant_id} ({result['name']})...", end="", flush=True)
        model, norm_stats, saved_config = load_variant_checkpoint(
            variant_id, model_path, device, base_config
        )

        test_dataset = KoopmanDataset(
            base_config["data"]["data_dir"], saved_config, "test", norm_stats=norm_stats
        )
        metrics = evaluate_rollout(model, test_dataset, saved_config, norm_stats, device)
        test_metrics[variant_id] = {
            **metrics,
            "name": result["name"],
            "params": result.get("params", 0),
        }
        print(f"  RMSE={metrics['rmse']:.6f}  MAE={metrics['mae']:.6f}")

    baseline_rmse = test_metrics.get("full_model", {}).get("rmse")
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"{'Variant':<40} {'RMSE':>12} {'MAE':>12} {'Params':>12} {'Delta':>10}")
    print("-" * 90)
    for variant_id, m in test_metrics.items():
        rmse = m["rmse"]
        mae = m["mae"]
        params = m["params"]
        if baseline_rmse and variant_id != "full_model":
            delta = (rmse - baseline_rmse) / baseline_rmse * 100
            delta_str = f"{delta:+7.1f}%"
        else:
            delta_str = "baseline"
        print(f"{m['name']:<40} {rmse:>12.6f} {mae:>12.6f} {params:>10,} {delta_str:>10}")

    save_path = os.path.join(results_dir, "test_results.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "platform": args.platform,
                "results_dir": results_dir,
                "config_path": config_path,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "test_metrics": test_metrics,
                "baseline_rmse": baseline_rmse,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"\nSaved: {save_path}")


if __name__ == "__main__":
    main()
