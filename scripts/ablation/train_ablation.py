"""Run ablation training for a platform.

Usage:
    python scripts/ablation/train_ablation.py --platform platform2 --variants all
    python scripts/ablation/train_ablation.py --platform platform1 --variants module
    python scripts/ablation/train_ablation.py --platform platform1 --variants hyperparameter
    python scripts/ablation/train_ablation.py --platform platform2 --variants full_model
    python scripts/ablation/train_ablation.py --platform platform1 --variants no_patch,no_attention
"""
import argparse
import copy
import json
import os
import traceback
from datetime import datetime

import numpy as np
import torch

from patchtst_koopman.ablation.models import ABLATION_MODELS
from patchtst_koopman.ablation.platform_configs import PLATFORM_CONFIGS, get_platform_config
from patchtst_koopman.training.edmd_trainer import EDMDTrainer
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.data_prep import prepare_datasets
from patchtst_koopman.utils.device import resolve_device
from patchtst_koopman.utils.evaluation import evaluate_on_first_trajectory
from patchtst_koopman.training.performance import apply_gpu_training_defaults
from patchtst_koopman.utils.seed import configure_cuda_performance, set_seed


def build_ablation_variants(platform):
    """Build the dict of ``variant_id -> {name, create_model, config_updates}``."""
    platform_config = get_platform_config(platform)

    variants = {
        "full_model": {
            "name": "Full Model (Baseline)",
            "create_model": lambda config: ABLATION_MODELS["full_model"](config),
            "config_updates": {},
        },
        "no_patch": {
            "name": "Without Patching",
            "create_model": lambda config: ABLATION_MODELS["no_patch"](config),
            "config_updates": {},
        },
        "no_attention": {
            "name": "Without Attention",
            "create_model": lambda config: ABLATION_MODELS["no_attention"](config),
            "config_updates": {},
        },
        "no_positional": {
            "name": "Without Positional Encoding",
            "create_model": lambda config: ABLATION_MODELS["no_positional"](config),
            "config_updates": {},
        },
    }

    for L in platform_config["patch_ablations"]:
        variants[f"patch_L{L}"] = {
            "name": f"Patch Length L={L}",
            "create_model": lambda config, L=L: ABLATION_MODELS["patch_L"](config, L),
            "config_updates": {"encoder": {"patch_length": L}},
        }

    for P in platform_config["history_ablations"]:
        variants[f"history_P{P}"] = {
            "name": f"History P={P}",
            "create_model": lambda config, P=P: ABLATION_MODELS["history_P"](config, P),
            "config_updates": {"encoder": {"history_length": P}},
        }

    for L in platform_config["n_layers_ablations"]:
        variants[f"n_layers_L{L}"] = {
            "name": f"Transformer L={L} layers",
            "create_model": lambda config, L=L: ABLATION_MODELS["n_layers"](config, L),
            "config_updates": {"encoder": {"n_layers": L}},
        }

    for d in platform_config["latent_dim_ablations"]:
        variants[f"latent_dim_d{d}"] = {
            "name": f"Latent dim d={d}",
            "create_model": lambda config, d=d: ABLATION_MODELS["latent_dim"](config, d),
            "config_updates": {
                "encoder": {"latent_dim": d},
                "koopman": {"lifted_dim": d},
            },
        }

    return variants


def apply_config_updates(config, updates):
    """Return a deepcopy of ``config`` with nested updates merged in."""
    updated = copy.deepcopy(config)
    for section, section_updates in updates.items():
        if section not in updated:
            updated[section] = {}
        updated[section].update(section_updates)
    return updated


def save_ablation_checkpoint(model, save_dir, filename, config, norm_stats):
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    A, B = model.get_koopman_matrices()
    spectral_radius = float(np.max(np.abs(np.linalg.eigvals(A))))

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "config": config,
        "koopman_A": A,
        "koopman_B": B,
        "spectral_radius": spectral_radius,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model_info": {
            "state_dim": config["data"]["state_dim"],
            "control_dim": config["data"]["control_dim"],
            "latent_dim": config["encoder"]["latent_dim"],
            "history_length": config["encoder"]["history_length"],
            "patch_length": config["encoder"]["patch_length"],
        },
        "normalization": {
            "x_mean": norm_stats["x_mean"],
            "x_std": norm_stats["x_std"],
            "u_mean": norm_stats["u_mean"],
            "u_std": norm_stats["u_std"],
        },
    }
    torch.save(checkpoint, save_path)
    print(f"  Saved: {save_path}  rho={spectral_radius:.4f}")
    return save_path


def train_variant(variant_id, variant_info, base_config, device, save_dir):
    print("\n" + "=" * 60)
    print(f"Training variant: {variant_info['name']}")
    print("=" * 60)

    try:
        config = apply_config_updates(base_config, variant_info.get("config_updates", {}))
        config["experiment"]["device"] = device

        print(
            f"  P={config['encoder']['history_length']}, p={config['encoder']['patch_length']}, "
            f"d={config['encoder']['latent_dim']}, L={config['encoder']['n_layers']}, "
            f"precision={config['experiment'].get('precision', 'float32')}"
        )

        variant_save_dir = os.path.join(save_dir, variant_id)
        os.makedirs(variant_save_dir, exist_ok=True)
        config["experiment"]["save_dir"] = variant_save_dir

        train_dataset, val_dataset, test_dataset, norm_stats = prepare_datasets(config)

        model = variant_info["create_model"](config)
        if config["experiment"].get("precision", "float32") == "float64":
            model = model.double()
        else:
            model = model.float()
        model = model.to(device)

        total_params = sum(p.numel() for p in model.parameters())
        print(f"  Total parameters: {total_params:,}")

        trainer = EDMDTrainer(model, config)
        trainer.train(train_dataset, val_dataset)

        rollout = evaluate_on_first_trajectory(model, test_dataset, config, norm_stats)
        print(f"  Test RMSE: {rollout['rmse']:.6f}  MAE: {rollout['mae']:.6f}")

        model_path = save_ablation_checkpoint(
            model, variant_save_dir, f"{variant_id}_model.pth", config, norm_stats
        )

        return {
            "name": variant_info["name"],
            "rmse": rollout["rmse"],
            "mae": rollout["mae"],
            "params": total_params,
            "status": "success",
            "model_path": model_path,
            "config": {
                "history_length": config["encoder"]["history_length"],
                "patch_length": config["encoder"]["patch_length"],
                "latent_dim": config["encoder"]["latent_dim"],
                "n_layers": config["encoder"]["n_layers"],
                "precision": config["experiment"].get("precision", "float32"),
                "device": device,
            },
        }

    except Exception as exc:
        print(f"  Variant failed: {exc}")
        traceback.print_exc()
        return {
            "name": variant_info["name"],
            "rmse": None,
            "mae": None,
            "params": None,
            "status": "failed",
            "error": str(exc),
        }


def select_variants(args_variants, all_variants):
    """Translate the ``--variants`` argument into a subset of ``all_variants``."""
    if args_variants == "all":
        return all_variants
    if args_variants == "module":
        keys = {"full_model", "no_patch", "no_attention", "no_positional"}
        return {k: v for k, v in all_variants.items() if k in keys}
    if args_variants == "hyperparameter":
        prefixes = ("patch_", "history_", "n_layers_", "latent_dim_")
        return {k: v for k, v in all_variants.items() if any(k.startswith(p) for p in prefixes)}
    if args_variants == "full_model":
        return {"full_model": all_variants["full_model"]}
    if args_variants in {"patch", "history", "n_layers", "latent_dim"}:
        prefix = args_variants + "_"
        return {k: v for k, v in all_variants.items() if k.startswith(prefix)}
    selected = [s.strip() for s in args_variants.split(",")]
    return {k: v for k, v in all_variants.items() if k in selected}


def main():
    parser = argparse.ArgumentParser(description="Ablation training")
    parser.add_argument(
        "--platform",
        type=str,
        default="platform1",
        choices=list(PLATFORM_CONFIGS.keys()),
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="YAML config path (defaults to configs/<platform>.yaml)",
    )
    parser.add_argument(
        "--variants",
        type=str,
        default="all",
        help="all / module / hyperparameter / full_model / patch / history / n_layers / latent_dim / <comma list>",
    )
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--precision", type=str, default=None, choices=["float32", "float64"])
    parser.add_argument(
        "--save_dir", type=str, default=None, help="Override config.experiment.save_dir"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Ablation training")
    print("=" * 60)
    print(f"  Platform: {args.platform}  ({PLATFORM_CONFIGS[args.platform]['name']})")

    config_path = args.config or f"configs/{args.platform}.yaml"
    config = load_config(config_path)
    print(f"  Config:   {config_path}")

    if args.precision:
        config["experiment"]["precision"] = args.precision

    apply_gpu_training_defaults(config)

    device = resolve_device(args.device or config["experiment"]["device"])
    config["experiment"]["device"] = device
    config["data"]["platform"] = args.platform

    set_seed(config["experiment"]["seed"])
    configure_cuda_performance(config)
    precision = config["experiment"].get("precision", "float32")
    torch.set_default_dtype(torch.float64 if precision == "float64" else torch.float32)

    print(f"  Device:   {device}")
    print(
        f"  Training: batch={config['training']['edmd']['pretrain']['batch_size']}, "
        f"workers={config['training'].get('num_workers', 0)}, "
        f"amp={config['experiment'].get('amp', True)}"
    )

    save_base_dir = args.save_dir or config["experiment"]["save_dir"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join(save_base_dir, f"ablation_{args.platform}", timestamp)
    os.makedirs(save_dir, exist_ok=True)

    all_variants = build_ablation_variants(args.platform)
    variants_to_run = select_variants(args.variants, all_variants)

    print(f"\nVariants to run: {len(variants_to_run)}")
    for vid, vinfo in variants_to_run.items():
        print(f"  - {vid}: {vinfo['name']}")

    all_results = {}
    for variant_id, variant_info in variants_to_run.items():
        all_results[variant_id] = train_variant(
            variant_id, variant_info, config, device, save_dir
        )
        if device == "cuda":
            torch.cuda.empty_cache()

    baseline_rmse = all_results.get("full_model", {}).get("rmse")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"\n{'Variant':<40} {'RMSE':<12} {'MAE':<12} {'Delta':<10}")
    print("-" * 74)
    for variant_id, result in all_results.items():
        rmse = result.get("rmse")
        mae = result.get("mae")
        if rmse is not None and baseline_rmse is not None and variant_id != "full_model":
            delta = (rmse - baseline_rmse) / baseline_rmse * 100
            print(f"{result['name']:<40} {rmse:<12.6f} {mae:<12.6f} {delta:>+8.2f}%")
        elif rmse is not None:
            print(f"{result['name']:<40} {rmse:<12.6f} {mae:<12.6f} {'baseline':<10}")
        else:
            print(f"{result['name']:<40} {'FAILED':<12}")

    platform_config = PLATFORM_CONFIGS[args.platform]
    results_file = os.path.join(save_dir, "ablation_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "platform": args.platform,
                "platform_name": platform_config["name"],
                "timestamp": timestamp,
                "baseline_params": platform_config["baseline"],
                "ablation_ranges": {
                    "patch_lengths": platform_config["patch_ablations"],
                    "history_lengths": platform_config["history_ablations"],
                    "n_layers": platform_config["n_layers_ablations"],
                    "latent_dims": platform_config["latent_dim_ablations"],
                },
                "results": all_results,
                "baseline_rmse": baseline_rmse,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"\nResults saved: {results_file}")
    print(f"Models saved:  {save_dir}")


if __name__ == "__main__":
    main()
