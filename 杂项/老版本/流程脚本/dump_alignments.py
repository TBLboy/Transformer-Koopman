# -*- coding: utf-8 -*-
import sys, io, json, sqlite3, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

root = r"D:\Project\Transformer-Koopman\.project-log"
db = glob.glob(os.path.join(root, ".state", "*", "*", "state.sqlite3"))[0]
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
cur = con.cursor()
for r in cur.execute("SELECT id,status,revision,payload FROM records WHERE kind='alignment' ORDER BY id").fetchall():
    p = json.loads(r["payload"])
    print("=" * 70)
    print("%s  [%s] rev=%s" % (r["id"], r["status"], r["revision"]))
    print("class:", p.get("class"))
    print("subject:", p.get("subject"))
    for k in ("should", "actual", "impact", "verification", "status_note", "resolution", "residual", "residual_owner", "fix_ref"):
        if k in p:
            v = p[k]
            if isinstance(v, list):
                print("%s:" % k)
                for it in v:
                    print("   -", it)
            else:
                print("%s: %s" % (k, v))
