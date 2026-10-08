import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

CODE = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码")
PAT = re.compile(r"positional_encoding|PositionalEncoding")

print("=== all references to PositionalEncoding / positional_encoding ===")
for p in sorted(CODE.rglob("*.py")):
    if "__pycache__" in p.parts:
        continue
    for lineno, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if PAT.search(line):
            print(f"  {p.relative_to(CODE)}:{lineno}: {line.strip()}")

print()
print("=== class definitions of PositionalEncoding ===")
for p in sorted(CODE.rglob("*.py")):
    if "__pycache__" in p.parts:
        continue
    for lineno, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if re.match(r"\s*class\s+PositionalEncoding\b", line):
            print(f"  {p.relative_to(CODE)}:{lineno}")
