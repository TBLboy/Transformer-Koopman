"""Demonstrate the guard is load-bearing for the newly added entry points.

This is a MECHANISM demonstration, not a historical replay: the real script runs
unchanged, but its stdout/stderr are replaced with a cp1252 stream whose
reconfigure() is a no-op — i.e. exactly the pre-fix situation where nothing pins
the encoding.
"""
import io
import runpy
import sys
from pathlib import Path

REPO = Path(r'D:\Project\vibe-coding\vibe-coding')


class LegacyNoReconfigure(io.TextIOWrapper):
    """A legacy-codepage stream that ignores reconfigure(), like the pre-fix CLI."""

    def reconfigure(self, *args, **kwargs):  # noqa: D102
        return None


def attempt(script_rel: str, argv: list[str]) -> str:
    sys.argv = [str(REPO / script_rel), *argv]
    sys.stdout = LegacyNoReconfigure(open(1, 'wb', closefd=False), encoding='cp1252', errors='strict')
    sys.stderr = LegacyNoReconfigure(open(2, 'wb', closefd=False), encoding='cp1252', errors='strict')
    try:
        runpy.run_path(str(REPO / script_rel), run_name='__main__')
    except SystemExit as exc:
        code = exc.code if exc.code is not None else 0
        return f'no crash (exit {code})'
    except UnicodeEncodeError as exc:
        return f'CRASHED: {type(exc).__name__}: {exc}'
    except Exception as exc:  # noqa: BLE001
        return f'other error: {type(exc).__name__}: {str(exc)[:90]}'
    return 'no crash (fell through)'


import tempfile  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    cjk = Path(tmp) / '工程记录测试'
    cjk.mkdir()
    cases = [
        ('runtime/scripts/init_project.py', ['--target', str(cjk), '--dry-run']),
        ('runtime/scripts/render_subagent_prompt.py',
         ['--role', 'business-analyst', '--project-root', str(cjk), '--task', '中文任务', '--scope', '只读']),
    ]
    for rel, argv in cases:
        outcome = attempt(rel, argv)
        print(f'{rel}\n    with reconfigure() disabled -> {outcome}')
