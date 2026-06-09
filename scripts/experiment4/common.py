"""Shared helpers for experiment4 parameter sweeps."""

import copy
import itertools
import json
import os
from pathlib import Path

from patchtst_koopman.utils.config_loader import save_config


SCANNABLE_ENCODER_KEYS = (
    "history_length",
    "patch_length",
    "latent_dim",
    "n_layers",
    "d_model",
    "d_ff",
)


def _deep_copy(value):
    return copy.deepcopy(value)


def build_base_config(scan_config):
    base = {
        "experiment": _deep_copy(scan_config["experiment"]),
        "data": _deep_copy(scan_config["data"]),
        "encoder": _deep_copy(scan_config["fixed_model"]["encoder"]),
        "koopman": _deep_copy(scan_config["fixed_model"]["koopman"]),
        "decoder": _deep_copy(scan_config["fixed_model"]["decoder"]),
        "training": _deep_copy(scan_config["fixed_training"]),
    }
    base["training"]["edmd"]["pretrain"]["loss_weights"] = _deep_copy(
        scan_config["fixed_loss_weights"]
    )

    for optional in ("controller", "evaluation", "logging"):
        if optional in scan_config:
            base[optional] = _deep_copy(scan_config[optional])

    return base


def candidate_identifier(params):
    ordered = [
        ("P", params["history_length"]),
        ("p", params["patch_length"]),
        ("d", params["latent_dim"]),
        ("L", params["n_layers"]),
        ("dm", params["d_model"]),
        ("ff", params["d_ff"]),
    ]
    return "__".join(f"{key}{value}" for key, value in ordered)


def summarize_candidate(config, candidate_id):
    pretrain = config["training"]["edmd"]["pretrain"]
    return {
        "candidate_id": candidate_id,
        "history_length": config["encoder"]["history_length"],
        "patch_length": config["encoder"]["patch_length"],
        "latent_dim": config["encoder"]["latent_dim"],
        "n_layers": config["encoder"]["n_layers"],
        "d_model": config["encoder"]["d_model"],
        "d_ff": config["encoder"]["d_ff"],
        "precision": config["experiment"].get("precision", "float32"),
        "batch_size": pretrain["batch_size"],
        "learning_rate": pretrain["learning_rate"],
        "seed": config["experiment"]["seed"],
        "deterministic": config["experiment"].get("deterministic", False),
    }


def validate_candidate(config, fixed_loss_weights, scan_keys):
    encoder = config["encoder"]
    if encoder["history_length"] % encoder["patch_length"] != 0:
        raise ValueError(
            "history_length must be divisible by patch_length: "
            f"{encoder['history_length']} vs {encoder['patch_length']}"
        )
    if encoder["latent_dim"] <= config["data"]["state_dim"]:
        raise ValueError(
            "latent_dim must be greater than state_dim for state-embedded encoder: "
            f"{encoder['latent_dim']} <= {config['data']['state_dim']}"
        )

    current = config["training"]["edmd"]["pretrain"].get("loss_weights", {})
    if current != fixed_loss_weights:
        raise ValueError("loss_weights drifted away from fixed_loss_weights")

    unexpected = set(scan_keys) - set(SCANNABLE_ENCODER_KEYS)
    if unexpected:
        raise ValueError(f"Unsupported scan_space keys: {sorted(unexpected)}")


def expand_candidates(scan_config):
    scan_space = scan_config["scan_space"]
    scan_keys = tuple(scan_space.keys())
    fixed_loss_weights = _deep_copy(scan_config["fixed_loss_weights"])
    base = build_base_config(scan_config)
    candidates = []

    for values in itertools.product(*(scan_space[key] for key in scan_keys)):
        params = dict(zip(scan_keys, values))
        resolved = _deep_copy(base)
        resolved["encoder"].update(params)
        resolved["koopman"]["lifted_dim"] = resolved["encoder"]["latent_dim"]

        try:
            validate_candidate(resolved, fixed_loss_weights, scan_keys)
        except ValueError:
            continue

        candidate_id = candidate_identifier(
            {
                "history_length": resolved["encoder"]["history_length"],
                "patch_length": resolved["encoder"]["patch_length"],
                "latent_dim": resolved["encoder"]["latent_dim"],
                "n_layers": resolved["encoder"]["n_layers"],
                "d_model": resolved["encoder"]["d_model"],
                "d_ff": resolved["encoder"]["d_ff"],
            }
        )
        resolved["experiment"]["name"] = f"{scan_config['experiment']['name']}__{candidate_id}"
        candidates.append(
            {
                "candidate_id": candidate_id,
                "params": params,
                "resolved_config": resolved,
                "summary": summarize_candidate(resolved, candidate_id),
            }
        )

    return candidates


def apply_runtime_overrides(config, args):
    if getattr(args, "precision", None):
        config["experiment"]["precision"] = args.precision
    if getattr(args, "device", None):
        config["experiment"]["device"] = args.device
    if getattr(args, "save_dir", None):
        config["experiment"]["save_dir"] = args.save_dir
    if getattr(args, "log_dir", None):
        config["experiment"]["log_dir"] = args.log_dir
    return config


def choose_candidates(all_candidates, selected_ids=None, limit=None):
    chosen = list(all_candidates)
    if selected_ids:
        selected = {item.strip() for item in selected_ids.split(",") if item.strip()}
        chosen = [candidate for candidate in chosen if candidate["candidate_id"] in selected]
    if limit is not None:
        chosen = chosen[:limit]
    return chosen


def candidate_sort_key(record, selection_cfg):
    ordered_metrics = [selection_cfg["primary_metric"]] + selection_cfg.get("tie_breakers", [])
    values = []
    for name in ordered_metrics:
        value = record.get(name)
        values.append(float("inf") if value is None else value)
    return tuple(values)


def select_best_candidate(results, selection_cfg):
    successful = [r for r in results if r.get("status") == "success"]
    if not successful:
        return None, []
    ranked = sorted(successful, key=lambda item: candidate_sort_key(item, selection_cfg))
    return ranked[0], ranked


def export_alignment_configs(best_config, run_dir, platform):
    exported_main = _deep_copy(best_config)
    exported_main["experiment"]["name"] = f"{platform}_patchtst"

    exported_ablation = _deep_copy(best_config)
    exported_ablation["experiment"]["name"] = f"ablation_{platform}_from_experiment4"
    exported_ablation["ablation"] = {
        "module_variants": ["no_patch", "no_attention", "no_positional"],
        "patch_ablations": [],
        "history_ablations": [],
        "n_layers_ablations": [],
        "latent_dim_ablations": [],
    }

    main_path = os.path.join(run_dir, f"exported_{platform}_main_config.yaml")
    ablation_path = os.path.join(run_dir, f"exported_{platform}_module_ablation_config.yaml")
    save_config(exported_main, main_path)
    save_config(exported_ablation, ablation_path)
    return main_path, ablation_path


def write_json(path, payload):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def write_resolved_config(run_dir, candidate_id, config):
    path = os.path.join(run_dir, candidate_id, "resolved_config.json")
    write_json(path, config)
    return path


def find_latest_results_dir(results_root):
    base = Path(results_root)
    if not base.exists():
        raise FileNotFoundError(f"No experiment4 results found under {results_root}")
    dirs = sorted([d for d in base.iterdir() if d.is_dir()], reverse=True)
    if not dirs:
        raise FileNotFoundError(f"No timestamped run inside {results_root}")
    return str(dirs[0])
