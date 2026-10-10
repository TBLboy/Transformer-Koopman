import sqlite3, json
db = r"C:\Users\12187\.local\share\opencode\opencode.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True); con.row_factory = sqlite3.Row
cur = con.cursor()
for sid,label in [("ses_f23144e55ffeLhRX1s1rknQq6Z","reviewer(worked)"),("ses_f230b49e1ffebsNyi46YXwb3pF","onboarder(failed)")]:
    r = cur.execute("SELECT id,agent,model,tokens_input,tokens_output,cost FROM session WHERE id=?",(sid,)).fetchone()
    print(label, dict(r) if r else None)
    for m in cur.execute("SELECT data FROM message WHERE session_id=? AND json_extract(data,'$.role')='user' ORDER BY time_created LIMIT 1",(sid,)):
        d=json.loads(m["data"]); print("   user-model:", d.get("model"))
