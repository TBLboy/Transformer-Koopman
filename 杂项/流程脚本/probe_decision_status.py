import json
import re
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
conn = sqlite3.connect(DB)

print("=== existing decision statuses ===")
for rid, st in conn.execute("select id,status from records where kind='decision' order by id"):
    print(f"  {rid} -> {st}")

src = Path(r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\state_store.py").read_text(encoding="utf-8")
m = re.search(r"RECORD_KIND_STATUS\s*[:=].*?(?=\n[A-Z_]+\s*[:=]|\ndef )", src, re.S)
if m:
    print("\n=== RECORD_KIND_STATUS ===\n" + m.group(0)[:700])

# which status is valid for decision?
dm = re.search(r'"decision"\s*:\s*\(([^)]*)\)', src)
if dm:
    print("\n=== decision allowed statuses ===\n " + dm.group(1))


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
    note = "" if ok else " -> " + r.stderr.decode("utf-8", "replace").strip()[:200]
    print(f"  {'OK  ' if ok else 'FAIL'} {label}{note}")
    return ok
