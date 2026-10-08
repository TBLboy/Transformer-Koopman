"""Probe the environment used by the step-3 script exercises."""
from __future__ import annotations

import shutil
import sys
import tempfile
import uuid
from pathlib import Path

REPO = Path(r"D:\Project\vibe-coding\vibe-coding")
sys.path.insert(0, str(REPO / "runtime" / "scripts"))

print("npm:", shutil.which("npm"))
print("bun:", shutil.which("bun"))
print("codex:", shutil.which("codex"))
try:
    import yaml  # noqa: F401
    print("yaml: ok")
except Exception as exc:  # noqa: BLE001
    print("yaml: missing", exc)

# Build a transactional Project Log with a non-ASCII goal title to drive the hooks.
from state_context import compact_context, initialize  # noqa: E402

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary) / "工程记录" / "work"
    root.mkdir(parents=True)
    store = initialize(root)
    store.apply({
        "schema_version": 1, "command_id": uuid.uuid4().hex,
        "expected_revision": store.status()["revision"],
        "action": "goal.create", "payload": {"id": "GOAL-001", "title": "中文目标"},
    })
    text = compact_context(root)
    print("compact_context ascii-only:", text.isascii())
    print("compact_context snippet:", text[:200].replace("\n", "\\n"))
