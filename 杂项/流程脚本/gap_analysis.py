import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman")
NEW = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码")

# code-bearing paths that 阶段① is supposed to carry over
CODE_DIRS = ["src", "scripts", "configs", "deploy"]
CODE_FILES = ["pyproject.toml", "requirements.txt", "run_all_training.bat",
              "run_all_training.ps1", "README.md", ".gitignore"]
SKIP = {"__pycache__", ".pytest_cache", "results", ".git"}


def collect(root):
    out = {}
    for d in CODE_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.is_file() and not any(s in p.parts for s in SKIP):
                out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    for f in CODE_FILES:
        p = root / f
        if p.is_file():
            out[f] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


old = collect(OLD)
new = collect(NEW)

missing = sorted(set(old) - set(new))
extra = sorted(set(new) - set(old))
differ = sorted(k for k in set(old) & set(new) if old[k] != new[k])

print(f"old files: {len(old)}   new files: {len(new)}")
print(f"\n=== MISSING in new repo ({len(missing)}) ===")
for k in missing:
    print(f"  {k}")
print(f"\n=== EXTRA in new repo ({len(extra)}) ===")
for k in extra:
    print(f"  {k}")
print(f"\n=== CONTENT DIFFERS ({len(differ)}) ===")
for k in differ:
    print(f"  {k}")
