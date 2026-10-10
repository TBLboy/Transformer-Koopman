"""Exercise each Vibe entry-point script under a simulated legacy Windows console.

Usage: exercise_guards.py <repo-root>

Every child is started with ``PYTHONIOENCODING=cp1252`` and with ``PYTHONUTF8``
removed from its environment, so a non-ASCII ``print`` to a strict stream raises
``UnicodeEncodeError`` unless the script forces its own streams to UTF-8.

Each exercise drives the script's non-ASCII output path where one is reachable and
prints: exit status, whether stdout/stderr decode as UTF-8, whether non-ASCII bytes
appeared, and whether a ``UnicodeEncodeError`` surfaced.
"""
from __future__ import annotations

import json
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


def describe(data: bytes) -> str:
    latin = data.decode("latin-1")
    try:
        data.decode("utf-8")
        utf8 = "utf8-ok"
    except UnicodeDecodeError:
        utf8 = "utf8-BAD"
    return (
        f"{utf8} nonascii={not latin.isascii()} "
        f"crash={'UnicodeEncodeError' in latin} bytes={len(data)}"
    )


def run(label: str, argv: list[str], stdin: str | None = None) -> None:
    completed = subprocess.run(
        argv,
        input=None if stdin is None else stdin.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=legacy_env(),
    )
    print(f"[{label}] rc={completed.returncode} stdout: {describe(completed.stdout)}")
    print(f"[{label}] {' ' * len(str(completed.returncode))} stderr: {describe(completed.stderr)}")


def main() -> int:
    repo = Path(sys.argv[1]).resolve()
    python = sys.executable
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        chinese_dir = base / "工程记录"
        chinese_dir.mkdir(parents=True, exist_ok=True)
        chinese_file = base / "中文目标.txt"
        chinese_file.write_text("x\n", encoding="utf-8")

        run(
            "validate_project",
            [python, str(repo / "runtime/scripts/validate_project.py"), "--root", str(chinese_dir)],
        )
        run(
            "global_installer",
            [
                python, str(repo / "scripts/global_installer.py"), "install",
                "--codex-home", str(chinese_dir / "codex-home"),
                "--skip-preflight", "--without-mcp", "--without-hooks",
            ],
        )
        run(
            "opencode_installer",
            [
                python, str(repo / "scripts/opencode_installer.py"), "preflight",
                "--opencode-home", str(chinese_dir / "opencode-home"),
            ],
        )
        run(
            "init_project_agents",
            [
                python, str(repo / "skills/a-project-init/scripts/init_project_agents.py"),
                "--target", str(chinese_dir / "newproj"), "--dry-run", "--json",
            ],
        )

        # Hooks: stdout was already forced to UTF-8 by hook_common at import time; this
        # drives non-ASCII stdout through the caught-error context path so the stream is
        # still exercised under cp1252. stderr is not naturally reachable here.
        payload = json.dumps({"project_root": str(chinese_file)})
        for hook in ("post_tool_use", "pre_compact", "session_start"):
            run(
                f"hook:{hook}",
                [python, str(repo / "runtime/hooks" / f"{hook}.py")],
                stdin=payload,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
