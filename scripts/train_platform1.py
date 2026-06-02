"""
Train PatchTST-Koopman on Platform 1 (6-DOF Flexible Manipulator).

Usage:
    python scripts/train_platform1.py
"""

import subprocess
import sys
import os
import shutil
import time
from pathlib import Path
from datetime import datetime

# ============================================================
# 可调参数
# ============================================================

PYTHON_EXE = sys.executable

PROJECT_DIR = Path(__file__).resolve().parent.parent

RESULTS_DIR = PROJECT_DIR / "results"
LOGS_DIR = RESULTS_DIR / "logs"
SCRIPTS_DIR = PROJECT_DIR / "scripts"
CONFIGS_DIR = PROJECT_DIR / "configs"

JOB = {
    "name": "P1 PatchTST-Koopman",
    "config": "platform1.yaml",
    "models_dir": "platform1/Models/patchtst_koopman",
    "results_dir": "platform1/Results/patchtst_koopman",
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def main():

    print("=" * 60)
    print("  PatchTST-Koopman Training — Platform 1")
    print(f"  Project: {PROJECT_DIR}")
    print(f"  Python:  {PYTHON_EXE}")
    print(f"  Start:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    job = JOB
    script = SCRIPTS_DIR / "train_patchtst.py"
    config = CONFIGS_DIR / job["config"]
    models_abs = PROJECT_DIR / "results" / job["models_dir"]
    results_abs = PROJECT_DIR / "results" / job["results_dir"]
    log_abs = LOGS_DIR / "p1_patchtst_koopman.log"

    os.makedirs(models_abs, exist_ok=True)
    os.makedirs(results_abs, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    log(f"Starting: {job['name']}")
    log(f"  Config:     {config}")
    log(f"  Models →    {models_abs}")
    log(f"  Results →   {results_abs}")
    log(f"  Log →       {log_abs}")

    cmd = [
        PYTHON_EXE,
        str(script),
        "--config", str(config),
        "--save_dir", str(models_abs),
    ]

    t0 = time.time()
    log_file = open(log_abs, "w", encoding="utf-8")
    log_file.write(f"Command: {' '.join(cmd)}\n")
    log_file.write(f"Started: {datetime.now().isoformat()}\n")
    log_file.write("=" * 60 + "\n")

    proc = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for line in proc.stdout:
        print(line, end="", flush=True)
        log_file.write(line)

    proc.wait()

    log_file.write("\n" + "=" * 60 + "\n")
    log_file.write(f"Exit code: {proc.returncode}\n")
    log_file.write(f"Finished: {datetime.now().isoformat()}\n")
    log_file.close()

    elapsed = time.time() - t0
    success = proc.returncode == 0

    # ── 产物校验与结果同步 ──
    model_files = sorted(models_abs.glob("model_*.pth"))
    if model_files:
        log(f"  Model: {model_files[0].name}")
    else:
        log("  WARNING: no model file (model_*.pth) found")
        success = False

    plot_src = models_abs / "auto_test" / "test_prediction.png"
    if plot_src.exists():
        shutil.copy2(plot_src, results_abs / "test_prediction.png")
    else:
        log("  WARNING: test_prediction.png not found")

    for json_src in models_abs.glob("results_*.json"):
        shutil.copy2(json_src, results_abs / json_src.name)

    # ── 汇总 ──
    print()
    print("=" * 60)
    status = "PASS" if success else "FAIL"
    print(f"  Platform 1  {status}  ({elapsed:.0f}s)")
    print(f"  Overall:    {'ALL PASS' if success else 'FAILED'}")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
