# -*- coding: utf-8 -*-
import sys, io, json, sqlite3, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

root = r"D:\Project\Transformer-Koopman\.project-log"
db = glob.glob(os.path.join(root, ".state", "*", "*", "state.sqlite3"))[0]
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
cur = con.cursor()
print("=== decisions ===")
for r in cur.execute("SELECT id,status,revision,title FROM records WHERE kind='decision' ORDER BY id").fetchall():
    print(r["id"], r["status"], "rev=%s" % r["revision"], r["title"])
print("=== alignments ===")
for r in cur.execute("SELECT id,status,revision FROM records WHERE kind='alignment' ORDER BY id").fetchall():
    print(r["id"], r["status"], "rev=%s" % r["revision"])
