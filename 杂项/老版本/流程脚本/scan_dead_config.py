import re
import sys
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
CODE = ROOT / "训练代码"
CONFIGS = {"p1": CODE / "configs" / "platform1.yaml", "p2": CODE / "configs" / "platform2.yaml"}

SCAN_DIRS = [CODE / "src", CODE / "scripts", CODE / "deploy", CODE / "tests"]


def leaf_paths(node, prefix=""):
    out = {}
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict) and value:
                out.update(leaf_paths(value, path))
            else:
                out[path] = key
    return out


def source_text():
    parts = []
    for d in SCAN_DIRS:
        for p in sorted(d.rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


text = source_text()
for name, path in CONFIGS.items():
    leaves = leaf_paths(yaml.safe_load(path.read_text(encoding="utf-8")))
    dead = []
    for lpath, token in leaves.items():
        if not re.search(rf"""["']{re.escape(str(token))}["']""", text):
            dead.append(lpath)
    print(f"===== {name}: {len(dead)} dead leaves =====")
    for d in sorted(dead):
        print("  ", d)
