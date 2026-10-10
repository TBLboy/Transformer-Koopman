import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman")
SKIP_DIRS = {".git", "data", "results", "figures", "__pycache__", ".ipynb_checkpoints",
             "论文草稿", ".venv", "venv", "weights", "checkpoints"}
SKIP_EXT = {".tex", ".pdf", ".ps", ".eps", ".bib", ".bst", ".cls", ".mat", ".npz", ".pth",
            ".pt", ".ckpt", ".png", ".jpg", ".log", ".txt", ".pyc"}

print("=== OLD REPO top level ===")
for p in sorted(OLD.iterdir()):
    if p.name in SKIP_DIRS:
        print(f"  [skip] {p.name}/")
        continue
    kind = "D" if p.is_dir() else "F"
    print(f"  {kind} {p.name}" + ("" if p.is_dir() else f"  ({p.stat().st_size} B)"))

print("\n=== OLD REPO: src/patchtst_koopman tree (code only) ===")
src = OLD / "src"
if src.exists():
    for p in sorted(src.rglob("*")):
        if not p.is_file() or p.suffix in SKIP_EXT:
            continue
        if "__pycache__" in p.parts:
            continue
        rel = p.relative_to(OLD)
        print(f"  {p.stat().st_size:>7} B  {rel}")
else:
    print("  src/ MISSING")

print("\n=== OLD REPO: configs/ ===")
for p in sorted((OLD / "configs").rglob("*")) if (OLD / "configs").exists() else []:
    if p.is_file():
        print(f"  {p.stat().st_size:>7} B  {p.relative_to(OLD)}")

print("\n=== OLD REPO: scripts/ ===")
for p in sorted((OLD / "scripts").rglob("*")) if (OLD / "scripts").exists() else []:
    if p.is_file() and p.suffix not in SKIP_EXT:
        print(f"  {p.stat().st_size:>7} B  {p.relative_to(OLD)}")

print("\n=== OLD REPO: packaging / test files ===")
for name in ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "pytest.ini",
             "tox.ini", "conftest.py", "README.md", "run_all.py", "run_all_training.bat",
             "run_all_training.ps1", ".gitignore"):
    p = OLD / name
    if p.exists():
        print(f"  F {p.stat().st_size:>7} B  {name}")
