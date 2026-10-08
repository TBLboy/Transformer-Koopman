import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

CP2 = Path(r"D:\Project\code-projectv2")
OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman")
NEW = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码")


def tree_hash(root, sub):
    base = root / sub
    if not base.is_dir():
        return None, 0
    h = hashlib.sha256()
    n = 0
    for p in sorted(base.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        h.update(str(p.relative_to(base)).encode())
        h.update(p.read_bytes())
        n += 1
    return h.hexdigest()[:16], n


print("=== git state ===")
for label, root in (("code-projectv2", CP2), ("论文3老版本", OLD), ("NEW 训练代码", NEW)):
    r = subprocess.run(["git", "-C", str(root), "log", "--oneline", "-3"],
                       capture_output=True)
    out = (r.stdout + r.stderr).decode("utf-8", "replace").strip()
    b = subprocess.run(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
                       capture_output=True)
    br = (b.stdout + b.stderr).decode("utf-8", "replace").strip()
    print(f"  {label}: branch={br}")
    for line in out.splitlines()[:3]:
        print(f"      {line}")

print("\n=== .project-log project_id ===")
for label, root in (("code-projectv2", CP2), ("论文3老版本", OLD), ("NEW", Path(r"D:\Project\Transformer-Koopman"))):
    pl = root / ".project-log"
    if not pl.is_dir():
        print(f"  {label}: no .project-log")
        continue
    found = None
    for f in pl.rglob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict) and "project_id" in d:
            found = (f.name, d["project_id"])
            break
    print(f"  {label}: {found}")

print("\n=== src/patchtst_koopman tree hash (py files) ===")
for label, root in (("code-projectv2", CP2), ("论文3老版本", OLD), ("NEW 训练代码", NEW)):
    h, n = tree_hash(root, "src/patchtst_koopman")
    print(f"  {label}: hash={h} files={n}")

print("\n=== top-level comparison ===")
for label, root in (("code-projectv2", CP2), ("论文3老版本", OLD)):
    names = sorted(p.name for p in root.iterdir() if p.name not in {".git", "__pycache__"})
    print(f"  {label}: {names}")
