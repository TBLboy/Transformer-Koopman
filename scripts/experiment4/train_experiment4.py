"""Train experiment4 parameter sweep for one platform."""

import argparse
import copy
import os
import shutil
import traceback
from datetime import datetime

import torch
from torch.utils.data import DataLoader

from common import (
    apply_runtime_overrides,
    choose_candidates,
    expand_candidates,
    export_alignment_configs,
    select_best_candidate,
    write_json,
    write_resolved_config,
)
from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
from patchtst_koopman.training.edmd_trainer import EDMDTrainer
from patchtst_koopman.training.performance import apply_gpu_training_defaults
from patchtst_koopman.utils.checkpoint import save_model
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.utils.data_prep import prepare_datasets
from patchtst_koopman.utils.device import resolve_device
from patchtst_koopman.utils.evaluation import evaluate_on_first_trajectory
from patchtst_koopman.utils.seed import configure_cuda_performance, get_worker_init_fn, set_seed


def parse_args():
    parser = argparse.ArgumentParser(description="Train experiment4 parameter sweep")
    parser.add_argument("--platform", type=str, default="platform1", choices=["platform1", "platform2"])
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--precision", type=str, default=None, choices=["float32", "float64"])
    parser.add_argument("--save_dir", type=str, default=None)
    parser.add_argument("--log_dir", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--candidates", type=str, default=None)
    return parser.parse_args()


def build_model(config):
    precision = config["experiment"].get("precision", "float32")
    model = PatchTSTKoopmanModel(config)
    model = model.double() if precision == "float64" else model.float()
    return model.to(config["experiment"]["device"])


def evaluate_one_step_rmse(model, dataset, config):
    training = config["training"]
    seed = config["experiment"]["seed"]
    num_workers = training.get("num_workers", 0)
    loader_kwargs = {
        "batch_size": config["training"]["edmd"]["pretrain"]["batch_size"],
        "shuffle": False,
        "num_workers": num_workers,
        "worker_init_fn": get_worker_init_fn(seed),
        "generator": torch.Generator().manual_seed(seed),
    }
    if config["experiment"]["device"] == "cuda":
        loader_kwargs["pin_memory"] = True
        if num_workers > 0:
            loader_kwargs["persistent_workers"] = True
            loader_kwargs["prefetch_factor"] = training.get("prefetch_factor", 4)

    loader = DataLoader(dataset, **loader_kwargs)
    total_loss = 0.0
    with torch.no_grad():
        for batch in loader:
            x_history = batch["x_history"].to(config["experiment"]["device"], non_blocking=True)
            u_t = batch["u_t"].to(config["experiment"]["device"], non_blocking=True)
            x_next = batch["x_next"].to(config["experiment"]["device"], non_blocking=True)
            x_pred = model(x_history, u_t)
            total_loss += torch.nn.functional.mse_loss(x_pred, x_next).item()
    return (total_loss / len(loader)) ** 0.5


def train_candidate(candidate, run_dir, selection_cfg):
    candidate_id = candidate["candidate_id"]
    config = copy.deepcopy(candidate["resolved_config"])
    candidate_dir = os.path.join(run_dir, candidate_id)
    os.makedirs(candidate_dir, exist_ok=True)
    config["experiment"]["save_dir"] = candidate_dir
    write_resolved_config(run_dir, candidate_id, config)

    print("\n" + "=" * 72)
    print(f"Training candidate: {candidate_id}")
    print("=" * 72)
    print(candidate["summary"])

    set_seed(config["experiment"]["seed"], deterministic=config["experiment"].get("deterministic", False))
    train_dataset, val_dataset, test_dataset, norm_stats = prepare_datasets(config)
    model = build_model(config)
    total_params = sum(param.numel() for param in model.parameters())

    trainer = EDMDTrainer(model, config)
    trainer.train(train_dataset, val_dataset)

    final_model_path = save_model(model, config, norm_stats=norm_stats, filename="final_model.pth")
    best_candidate_checkpoint = os.path.join(candidate_dir, "best_model.pth")
    shutil.copy2(final_model_path, best_candidate_checkpoint)

    val_one_step_rmse = evaluate_one_step_rmse(model, val_dataset, config)
    val_rollout = evaluate_on_first_trajectory(model, val_dataset, config, norm_stats)
    test_rollout = evaluate_on_first_trajectory(model, test_dataset, config, norm_stats)

    train_metrics = {
        "candidate_id": candidate_id,
        "status": "success",
        "selection_source_split": selection_cfg.get("source_split", "val"),
        "val_one_step_rmse": float(val_one_step_rmse),
        "val_rollout_rmse": float(val_rollout["rmse"]),
        "val_rollout_mae": float(val_rollout["mae"]),
        "test_rollout_rmse_preview": float(test_rollout["rmse"]),
        "test_rollout_mae_preview": float(test_rollout["mae"]),
        "params": total_params,
        "final_model_path": final_model_path,
        "best_model_path": best_candidate_checkpoint,
        "pretrain_best_path": os.path.join(candidate_dir, "pretrain_best.pth"),
        "config": candidate["summary"],
    }
    write_json(os.path.join(candidate_dir, "train_metrics.json"), train_metrics)
    write_json(
        os.path.join(candidate_dir, "rollout_metrics.json"),
        {
            "validation": {
                "rmse": float(val_rollout["rmse"]),
                "mae": float(val_rollout["mae"]),
            },
            "test_preview": {
                "rmse": float(test_rollout["rmse"]),
                "mae": float(test_rollout["mae"]),
            },
        },
    )
    return train_metrics


def main():
    args = parse_args()
    config_path = args.config or f"scripts/experiment4/experiment4_{args.platform}.yaml"
    scan_config = load_config(config_path)
    apply_runtime_overrides(scan_config, args)
    apply_gpu_training_defaults(scan_config)

    device = resolve_device(scan_config["experiment"]["device"])
    scan_config["experiment"]["device"] = device
    scan_config["data"]["platform"] = args.platform

    set_seed(scan_config["experiment"]["seed"])
    configure_cuda_performance(scan_config)
    precision = scan_config["experiment"].get("precision", "float32")
    torch.set_default_dtype(torch.float64 if precision == "float64" else torch.float32)

    all_candidates = choose_candidates(
        expand_candidates(scan_config),
        selected_ids=args.candidates,
        limit=args.limit,
    )
    if not all_candidates:
        raise RuntimeError("No valid experiment4 candidates generated from scan_space")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(scan_config["experiment"]["save_dir"], args.platform, timestamp)

    print("=" * 72)
    print("Experiment4 parameter sweep")
    print("=" * 72)
    print(f"Platform:   {args.platform}")
    print(f"Config:     {config_path}")
    print(f"Device:     {device}")
    print(f"Candidates: {len(all_candidates)}")

    manifest = {
        "platform": args.platform,
        "config_path": config_path,
        "candidate_count": len(all_candidates),
        "candidate_ids": [candidate["candidate_id"] for candidate in all_candidates],
        "candidates": [candidate["summary"] for candidate in all_candidates],
    }
    if args.dry_run:
        print("Dry-run only; no training will be executed.")
        for summary in manifest["candidates"]:
            print(f"  - {summary['candidate_id']}")
        return

    os.makedirs(run_dir, exist_ok=True)
    selection_cfg = scan_config["selection"]
    scan_metadata = {
        "platform": args.platform,
        "timestamp": timestamp,
        "config_path": config_path,
        "selection": selection_cfg,
        "scan_space": scan_config["scan_space"],
        "candidate_count": len(all_candidates),
    }
    write_json(os.path.join(run_dir, "selection_summary.json"), scan_metadata)
    write_json(os.path.join(run_dir, "candidate_manifest.json"), manifest)

    results = []
    for candidate in all_candidates:
        try:
            results.append(train_candidate(candidate, run_dir, selection_cfg))
        except Exception as exc:
            traceback.print_exc()
            failure = {
                "candidate_id": candidate["candidate_id"],
                "status": "failed",
                "error": str(exc),
                "config": candidate["summary"],
            }
            results.append(failure)
            os.makedirs(os.path.join(run_dir, candidate["candidate_id"]), exist_ok=True)
            write_json(os.path.join(run_dir, candidate["candidate_id"], "train_metrics.json"), failure)
        if device == "cuda":
            torch.cuda.empty_cache()

    best_candidate, ranking = select_best_candidate(results, selection_cfg)
    if best_candidate is None:
        raise RuntimeError("All experiment4 candidates failed")

    best_resolved = next(
        candidate["resolved_config"]
        for candidate in all_candidates
        if candidate["candidate_id"] == best_candidate["candidate_id"]
    )
    main_export_path, ablation_export_path = export_alignment_configs(
        best_resolved,
        run_dir,
        args.platform,
    )

    write_json(
        os.path.join(run_dir, "best_config.json"),
        {
            "platform": args.platform,
            "selected_by": selection_cfg,
            "best_candidate": best_candidate,
            "exported_main_config": main_export_path,
            "exported_module_ablation_config": ablation_export_path,
            "resolved_config": best_resolved,
        },
    )
    write_json(
        os.path.join(run_dir, "scan_results.json"),
        {
            **scan_metadata,
            "results": results,
            "ranking": ranking,
            "best_candidate_id": best_candidate["candidate_id"],
        },
    )

    print("\n" + "=" * 72)
    print("Experiment4 sweep complete")
    print("=" * 72)
    print(f"Run dir: {run_dir}")
    print(f"Best candidate: {best_candidate['candidate_id']}")
    print(
        f"Best {selection_cfg['primary_metric']}: "
        f"{best_candidate[selection_cfg['primary_metric']]:.6f}"
    )


if __name__ == "__main__":
    main()
