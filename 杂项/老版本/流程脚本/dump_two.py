"""Show the encoded failure text for the two installer CLIs under a legacy console."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def legacy_env() -> dict:
    environment = {
        key: value for key, value in os.environ.items() if key.upper() != "PYTHONUTF8"
    }
    environment.pop("PYTHONIOENCODING", None)
    environment["PYTHONIOENCODING"] = "cp1252"
    return environment


def show(label: str, argv: list[str]) -> None:
    completed = subprocess.run(
        argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=legacy_env()
    )
    print(f"--- {label}: rc={completed.returncode}")
    print("stdout:", completed.stdout.decode("latin-1").strip()[:300])
    print("stderr:", completed.stderr.decode("latin-1").strip()[:400])


def main() -> int:
    repo = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory() as temporary:
        chinese = Path(temporary) / "工程记录"
        chinese.mkdir(parents=True)
        show(
            "global_installer",
            [
                sys.executable, str(repo / "scripts/global_installer.py"), "install",
                "--codex-home", str(chinese / "codex-home"),
                "--skip-preflight", "--without-mcp", "--without-hooks",
            ],
        )
        show(
            "opencode_installer",
            [
                sys.executable, str(repo / "scripts/opencode_installer.py"), "preflight",
                "--opencode-home", str(chinese / "opencode-home"),
            ],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
