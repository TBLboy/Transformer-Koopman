"""FIX-04 regression guard: the migrated code must not contain machine-specific paths.

The legacy tree hard-coded ``C:\\Users\\Windows\\Desktop\\论文4\\code-projectv2`` in
launcher scripts and debug helpers, which made the project unrunnable anywhere else.
This test fails if such a path (or the old project name / a foreign conda env) is
reintroduced.
"""
import re
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

# Directories that are generated or not part of the source tree.
SKIP_DIRS = {"__pycache__", ".pytest_cache", "results", ".git", ".mypy_cache"}
SCAN_EXTS = {".py", ".bat", ".ps1", ".yaml", ".yml", ".md", ".txt", ".cfg", ".toml", ".ini"}

# Generated provenance records. These deliberately preserve the absolute path the
# asset was exported from as a historical record; rewriting them would falsify
# provenance. They are the ONLY permitted exception (see ALN-006 / DEC-011), and
# test_provenance_allowlist_is_exactly_as_expected pins the set so it cannot grow
# silently.
PROVENANCE_ALLOWLIST = {
    Path("deploy/algorithms/tk_assets/model_assets/platform2_metadata.json"),
}

PATTERNS = {
    # C:\Users\... / C:/Users/...
    "windows-user-path": re.compile(r"[A-Za-z]:[\\/]Users[\\/]", re.I),
    # the old author's desktop
    "desktop": re.compile(r"Desktop", re.I),
    # the legacy project name
    "old-project-name": re.compile(r"code-projectv2|code_projectv2|论文4", re.I),
    # a conda env that does not exist on this machine
    "foreign-conda-env": re.compile(
        r"envs[\\/](koopman|project|FlexibleArm|matpython)\b", re.I),
    # any absolute drive path; the lookahead skips escape sequences (\n, \t, ...)
    # and URL separators (https://) so only real paths are flagged
    "absolute-drive-path": re.compile(r"(?<![\w.])[A-Za-z]:[\\/](?![nrtbfv0\\/])"),
}


def iter_source_files():
    for path in sorted(PROJECT_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SCAN_EXTS:
            continue
        if path.resolve() == SELF:
            continue  # the scanner itself necessarily contains the patterns
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.relative_to(PROJECT_DIR) in PROVENANCE_ALLOWLIST:
            continue
        yield path


def test_provenance_allowlist_is_exactly_as_expected():
    """The exception must stay minimal and must actually exist on disk."""
    assert PROVENANCE_ALLOWLIST == {
        Path("deploy/algorithms/tk_assets/model_assets/platform2_metadata.json")
    }, "the provenance allowlist changed; justify it in ALN-006 / DEC-011 first"
    for rel in PROVENANCE_ALLOWLIST:
        assert (PROJECT_DIR / rel).is_file(), f"allowlisted file missing: {rel}"


def test_patterns_detect_planted_paths():
    """Guard against a silently broken regex making the scan vacuous."""
    samples = {
        "windows-user-path": r"set PROJECT=C:\Users\Windows\Desktop\x",
        "desktop": "cd /home/user/Desktop/proj",
        "old-project-name": "cd code-projectv2",
        "foreign-conda-env": r"C:\Users\x\.conda\envs\koopman\python.exe",
        "absolute-drive-path": r'PATH = r"D:\conda\envs\edmddl2\python.exe"',
    }
    for name, text in samples.items():
        assert PATTERNS[name].search(text), f"pattern {name!r} failed to match {text!r}"


def test_patterns_ignore_benign_text():
    """No false positives on escape sequences, URLs or relative paths."""
    benign = [
        r'cfg.write_text("a:\n  b: 1\n", encoding="utf-8")',
        "https://github.com/example/repo",
        "configs/platform2.yaml",
        "scripts/train_patchtst.py",
        "results/models/model_20260527.pth",
    ]
    for text in benign:
        for name, rx in PATTERNS.items():
            assert not rx.search(text), f"pattern {name!r} false-positived on {text!r}"


def test_no_hardcoded_machine_paths_in_source():
    hits = []
    for path in iter_source_files():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:  # pragma: no cover - unreadable file
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, rx in PATTERNS.items():
                if rx.search(line):
                    hits.append(
                        f"{path.relative_to(PROJECT_DIR)}:{lineno} [{name}] {line.strip()[:100]}"
                    )
    assert not hits, (
        "machine-specific paths found in the migrated source (FIX-04 regression):\n  "
        + "\n  ".join(hits)
    )
