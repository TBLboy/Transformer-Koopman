# -*- coding: utf-8 -*-
import sys, io, json, sqlite3, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

root = r"D:\Project\Transformer-Koopman\.project-log"
db = glob.glob(os.path.join(root, ".state", "*", "*", "state.sqlite3"))
print("db:", db)
con = sqlite3.connect(db[0])
con.row_factory = sqlite3.Row
cur = con.cursor()
# revision
for t in ("meta", "state_meta", "store_meta"):
    try:
        rows = cur.execute("SELECT * FROM %s" % t).fetchall()
        print(t, [dict(r) for r in rows][:5])
    except Exception as e:
        pass
print("tables:", [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
