import json
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
DB = next(Path(ROOT, ".project-log", ".state").rglob("state.sqlite3"))
DOC = ".project-log/docs/business-logic/clarification.yaml"
NEW = "39de4ac263088864d65c75f27a2df036767bbc9905c3c8da68579d6ffad95349"


def revision():
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def apply(action, payload, tag, label):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(),
           "action": action, "payload": payload}
    p = f"{TMP}/env_{tag}.json"
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(env, ensure_ascii=False, indent=2))
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", p], capture_output=True)
    ok = r.returncode == 0
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:300]))


c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
rows = c.execute("SELECT kind,id,revision,payload FROM records").fetchall()
c.close()

targets = []
for r in rows:
    try:
        p = json.loads(r["payload"])
    except Exception:
        continue
    dr = p.get("doc_ref")
    if isinstance(dr, dict) and dr.get("sha256") and dr.get("sha256") != NEW:
        targets.append((r["kind"], r["id"], r["revision"], dr.get("sha256")))

print("records to re-point:", len(targets))
for kind, rid, rev, old in targets:
    apply("record.update", {"kind": kind, "id": rid, "expected_record_revision": rev,
                            "payload": {"doc_ref": {"path": DOC, "sha256": NEW}}},
          f"t31-docref-{rid}", f"{kind}/{rid} ({old[:12]} -> {NEW[:12]})")

print("\nfinal revision:", revision())
