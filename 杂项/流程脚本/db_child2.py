import sqlite3, json
db = r"C:\Users\12187\.local\share\opencode\opencode.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True); con.row_factory = sqlite3.Row
cur = con.cursor()
sid = "ses_f230b49e1ffebsNyi46YXwb3pF"
print("=== messages ===")
msgs = list(cur.execute("SELECT id,time_created,data FROM message WHERE session_id=? ORDER BY time_created",(sid,)))
for m in msgs:
    d = json.loads(m["data"]) if isinstance(m["data"],str) else m["data"]
    print(m["id"], d.get("role") or d.get("type"), "finish=",d.get("finish"),"err=",d.get("error"))
    print("   ", json.dumps(d, ensure_ascii=False)[:600])
print("=== parts ===")
for p in cur.execute("SELECT id,message_id,time_created,data FROM part WHERE session_id=? ORDER BY time_created",(sid,)):
    d = json.loads(p["data"]) if isinstance(p["data"],str) else p["data"]
    print(p["id"], d.get("type"), json.dumps(d, ensure_ascii=False)[:500])
print("=== session_input ===")
for r in cur.execute("SELECT * FROM session_input WHERE session_id=?",(sid,)):
    print(dict(r).get("prompt","")[:1500])
