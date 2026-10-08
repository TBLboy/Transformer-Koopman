"""ALN-014 guard: ASCII-only Python identifiers; Chinese dir names are accepted.

The legacy tree mixed Chinese directory/file names with the code and even used
non-ASCII identifiers, which is a cross-platform tooling hazard. The new project
keeps the Chinese *directory* names (DEC-008 / DEC-010 / DEC-014) but must not
introduce non-ASCII Python identifiers, and the accepted set of non-ASCII
top-level directories is pinned so a new one cannot appear silently.
"""
import io
import tokenize

from conftest import PROJECT_DIR, REPO_ROOT

SKIP_DIRS = {"__pycache__", ".pytest_cache", "results", ".git", ".mypy_cache"}

# The Chinese top-level directories the project deliberately keeps (DEC-014).
ACCEPTED_NON_ASCII_TOP_LEVEL = {"数据备份", "论文", "结果备份", "训练代码", "杂项"}


def iter_py_files():
    for path in sorted(PROJECT_DIR.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def test_no_non_ascii_python_identifiers():
    offenders = []
    for path in iter_py_files():
        text = path.read_text(encoding="utf-8")
        try:
            tokens = tokenize.generate_tokens(io.StringIO(text).readline)
            for tok in tokens:
                if tok.type == tokenize.NAME and any(ord(c) > 127 for c in tok.string):
                    offenders.append(
                        f"{path.relative_to(PROJECT_DIR)}:{tok.start[0]} {tok.string}"
                    )
        except (tokenize.TokenError, IndentationError):
            continue
    assert not offenders, (
        "non-ASCII Python identifiers found (ALN-014); use ASCII names:\n  "
        + "\n  ".join(offenders)
    )


def test_accepted_non_ascii_top_level_dirs_are_pinned():
    actual = {
        p.name for p in REPO_ROOT.iterdir()
        if p.is_dir() and any(ord(c) > 127 for c in p.name)
    }
    assert actual == ACCEPTED_NON_ASCII_TOP_LEVEL, (
        "the set of non-ASCII top-level directories changed; update DEC-014 and "
        f"this pin deliberately (actual={sorted(actual)})"
    )
