"""
One-click training for the 2 PatchTST-Koopman models (Platform 1 & 2).

Results are saved under the same paths used by ``run_all.py`` so the two
scripts can be used interchangeably for the Transformer model family.

Usage:
    python scripts/train_transformer.py
"""

import subprocess
import sys
import os
import shutil
import time
from pathlib import Path
from datetime import datetime

# ============================================================
# 可调参数（修改此处即可）
# ============================================================

PYTHON_EXE = sys.executable

PROJECT_DIR = Path(__file__).resolve().parent.parent

RESULTS_DIR = PROJECT_DIR / "results"
LOGS_DIR = RESULTS_DIR / "logs"
SCRIPTS_DIR = PROJECT_DIR / "scripts"
CONFIGS_DIR = PROJECT_DIR / "configs"

# ============================================================
# 任务定义
# ============================================================

JOBS = [
    {
        "name": "P2 PatchTST-Koopman",
        "config": "platform2.yaml",
        "models_dir": "platform2/Models/patchtst_koopman",
        "results_dir": "platform2/Results/patchtst_koopman",
    },
    {
        "name": "P1 PatchTST-Koopman",
        "config": "platform1.yaml",
        "models_dir": "platform1/Models/patchtst_koopman",
        "results_dir": "platform1/Results/patchtst_koopman",
    },
]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def run_job(job, python_exe, project_dir):
    """Run a single training job and return (success, model_files)."""
    script = SCRIPTS_DIR / "train_patchtst.py"
    config = CONFIGS_DIR / job["config"]
    models_abs = project_dir / "results" / job["models_dir"]
    results_abs = project_dir / "results" / job["results_dir"]
    log_name = job["name"].replace(" ", "_").replace("-", "_").lower()
    log_abs = LOGS_DIR / f"{log_name}.log"

    os.makedirs(models_abs, exist_ok=True)
    os.makedirs(results_abs, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    log(f"Starting: {job['name']}")
    log(f"  Config:     {config}")
    log(f"  Models →    {models_abs}")
    log(f"  Results →   {results_abs}")
    log(f"  Log →       {log_abs}")

    cmd = [
        python_exe,
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
        cwd=str(project_dir),
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
    if not model_files:
        log("  WARNING: no model file (model_*.pth) found")
        success = False

    # Copy test_prediction.png (saved under Models/auto_test/)
    plot_src = models_abs / "auto_test" / "test_prediction.png"
    if plot_src.exists():
        shutil.copy2(plot_src, results_abs / "test_prediction.png")
    else:
        log("  WARNING: test_prediction.png not found")

    # Copy results_*.json
    for json_src in models_abs.glob("results_*.json"):
        shutil.copy2(json_src, results_abs / json_src.name)

    status = "PASS" if success else "FAIL"
    log(f"  {status} ({elapsed:.0f}s)")
    return success, model_files


def main():

    print("=" * 60)
    print("  PatchTST-Koopman Training (2 models)")
    print(f"  Project: {PROJECT_DIR}")
    print(f"  Python:  {PYTHON_EXE}")
    print(f"  Start:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    print(f"  {'Job':<35s}  Status")
    print(f"  {'─'*35}  ─────")

    results_log = []
    all_ok = True

    for idx, job in enumerate(JOBS, 1):
        print()
        ok, models = run_job(job, PYTHON_EXE, PROJECT_DIR)
        results_log.append((job["name"], ok, models))
        if not ok:
            all_ok = False

    # ── 汇总表 ──
    print()
    print("=" * 60)
    print("  Summary")
    print("=" * 60)
    print()
    print(f"  {'Job':<35s}  {'Status':<10s}  {'Model':<30s}")
    print(f"  {'─'*35}  {'─'*10}  {'─'*30}")
    for name, ok, models in results_log:
        status = "PASS" if ok else "FAIL"
        model_str = models[0].name if models else "—"
        print(f"  {name:<35s}  {status:<10s}  {model_str:<30s}")
    print()
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Overall:  {'ALL PASS' if all_ok else 'SOME JOBS FAILED'}")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
