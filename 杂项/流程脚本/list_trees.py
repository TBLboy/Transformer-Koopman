import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

NEW = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码")
OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman")


def tree(root, label, maxdepth=2):
    print(f"=== {label}: {root} ===")
    if not root.is_dir():
        print("  (missing)")
        return
    for p in sorted(root.iterdir()):
        if p.name in {".git", "__pycache__", ".pytest_cache", "results"}:
            continue
        if p.is_dir():
            n = sum(1 for _ in p.rglob("*") if _.is_file())
            print(f"  [dir ] {p.name}/  ({n} files)")
        else:
            print(f"  [file] {p.name}  ({p.stat().st_size} B)")
    print()


tree(NEW, "NEW 训练代码")
tree(OLD, "OLD repo root")

print("=== OLD top-level dirs not present in NEW ===")
new_names = {p.name for p in NEW.iterdir()}
for p in sorted(OLD.iterdir()):
    if p.name in {".git", "__pycache__", "results", "data"}:
        continue
    if p.name not in new_names:
        n = sum(1 for _ in p.rglob("*") if _.is_file()) if p.is_dir() else 1
        print(f"  {p.name}{'/' if p.is_dir() else ''}  ({n} files)")