import json
import sqlite3

DB = r"C:\Users\12187\.local\share\opencode\opencode.db"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = con.cursor()

print("=== last 12 sessions: id | parent | agent | model | title ===")
cur.execute(
    "SELECT rowid, id, parent_id, agent, model, title FROM session ORDER BY rowid DESC LIMIT 12"
)
for rowid, sid, parent, agent, model, title in cur.fetchall():
    print(f"rowid={rowid} id={sid}")
    print(f"   parent={parent}")
    print(f"   agent={agent}")
    print(f"   model={model}")
    print(f"   title={title}")
    print()

print("=== distinct model values across all sessions ===")
cur.execute("SELECT model, COUNT(*) FROM session GROUP BY model ORDER BY COUNT(*) DESC")
for model, n in cur.fetchall():
    print(f"  {n:4d}  {model}")

print()
print("=== workspace table schema + rows ===")
cur.execute("PRAGMA table_info(workspace)")
print("cols:", [r[1] for r in cur.fetchall()])
try:
    cur.execute("SELECT * FROM workspace")
    for r in cur.fetchall():
        print(str(r)[:1500])
except Exception as exc:  # noqa: BLE001
    print("ERR", exc)

print()
print("=== project / project_directory rows ===")
for table in ("project", "project_directory"):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    print(f"--- {table} cols={cols}")
    cur.execute(f"SELECT * FROM {table}")
    for r in cur.fetchall():
        print("   ", str(r)[:600])
