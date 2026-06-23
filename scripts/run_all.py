#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified one-click training pipeline: trains 8 models across 2 platforms.

Usage:
    python scripts/run_all.py           # run all 8 jobs
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

# Python 可执行文件路径
PYTHON_EXE = sys.executable

# 项目根目录（自动检测）
PROJECT_DIR = Path(__file__).resolve().parent.parent

# 结果根目录
RESULTS_DIR = PROJECT_DIR / "results"

# 日志根目录
LOGS_DIR = RESULTS_DIR / "logs"

# 训练脚本目录
SCRIPTS_DIR = PROJECT_DIR / "scripts"

# 配置文件目录
CONFIGS_DIR = PROJECT_DIR / "configs"

# ============================================================
# 任务定义
# ============================================================

JOBS = [
    # ── Platform 2 (2-DOF Soft Robotic Arm) ──
    {
        "name": "P2 PatchTST-Koopman",
        "script": "train_patchtst.py",
        "config": "platform2.yaml",
        "models_dir": "platform2/Models/patchtst_koopman",
        "results_dir": "platform2/Results/patchtst_koopman",
    },
    {
        "name": "P2 MLP-Koopman",
        "script": "train_mlp_koopman.py",
        "config": "platform2.yaml",
        "models_dir": "platform2/Models/mlp_koopman",
        "results_dir": "platform2/Results/mlp_koopman",
    },
    {
        "name": "P2 LSTM-Koopman",
        "script": "train_lstm_koopman.py",
        "config": "platform2.yaml",
        "models_dir": "platform2/Models/lstm_koopman",
        "results_dir": "platform2/Results/lstm_koopman",
    },
    {
        "name": "P2 Traditional EDMD",
        "script": "train_traditional_edmd.py",
        "config": "platform2.yaml",
        "models_dir": "platform2/Models/traditional_edmd",
        "results_dir": "platform2/Results/traditional_edmd",
    },
    # ── Platform 1 (6-DOF Flexible Manipulator) ──
    {
        "name": "P1 PatchTST-Koopman",
        "script": "train_patchtst.py",
        "config": "platform1.yaml",
        "models_dir": "platform1/Models/patchtst_koopman",
        "results_dir": "platform1/Results/patchtst_koopman",
    },
    {
        "name": "P1 MLP-Koopman",
        "script": "train_mlp_koopman.py",
        "config": "platform1.yaml",
        "models_dir": "platform1/Models/mlp_koopman",
        "results_dir": "platform1/Results/mlp_koopman",
    },
    {
        "name": "P1 LSTM-Koopman",
        "script": "train_lstm_koopman.py",
        "config": "platform1.yaml",
        "models_dir": "platform1/Models/lstm_koopman",
        "results_dir": "platform1/Results/lstm_koopman",
    },
    {
        "name": "P1 Traditional EDMD",
        "script": "train_traditional_edmd.py",
        "config": "platform1.yaml",
        "models_dir": "platform1/Models/traditional_edmd",
        "results_dir": "platform1/Results/traditional_edmd",
    },
]

# ============================================================
# 校验规则：(模型文件 glob pattern, 结果文件列表)
# ============================================================

VERIFY_RULES = {
    "patchtst_koopman": {
        "model_patterns": ["model_*.pth"],
        "result_files": ["test_prediction.png"],
        "result_json_pattern": "results_*.json",
    },
    "mlp_koopman": {
        "model_patterns": ["model.pth"],
        "result_files": ["results.json", "test_prediction.png"],
        "result_json_pattern": None,
    },
    "lstm_koopman": {
        "model_patterns": ["model.pth"],
        "result_files": ["results.json", "test_prediction.png"],
        "result_json_pattern": None,
    },
    "traditional_edmd": {
        "model_patterns": ["A_matrix.npy", "lifting_meta.npz"],
        "result_files": ["results.npy", "test_prediction.png"],
        "result_json_pattern": None,
    },
}


def get_model_type(job):
    return job["models_dir"].split("/")[-1]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def run_job(job, python_exe, project_dir):
    """Run a single training job and return (success, model_files, result_files)."""
    script = SCRIPTS_DIR / job["script"]
    config = CONFIGS_DIR / job["config"]
    models_abs = project_dir / "results" / job["models_dir"]
    results_abs = project_dir / "results" / job["results_dir"]
    log_name = job['name'].replace(' ', '_').replace('-', '_').lower()
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

    # ── 产物校验 ──
    model_type = get_model_type(job)
    rules = VERIFY_RULES[model_type]

    model_files = []
    for pattern in rules["model_patterns"]:
        matches = list(models_abs.glob(pattern))
        model_files.extend(matches)
        if not matches:
            log(f"  WARNING: no model files matching '{pattern}' found")
            success = False

    result_files = []
    for fname in rules["result_files"]:
        fpath = results_abs / fname
        # Result may have been saved to models_dir; copy if not yet in results_dir
        src = models_abs / fname
        if src.exists() and not fpath.exists():
            shutil.copy2(src, fpath)
        if fpath.exists():
            result_files.append(fpath)
        else:
            # Also check common nested paths
            alt_src = models_abs / "auto_test" / fname
            if alt_src.exists():
                os.makedirs(results_abs, exist_ok=True)
                shutil.copy2(alt_src, fpath)
                result_files.append(fpath)
            else:
                log(f"  WARNING: result file '{fname}' not found")
                success = False

    # Copy result json if applicable
    if rules["result_json_pattern"]:
        for json_src in models_abs.glob(rules["result_json_pattern"]):
            dst = results_abs / json_src.name
            shutil.copy2(json_src, dst)
            result_files.append(dst)

    status = "PASS" if success else "FAIL"
    log(f"  {status} ({elapsed:.0f}s)")
    return success, model_files, result_files


def main():

    print("=" * 60)
    print("  Unified Training Pipeline")
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
        ok, models, results_files = run_job(job, PYTHON_EXE, PROJECT_DIR)
        results_log.append((job["name"], ok, models, results_files))
        if not ok:
            all_ok = False

    # ── 汇总表 ──
    print()
    print("=" * 60)
    print("  Summary")
    print("=" * 60)
    print()
    print(f"  {'Job':<35s}  {'Status':<10s}  {'Model':<30s}  {'Results':<30s}")
    print(f"  {'─'*35}  {'─'*10}  {'─'*30}  {'─'*30}")
    for name, ok, models, results_files in results_log:
        status = "PASS" if ok else "FAIL"
        model_str = models[0].name if models else "—"
        result_str = results_files[0].name if results_files else "—"
        print(f"  {name:<35s}  {status:<10s}  {model_str:<30s}  {result_str:<30s}")
    print()
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Overall:  {'ALL PASS' if all_ok else 'SOME JOBS FAILED'}")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
