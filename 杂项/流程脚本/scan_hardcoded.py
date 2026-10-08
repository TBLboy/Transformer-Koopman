import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

CODE = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码")

PATTERNS = [
    ("windows-user-path", re.compile(r"[A-Za-z]:[\\/]Users[\\/]", re.I)),
    ("desktop", re.compile(r"Desktop", re.I)),
    ("old-project-name", re.compile(r"code-projectv2|论文4", re.I)),
    ("foreign-conda-env", re.compile(r"envs[\\/](koopman|project|FlexibleArm|matpython)\b", re.I)),
    ("absolute-drive-path", re.compile(r"(?<![\w.])[A-Za-z]:[\\/](?!\\)")),
]

SKIP_DIRS = {"__pycache__", ".pytest_cache", "results", ".git"}
EXTS = {".py", ".bat", ".ps1", ".yaml", ".yml", ".md", ".txt", ".cfg", ".toml", ".ini"}

hits = []
scanned = 0
for p in sorted(CODE.rglob("*")):
    if not p.is_file() or p.suffix.lower() not in EXTS:
        continue
    if any(part in SKIP_DIRS for part in p.parts):
        continue
    scanned += 1
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, rx in PATTERNS:
            if rx.search(line):
                hits.append((str(p.relative_to(CODE)), lineno, name, line.strip()[:110]))

print(f"scanned {scanned} files under {CODE.name}/")
print(f"hits: {len(hits)}")
for rel, lineno, name, line in hits:
    print(f"  [{name}] {rel}:{lineno}: {line}")