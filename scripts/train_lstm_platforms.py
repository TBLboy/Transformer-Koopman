"""
Batch training script for LSTM-Koopman on both platforms.

Trains LSTM-Koopman on Platform 1 and Platform 2, saves models and results.

Usage:
    python scripts/train_lstm_platforms.py
"""

import subprocess
import sys
import os
import shutil
import time
from pathlib import Path
from datetime import datetime

# ============================================================
# Configuration
# ============================================================

PYTHON_EXE = sys.executable
PROJECT_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_DIR / "results"
LOGS_DIR = RESULTS_DIR / "logs"
SCRIPTS_DIR = PROJECT_DIR / "scripts"
CONFIGS_DIR = PROJECT_DIR / "configs"

# ============================================================
# Job Definitions
# ============================================================

JOBS = [
    {
        "name": "Platform 2 LSTM-Koopman",
        "script": "train_lstm_koopman.py",
        "config": "platform2.yaml",
        "models_dir": "platform2/Models/lstm_koopman",
        "results_dir": "platform2/Results/lstm_koopman",
    },
    {
        "name": "Platform 1 LSTM-Koopman",
        "script": "train_lstm_koopman.py",
        "config": "platform1.yaml",
        "models_dir": "platform1/Models/lstm_koopman",
        "results_dir": "platform1/Results/lstm_koopman",
    },
]

# ============================================================
# Helper Functions
# ============================================================

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def run_job(job, job_idx, total_jobs):
    """Run a single training job."""
    print_header(f"Job {job_idx}/{total_jobs}: {job['name']}")
    
    script_path = SCRIPTS_DIR / job["script"]
    config_path = CONFIGS_DIR / job["config"]
    models_dir = RESULTS_DIR / job["models_dir"]
    results_dir = RESULTS_DIR / job["results_dir"]
    
    # Create output directories
    models_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare command
    cmd = [
        str(PYTHON_EXE),
        str(script_path),
        "--config", str(config_path),
        "--save_dir", str(models_dir),
    ]
    
    # Setup log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"{job['name'].replace(' ', '_')}_{timestamp}.log"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Command: {' '.join(cmd)}")
    print(f"Log file: {log_file}")
    print(f"Models dir: {models_dir}")
    print(f"Results dir: {results_dir}")
    print()
    
    # Run training
    start_time = time.time()
    
    with open(log_file, "w", encoding="utf-8") as f:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        
        for line in process.stdout:
            print(line, end="")
            f.write(line)
            f.flush()
        
        process.wait()
    
    elapsed = time.time() - start_time
    
    if process.returncode == 0:
        print(f"\n✓ Job completed successfully in {elapsed/60:.1f} minutes")
        # Copy result files to results_dir
        for fname in ["results.json", "test_prediction.png"]:
            src = models_dir / fname
            dst = results_dir / fname
            if src.exists():
                shutil.copy2(src, dst)
                print(f"  Copied {fname} → {results_dir}")
        return True
    else:
        print(f"\n✗ Job failed with return code {process.returncode}")
        return False


def verify_outputs(job):
    """Verify that expected outputs exist."""
    models_dir = RESULTS_DIR / job["models_dir"]
    results_dir = RESULTS_DIR / job["results_dir"]

    model_file = models_dir / "model.pth"
    result_files = [results_dir / f for f in ["results.json", "test_prediction.png"]]

    all_ok = True
    if not model_file.exists():
        print(f"  ⚠ Missing model: {model_file}")
        all_ok = False
    for fpath in result_files:
        if not fpath.exists():
            print(f"  ⚠ Missing result: {fpath}")
            all_ok = False

    if all_ok:
        print(f"  ✓ Model in {models_dir}")
        print(f"  ✓ Results in {results_dir}")
    return all_ok


# ============================================================
# Main
# ============================================================

def main():
    print_header("LSTM-Koopman Batch Training")
    print(f"Python: {PYTHON_EXE}")
    print(f"Project: {PROJECT_DIR}")
    print(f"Results: {RESULTS_DIR}")
    print(f"Total jobs: {len(JOBS)}")
    
    start_time = time.time()
    results = []
    
    for idx, job in enumerate(JOBS, 1):
        success = run_job(job, idx, len(JOBS))
        results.append((job["name"], success))
        
        if success:
            verify_outputs(job)
    
    # Summary
    total_time = time.time() - start_time
    print_header("Training Summary")
    
    for name, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {status}: {name}")
    
    success_count = sum(1 for _, s in results if s)
    print(f"\nCompleted: {success_count}/{len(JOBS)} jobs")
    print(f"Total time: {total_time/60:.1f} minutes")
    
    if success_count == len(JOBS):
        print("\n🎉 All jobs completed successfully!")
        return 0
    else:
        print(f"\n⚠ {len(JOBS) - success_count} job(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
