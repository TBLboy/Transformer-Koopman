from pathlib import Path

log = Path(r"D:\Project\vibe-coding\.project-log")

attributes = (
    "# The Project Log is authoritative: the ledger is archived byte-for-byte, so Git\n"
    "# must never apply end-of-line or clean/smudge conversion to it. One byte form on\n"
    "# every platform keeps an Ubuntu and a Windows checkout identical.\n"
    "* -text\n"
)
(log / ".gitattributes").write_text(attributes, encoding="utf-8", newline="\n")

changed = 0
skipped_binary = 0
for path in log.rglob("*"):
    if path.is_dir():
        continue
    rel = path.relative_to(log).as_posix()
    if rel.startswith(".state/") or "__pycache__" in rel:
        continue
    data = path.read_bytes()
    if b"\x00" in data[:4096]:
        skipped_binary += 1
        continue
    if b"\r\n" in data:
        path.write_bytes(data.replace(b"\r\n", b"\n"))
        changed += 1

# report remaining CRLF among the files we would archive
remaining = 0
for path in log.rglob("*"):
    if path.is_dir():
        continue
    rel = path.relative_to(log).as_posix()
    if rel.startswith(".state/") or "__pycache__" in rel:
        continue
    data = path.read_bytes()
    if b"\x00" in data[:4096]:
        continue
    if b"\r\n" in data:
        remaining += 1

print("normalized:", changed, "binary skipped:", skipped_binary, "remaining CRLF:", remaining)
print("ledger CRLF:", open(log / "ledger/v1/ledger.jsonl", "rb").read().count(b"\r\n"))
