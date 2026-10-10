"""Shared subprocess helpers for the training pipelines (ALN-010).

Five pipeline scripts (``run_all.py``, ``train_transformer.py``,
``train_platform1.py``, ``train_platform2.py``, ``train_lstm_platforms.py``)
carried a byte-identical copy of the "spawn a training script, stream its output
to the console and a log file" block; two more
(``run_ablation_pipeline.py``, ``run_experiment4_pipeline.py``) used a plain
``subprocess.run``. They now all call the helpers below.
"""
import subprocess
import time
from datetime import datetime


def run_streaming(cmd, cwd, log_path=None, echo=True):
    """Run ``cmd``, streaming stdout+stderr to the console and optionally a log.

    Parameters
    ----------
    cmd : sequence of str
        Command and arguments.
    cwd : str or Path
        Working directory for the child process.
    log_path : str or Path or None
        When given, the streamed output plus a header/footer is written here.
    echo : bool
        Whether to echo the child's output to this process's stdout.

    Returns
    -------
    (returncode, elapsed_seconds) : tuple[int, float]
    """
    cmd = [str(part) for part in cmd]
    t0 = time.time()

    log_file = None
    if log_path is not None:
        log_file = open(log_path, "w", encoding="utf-8")
        log_file.write(f"Command: {' '.join(cmd)}\n")
        log_file.write(f"Started: {datetime.now().isoformat()}\n")
        log_file.write("=" * 60 + "\n")

    returncode = None
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        for line in proc.stdout:
            if echo:
                print(line, end="", flush=True)
            if log_file is not None:
                log_file.write(line)

        proc.wait()
        returncode = proc.returncode
    finally:
        if log_file is not None:
            log_file.write("\n" + "=" * 60 + "\n")
            log_file.write(f"Exit code: {returncode}\n")
            log_file.write(f"Finished: {datetime.now().isoformat()}\n")
            log_file.close()

    return returncode, time.time() - t0


def run_capture(cmd, cwd):
    """Run ``cmd`` to completion, inheriting this process's stdio.

    Returns the :class:`subprocess.CompletedProcess`.
    """
    cmd = [str(part) for part in cmd]
    return subprocess.run(cmd, cwd=str(cwd), text=True)
