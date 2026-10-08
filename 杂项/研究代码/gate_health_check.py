import json
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.path.insert(0, r"C:\Users\12187\.config\opencode\vibe-workflow\scripts")

import state_store  # noqa: E402

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"

DB = next(Path(ROOT, ".project-log", ".state").rglob("state.sqlite3"))
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

print("=== goal completion problems (read-only) ===")
probs = state_store.Store._goal_completion_problems(conn, "GOAL-001", Path(ROOT))
malformed = [p for p in probs if "not an object" in p or "must be a list" in p]
genuine = [p for p in probs if p not in malformed]
print(f"  total={len(probs)}  malformed={len(malformed)}  genuine-unmet={len(genuine)}")
print("  --- malformed (should be 0) ---")
for p in malformed:
    print("   !", p)
print("  --- genuine unmet (first 16) ---")
for p in genuine[:16]:
    print("   -", p[:150])

print("\n=== task completion problems TASK-001 (read-only) ===")
row = conn.execute("select * from tasks where id='TASK-001'").fetchone()
t = dict(row)
t["extensions"] = json.loads(t["extensions"])
tp = state_store.Store._task_completion_problems(conn, t, Path(ROOT))
print("  problems:", tp if tp else "NONE")

print("\n=== evidence + review ===")
for r in conn.execute("select id,kind,subject,status,task_id from evidence"):
    print(f"  {r['id']:<24} kind={r['kind']:<9} status={r['status']:<7} task={r['task_id']}")
for r in conn.execute("select id,task_id,reviewer,verdict from reviews"):
    print(f"  {r['id']:<20} task={r['task_id']} reviewer={r['reviewer']} verdict={r['verdict']}")

print("\n=== stale check (evidence + documents) ===")
st = state_store.Store(root=Path(ROOT))
print("  stale evidence :", st.stale_evidence(Path(ROOT)))
print("  stale documents:", st.stale_documents(Path(ROOT)))

print("\n=== ledger ===")
r = subprocess.run([PY, VIBE, "--root", ROOT, "ledger", "verify"], capture_output=True)
out = json.loads(r.stdout.decode("utf-8", "replace"))
print("  events:", out.get("events"), " revision:", out.get("revision"),
      " matches:", out.get("matches"), " mismatches:", out.get("mismatches"))

print("\n=== counts ===")
for k, n in conn.execute("select kind,count(*) from records group by kind order by kind"):
    print(f"  {k:<14} {n}")
print("  tasks:", [r[0] for r in conn.execute("select id||':'||status from tasks")],
      " goals:", [r[0] for r in conn.execute("select id||':'||status from goals")])
