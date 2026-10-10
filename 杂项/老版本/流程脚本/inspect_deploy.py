import hashlib
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman\deploy")

PATTERNS = {
    "windows-user-path": re.compile(r"[A-Za-z]:[\\/]Users[\\/]", re.I),
    "desktop": re.compile(r"Desktop", re.I),
    "old-project-name": re.compile(r"code-projectv2|code_projectv2|论文4", re.I),
    "foreign-conda-env": re.compile(r"envs[\\/](koopman|project|FlexibleArm|matpython)\b", re.I),
    "absolute-drive-path": re.compile(r"(?<![\w.])[A-Za-z]:[\\/](?![nrtbfv0\\/])"),
    "flexiblearm-ref": re.compile(r"FlexibleArmControl34", re.I),
}

print(f"=== deploy/ tree ({OLD}) ===")
total = 0
for p in sorted(OLD.rglob("*")):
    if p.is_file():
        total += 1
        rel = p.relative_to(OLD)
        print(f"  {rel}  ({p.stat().st_size} B)  sha256={hashlib.sha256(p.read_bytes()).hexdigest()[:16]}")
print(f"  total files: {total}")

print("\n=== hardcoded-path scan of deploy/ ===")
hits = 0
for p in sorted(OLD.rglob("*")):
    if not p.is_file():
        continue
    if p.suffix.lower() not in {".py", ".md", ".json", ".yaml", ".yml", ".txt", ".cfg", ".toml", ".bat", ".ps1"}:
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, rx in PATTERNS.items():
            if rx.search(line):
                hits += 1
                print(f"  [{name}] {p.relative_to(OLD)}:{lineno}: {line.strip()[:120]}")
print(f"  hits: {hits}")