import hashlib
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman\deploy")
NEW = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\deploy")

if NEW.exists():
    print(f"target already exists: {NEW}")
    sys.exit(1)

mismatch = []
count = 0
for src in sorted(OLD.rglob("*")):
    if not src.is_file():
        continue
    rel = src.relative_to(OLD)
    dst = NEW / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    count += 1
    a = hashlib.sha256(src.read_bytes()).hexdigest()
    b = hashlib.sha256(dst.read_bytes()).hexdigest()
    if a != b:
        mismatch.append(str(rel))
    print(f"  {rel}  {'OK' if a == b else 'MISMATCH'}")

print(f"\ncopied {count} files; sha256 mismatches: {len(mismatch)}")
if mismatch:
    print("  " + "\n  ".join(mismatch))
    sys.exit(1)
print("byte-identical: True")
