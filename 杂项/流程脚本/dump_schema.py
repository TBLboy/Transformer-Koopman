# -*- coding: utf-8 -*-
import sys, io, json, sqlite3, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

root = r"D:\Project\Transformer-Koopman\.project-log"
db = glob.glob(os.path.join(root, ".state", "*", "*", "state.sqlite3"))[0]
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
cur = con.cursor()
print("tables:", [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
for t in [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
    cols = [c[1] for c in cur.execute("PRAGMA table_info(%s)" % t).fetchall()]
    print("--", t, cols)
