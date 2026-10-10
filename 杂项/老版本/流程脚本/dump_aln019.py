# -*- coding: utf-8 -*-
import sys, io, json, sqlite3, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

root = r"D:\Project\Transformer-Koopman\.project-log"
db = glob.glob(os.path.join(root, ".state", "*", "*", "state.sqlite3"))[0]
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
cur = con.cursor()
for rid in ("ALN-019", "ALN-007", "ALN-012", "ALN-014", "ALN-015", "ALN-016", "ALN-017", "ALN-018"):
    r = cur.execute("SELECT id,status,revision,payload FROM records WHERE id=?", (rid,)).fetchone()
    print("=" * 70)
    print(r["id"], r["status"], "rev=%s" % r["revision"])
    print(json.dumps(json.loads(r["payload"]), ensure_ascii=False, indent=2))
