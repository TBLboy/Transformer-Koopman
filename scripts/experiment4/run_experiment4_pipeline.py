"""Run experiment4 training then test evaluation for one or both platforms."""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
EXPERIMENT4_DIR = PROJECT_DIR / "scripts" / "experiment4"
PYTHON = sys.executable


def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def run_command(cmd):
    log(" ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(PROJECT_DIR), text=True)
    return proc.returncode == 0


def run_training(platform, extra_args):
    cmd = [
        PYTHON,
        str(EXPERIMENT4_DIR / "train_experiment4.py"),
        "--platform",
        platform,
    ]
    cmd.extend(extra_args)
    return run_command(cmd)


def run_testing(platform, extra_args):
    cmd = [
        PYTHON,
        str(EXPERIMENT4_DIR / "test_experiment4.py"),
        "--platform",
        platform,
    ]
    cmd.extend(extra_args)
    return run_command(cmd)


def main():
    parser = argparse.ArgumentParser(description="Unified experiment4 pipeline")
    parser.add_argument("--skip-platform1", action="store_true")
    parser.add_argument("--skip-platform2", action="store_true")
    parser.add_argument("--train-only", action="store_true")
    parser.add_argument("--eval-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    train_args = []
    if args.dry_run:
        train_args.append("--dry-run")
    if args.limit is not None:
        train_args.extend(["--limit", str(args.limit)])

    platforms = []
    if not args.skip_platform1:
        platforms.append("platform1")
    if not args.skip_platform2:
        platforms.append("platform2")

    failed = []
    if not args.eval_only:
        for platform in platforms:
            log(f"Training {platform}")
            if not run_training(platform, train_args):
                failed.append(platform)

    if not args.train_only and not args.dry_run:
        for platform in platforms:
            if platform in failed:
                continue
            log(f"Testing {platform}")
            if not run_testing(platform, []):
                failed.append(platform)

    if failed:
        raise SystemExit(f"Experiment4 pipeline failed for: {sorted(set(failed))}")


if __name__ == "__main__":
    main()
