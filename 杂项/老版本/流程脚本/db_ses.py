import sqlite3, json
db = r"C:\Users\12187\.local\share\opencode\opencode.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()
sid = "ses_f231aa70dffeeUTgK6WrHc6jov"
row = cur.execute("SELECT * FROM session WHERE id=?", (sid,)).fetchone()
print("SESSION:", dict(row) if row else None)
print("--- messages ---")
for m in cur.execute("SELECT id, time_created, data FROM message WHERE session_id=? ORDER BY time_created", (sid,)):
    d = json.loads(m["data"]) if isinstance(m["data"], str) else m["data"]
    role = d.get("role") or d.get("type")
    err = d.get("error")
    print(m["id"], role, "err=", err)
    print("   keys:", list(d.keys()))
