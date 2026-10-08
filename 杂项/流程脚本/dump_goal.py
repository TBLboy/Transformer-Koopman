# -*- coding: utf-8 -*-
import sys, io, json, sqlite3, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

root = r"D:\Project\Transformer-Koopman\.project-log"
db = glob.glob(os.path.join(root, ".state", "*", "*", "state.sqlite3"))[0]
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
cur = con.cursor()
for r in cur.execute("SELECT * FROM goals").fetchall():
    print("id=%s status=%s" % (r["id"], r["status"]))
    print("extensions:", json.dumps(json.loads(r["extensions"]), ensure_ascii=False, indent=2))
