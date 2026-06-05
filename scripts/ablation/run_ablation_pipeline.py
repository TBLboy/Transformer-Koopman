"""Unified ablation pipeline: train + evaluate all variants for both platforms.

Usage:
    python scripts/ablation/run_ablation_pipeline.py
    python scripts/ablation/run_ablation_pipeline.py --skip-platform1
    python scripts/ablation/run_ablation_pipeline.py --train-only
    python scripts/ablation/run_ablation_pipeline.py --eval-only

Pipeline flow:
    1. Train all ablation variants for platform1
    2. Train all ablation variants for platform2
    3. Evaluate platform1 ablation results
    4. Evaluate platform2 ablation results
"""
import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
ABLATION_SCRIPTS = PROJECT_DIR / "scripts" / "ablation"
PYTHON = sys.executable


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def find_latest_results_dir(platform: str, results_root: str):
    """Find the latest timestamped ablation results directory."""
    base = Path(results_root) / f"ablation_{platform}"
    if not base.exists():
        return None
    dirs = sorted([d for d in base.iterdir() if d.is_dir()], reverse=True)
    return str(dirs[0]) if dirs else None


def run_training(platform: str) -> bool:
    """Run ablation training for a platform. Returns True on success."""
    config = ABLATION_SCRIPTS / f"ablation_{platform}.yaml"
    cmd = [
        PYTHON,
        str(ABLATION_SCRIPTS / "train_ablation.py"),
        "--platform", platform,
        "--variants", "all",
        "--config", str(config),
    ]
    log(f"Training {platform}...")
    log(f"  Command: {' '.join(cmd)}")

    proc = subprocess.run(cmd, cwd=str(PROJECT_DIR), text=True)
    if proc.returncode != 0:
        log(f"  FAILED (exit code {proc.returncode})")
        return False
    log("  PASSED")
    return True


def run_testing(platform: str, results_dir: str) -> bool:
    """Run evaluation on trained ablation results. Returns True on success."""
    config = ABLATION_SCRIPTS / f"ablation_{platform}.yaml"
    cmd = [
        PYTHON,
        str(ABLATION_SCRIPTS / "test_ablation.py"),
        "--platform", platform,
        "--config", str(config),
        "--results_dir", results_dir,
    ]
    log(f"Testing {platform}...")
    log(f"  Command: {' '.join(cmd)}")

    proc = subprocess.run(cmd, cwd=str(PROJECT_DIR), text=True)
    if proc.returncode != 0:
        log(f"  FAILED (exit code {proc.returncode})")
        return False
    log("  PASSED")
    return True


def main():
    parser = argparse.ArgumentParser(description="Unified ablation pipeline")
    parser.add_argument("--skip-platform1", action="store_true", help="Skip platform1")
    parser.add_argument("--skip-platform2", action="store_true", help="Skip platform2")
    parser.add_argument("--train-only", action="store_true", help="Only train, skip evaluation")
    parser.add_argument("--eval-only", action="store_true", help="Only evaluate, skip training")
    args = parser.parse_args()

    print("=" * 70)
    print("  Unified Ablation Pipeline")
    print(f"  Project: {PROJECT_DIR}")
    print(f"  Start:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    platforms_to_run = []
    if not args.skip_platform1:
        platforms_to_run.append("platform1")
    if not args.skip_platform2:
        platforms_to_run.append("platform2")

    results_dirs = {}
    failed_platforms = []

    if not args.eval_only:
        print()
        print("=" * 70)
        print("  Phase 1: Training")
        print("=" * 70)

        for platform in platforms_to_run:
            print()
            ok = run_training(platform)
            if not ok:
                failed_platforms.append(platform)
                log(f"  Skipping evaluation for {platform} due to training failure")
                continue

            results_root = str(PROJECT_DIR / "results" / "ablation" / platform)
            results_dir = find_latest_results_dir(platform, results_root)
            if results_dir:
                results_dirs[platform] = results_dir
                log(f"  Results saved to: {results_dir}")
            else:
                failed_platforms.append(platform)
                log(f"  FAILED: could not find results directory for {platform}")

    if not args.train_only:
        print()
        print("=" * 70)
        print("  Phase 2: Evaluation")
        print("=" * 70)

        if args.eval_only:
            for platform in platforms_to_run:
                results_root = str(PROJECT_DIR / "results" / "ablation" / platform)
                results_dir = find_latest_results_dir(platform, results_root)
                if results_dir:
                    results_dirs[platform] = results_dir
                else:
                    failed_platforms.append(platform)
                    log(f"No results found for {platform} in eval-only mode")

        for platform in platforms_to_run:
            if platform not in results_dirs:
                failed_platforms.append(platform)
                log(f"No results found for {platform}, skipping evaluation")
                continue
            print()
            ok = run_testing(platform, results_dirs[platform])
            if not ok:
                failed_platforms.append(platform)

    print()
    print("=" * 70)
    print(f"  Pipeline complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if results_dirs:
        print()
        print("Results directories:")
        for platform, d in results_dirs.items():
            print(f"  {platform}: {d}")

    if failed_platforms:
        print()
        print("Failed platforms:")
        for platform in sorted(set(failed_platforms)):
            print(f"  {platform}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
