from pathlib import Path

repo = Path(r"D:\Project\vibe-coding\vibe-coding")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache", ".pytest_cache"}
CRLF = b"\r\n"

changed = 0
skipped_binary = 0
scanned = 0
for path in repo.rglob("*"):
    if path.is_dir():
        continue
    parts = set(path.relative_to(repo).parts[:-1])
    if parts & SKIP_DIRS:
        continue
    scanned += 1
    data = path.read_bytes()
    if b"\x00" in data[:8192]:
        skipped_binary += 1
        continue
    if CRLF in data:
        path.write_bytes(data.replace(CRLF, b"\n"))
        changed += 1

print("scanned:", scanned, "normalized:", changed, "binary skipped:", skipped_binary)

remaining = 0
for path in repo.rglob("*"):
    if path.is_dir():
        continue
    parts = set(path.relative_to(repo).parts[:-1])
    if parts & SKIP_DIRS:
        continue
    data = path.read_bytes()
    if b"\x00" in data[:8192]:
        continue
    if CRLF in data:
        remaining += 1
print("remaining CRLF (text):", remaining)
