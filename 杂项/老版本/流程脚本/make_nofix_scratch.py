"""Build a scratch copy of the repo with the UTF-8 guard reverted in two scripts.

Never modifies the real repository: it copies the working tree to a temp dir and
overwrites the two scripts with their committed (pre-fix) bytes using `git show`.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(r"D:\Project\vibe-coding\vibe-coding")
SCRATCH = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\repro-nofix")

REVERT = [
    "runtime/scripts/validate_project.py",
    "scripts/global_installer.py",
    "scripts/opencode_installer.py",
    "skills/a-project-init/scripts/init_project_agents.py",
    "skills/a-project-log-align/scripts/align.py",
    "skills/a-project-log-archive/scripts/archive.py",
    "runtime/hooks/post_tool_use.py",
    "runtime/hooks/pre_compact.py",
    "runtime/hooks/session_start.py",
]


def ignore(directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in {".git", "__pycache__", ".project-log"}}


def main() -> int:
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
    shutil.copytree(REPO, SCRATCH, ignore=ignore)
    for relative in REVERT:
        data = subprocess.check_output(
            ["git", "-C", str(REPO), "show", f"HEAD:{relative}"]
        )
        target = SCRATCH / relative
        target.write_bytes(data)
        print(f"reverted {relative} -> {len(data)} bytes (pre-fix)")
    print(f"scratch ready: {SCRATCH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
