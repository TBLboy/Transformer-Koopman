import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\12187\.config\opencode\vibe-workflow\scripts")
from state_context import open_store  # noqa: E402

ROOT = Path(r"D:\Project\辅料称重防错系统")
store = open_store(ROOT, heal=True)
for ev in store.list_evidence():
    if ev["id"].startswith(("EV-TASK-140", "EV-TASK-141")):
        print(
            json.dumps(
                {
                    "id": ev["id"],
                    "status": ev["status"],
                    "invalidated_sequence": ev.get("invalidated_sequence"),
                    "reason": (ev.get("invalidation_reason") or "")[:90],
                },
                ensure_ascii=False,
            )
        )
print("--- stale_evidence now ---")
print(json.dumps(store.stale_evidence(ROOT), ensure_ascii=False)[:800])
