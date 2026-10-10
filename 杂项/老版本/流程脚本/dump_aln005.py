# -*- coding: utf-8 -*-
import sys, io, json, sqlite3, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

root = r"D:\Project\Transformer-Koopman\.project-log"
db = glob.glob(os.path.join(root, ".state", "*", "*", "state.sqlite3"))[0]
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
cur = con.cursor()
for r in cur.execute("SELECT kind,id,status,revision,payload FROM records WHERE id='ALN-005'").fetchall():
    print("kind=%s id=%s status=%s rev=%s" % (r["kind"], r["id"], r["status"], r["revision"]))
    print(json.dumps(json.loads(r["payload"]), ensure_ascii=False, indent=2))
print("=== evidence ===")
for r in cur.execute("SELECT id,status,subject,covers FROM evidence ORDER BY recorded_sequence").fetchall():
    print(r["id"], r["status"], r["subject"])
