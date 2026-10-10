#!/usr/bin/env python3
"""Read-only: prove byte-identical archive of the 14 legacy files vs git HEAD."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

NESTED = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
LEGACY = Path(r"D:\Project\Transformer-Koopman\.project-log\legacy")


def tracked() -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(NESTED), "ls-files", ".project-log"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def head_bytes(rel: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(NESTED), "show", f"HEAD:{rel}"],
        capture_output=True, check=True,
    ).stdout


rows = []
for rel in tracked():
    target = LEGACY / rel[len(".project-log/"):]
    original = head_bytes(rel)
    archived = target.read_bytes() if target.is_file() else None
    rows.append({
        "path": rel,
        "head_sha256": hashlib.sha256(original).hexdigest(),
        "archive_sha256": hashlib.sha256(archived).hexdigest() if archived is not None else None,
        "byte_equal": archived == original,
    })

extra = sorted(
    p.relative_to(LEGACY).as_posix()
    for p in LEGACY.rglob("*")
    if p.is_file() and p.name != "PROVENANCE.md"
    and p.relative_to(LEGACY).as_posix() not in {r["path"][len(".project-log/"):] for r in rows}
)

print(json.dumps({
    "tracked_count": len(rows),
    "all_byte_equal": all(r["byte_equal"] for r in rows),
    "rows": rows,
    "extra_files_in_archive": extra,
    "source_dir_exists": (NESTED / ".project-log").exists(),
}, indent=2))
