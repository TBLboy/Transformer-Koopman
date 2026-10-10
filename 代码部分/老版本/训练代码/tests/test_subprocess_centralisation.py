"""ALN-010 regression guard: one subprocess helper, shared by every pipeline.

The legacy tree carried a byte-identical "spawn a training script and stream its
output" block in five pipeline scripts, plus two more that used a plain
``subprocess.run``. They now all delegate to
``patchtst_koopman.utils.subprocess_runner``. These tests pin both the helper's
behaviour and the fact that no pipeline spawns a child process on its own.
"""
import re
import sys
from pathlib import Path

import pytest

from conftest import PROJECT_DIR

from patchtst_koopman.utils.subprocess_runner import run_capture, run_streaming

SCRIPTS_DIR = PROJECT_DIR / "scripts"

# The seven pipelines that used to own a private copy of the spawn block.
PIPELINES = [
    "run_all.py",
    "train_transformer.py",
    "train_platform1.py",
    "train_platform2.py",
    "train_lstm_platforms.py",
    "ablation/run_ablation_pipeline.py",
    "experiment4/run_experiment4_pipeline.py",
]

# Pipelines that stream output to a log file (the other two capture instead).
STREAMING_PIPELINES = PIPELINES[:5]
CAPTURE_PIPELINES = PIPELINES[5:]


def read_source(rel_path):
    """Read a script, tolerating a UTF-8 BOM (a legacy migration leftover)."""
    return (SCRIPTS_DIR / rel_path).read_text(encoding="utf-8-sig")


# --------------------------------------------------------------------------- #
# Behaviour of the shared helpers
# --------------------------------------------------------------------------- #

def test_run_streaming_propagates_returncode(tmp_path):
    log = tmp_path / "child.log"
    rc, elapsed = run_streaming(
        [sys.executable, "-c", "import sys; sys.exit(3)"],
        cwd=tmp_path,
        log_path=log,
        echo=False,
    )
    assert rc == 3
    assert elapsed >= 0.0


def test_run_streaming_writes_header_and_footer(tmp_path):
    log = tmp_path / "child.log"
    rc, _ = run_streaming(
        [sys.executable, "-c", "print('hello-from-child')"],
        cwd=tmp_path,
        log_path=log,
        echo=False,
    )
    assert rc == 0
    text = log.read_text(encoding="utf-8")
    assert "Command:" in text
    assert "Started:" in text
    assert "hello-from-child" in text
    assert "Exit code: 0" in text
    assert "Finished:" in text


def test_run_streaming_echo_toggle(tmp_path, capsys):
    cmd = [sys.executable, "-c", "print('visible-line')"]

    run_streaming(cmd, cwd=tmp_path, echo=False)
    assert "visible-line" not in capsys.readouterr().out

    run_streaming(cmd, cwd=tmp_path, echo=True)
    assert "visible-line" in capsys.readouterr().out


def test_run_streaming_without_log_file(tmp_path):
    rc, _ = run_streaming(
        [sys.executable, "-c", "print('no-log')"],
        cwd=tmp_path,
        log_path=None,
        echo=False,
    )
    assert rc == 0


def test_run_streaming_merges_stderr_into_log(tmp_path):
    log = tmp_path / "child.log"
    rc, _ = run_streaming(
        [sys.executable, "-c", "import sys; print('to-stderr', file=sys.stderr)"],
        cwd=tmp_path,
        log_path=log,
        echo=False,
    )
    assert rc == 0
    assert "to-stderr" in log.read_text(encoding="utf-8")


def test_run_capture_returns_completed_process(tmp_path):
    proc = run_capture(
        [sys.executable, "-c", "print('captured'); raise SystemExit(2)"],
        cwd=tmp_path,
    )
    assert proc.returncode == 2


def test_run_capture_uses_given_cwd(tmp_path):
    proc = run_capture(
        [sys.executable, "-c", "import os; print(os.getcwd())"],
        cwd=tmp_path,
    )
    assert proc.returncode == 0


# --------------------------------------------------------------------------- #
# No pipeline spawns a child process on its own
# --------------------------------------------------------------------------- #

def test_no_raw_subprocess_in_scripts():
    """``subprocess.Popen`` / ``subprocess.run`` must not appear under scripts/."""
    offenders = []
    for path in sorted(SCRIPTS_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8-sig")
        for lineno, line in enumerate(text.splitlines(), 1):
            if re.search(r"subprocess\.(Popen|run)\b", line):
                offenders.append(
                    f"{path.relative_to(SCRIPTS_DIR)}:{lineno}: {line.strip()}"
                )
    assert not offenders, (
        "raw subprocess usage found under scripts/; use "
        "patchtst_koopman.utils.subprocess_runner instead (ALN-010):\n  "
        + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("rel_path", STREAMING_PIPELINES)
def test_streaming_pipelines_use_shared_helper(rel_path):
    text = read_source(rel_path)
    assert "from patchtst_koopman.utils.subprocess_runner import run_streaming" in text
    assert "run_streaming(" in text


@pytest.mark.parametrize("rel_path", CAPTURE_PIPELINES)
def test_capture_pipelines_use_shared_helper(rel_path):
    text = read_source(rel_path)
    assert "from patchtst_koopman.utils.subprocess_runner import run_capture" in text
    assert "run_capture(" in text


@pytest.mark.parametrize("rel_path", PIPELINES)
def test_pipelines_do_not_import_subprocess_directly(rel_path):
    text = read_source(rel_path)
    assert not re.search(r"^\s*import subprocess\b", text, re.MULTILINE), (
        f"{rel_path} still imports subprocess directly"
    )
