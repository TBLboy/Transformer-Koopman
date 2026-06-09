"""Evaluate experiment4 sweep outputs on the test split."""

import argparse
import json
import os

from common import find_latest_results_dir, write_json
from patchtst_koopman.utils.checkpoint import load_model
from patchtst_koopman.utils.data_prep import prepare_datasets
from patchtst_koopman.utils.device import resolve_device
from patchtst_koopman.utils.evaluation import evaluate_on_first_trajectory


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate experiment4 results")
    parser.add_argument("--platform", type=str, default="platform1", choices=["platform1", "platform2"])
    parser.add_argument("--results_dir", type=str, default=None)
    parser.add_argument("--results_root", type=str, default="./results/experiment4")
    parser.add_argument("--device", type=str, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    results_dir = args.results_dir or find_latest_results_dir(os.path.join(args.results_root, args.platform))
    scan_results_path = os.path.join(results_dir, "scan_results.json")
    if not os.path.exists(scan_results_path):
        raise FileNotFoundError(f"Missing scan_results.json in {results_dir}")

    with open(scan_results_path, "r", encoding="utf-8") as handle:
        scan_results = json.load(handle)

    evaluated = {}
    for result in scan_results["results"]:
        if result.get("status") != "success":
            continue
        device = resolve_device(args.device or result["config"].get("device", "cuda"))
        model_path = result["final_model_path"]
        model, config, checkpoint = load_model(model_path, device=device)
        config["experiment"]["device"] = device
        _, _, test_dataset, norm_stats = prepare_datasets(config)
        rollout = evaluate_on_first_trajectory(
            model,
            test_dataset,
            config,
            checkpoint.get("normalization", norm_stats),
        )
        evaluated[result["candidate_id"]] = {
            "rmse": float(rollout["rmse"]),
            "mae": float(rollout["mae"]),
            "final_model_path": model_path,
            "best_model_path": result.get("best_model_path"),
        }

    write_json(
        os.path.join(results_dir, "test_results.json"),
        {
            "platform": args.platform,
            "results_dir": results_dir,
            "test_metrics": evaluated,
        },
    )
    print(f"Saved test results to {os.path.join(results_dir, 'test_results.json')}")


if __name__ == "__main__":
    main()
