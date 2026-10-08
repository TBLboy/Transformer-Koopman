import re
import sys
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PROJECT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码")
SRC = PROJECT / "src"
CFG = PROJECT / "configs"

text = "\n".join(p.read_text(encoding="utf-8") for p in sorted(SRC.rglob("*.py")))


def leaves(node, prefix=""):
    out = {}
    if isinstance(node, dict):
        for k, v in node.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, dict) and v:
                out.update(leaves(v, path))
            else:
                out[path] = k
    return out


for name in ("platform1.yaml", "platform2.yaml"):
    data = yaml.safe_load((CFG / name).read_text(encoding="utf-8"))
    lv = leaves(data)
    unread = sorted(p for p, tok in lv.items()
                    if not re.search(rf"""["']{re.escape(str(tok))}["']""", text))
    print(f"=== {name}: {len(lv)} leaves, {len(unread)} unread ===")
    for p in unread:
        print(f"   {p}")
    print()
