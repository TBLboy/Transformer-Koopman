# -*- coding: utf-8 -*-
import sys, io, json, sqlite3, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
db = glob.glob(r"D:\Project\Transformer-Koopman\.project-log\.state\*\*\state.sqlite3")[0]
c = sqlite3.connect(db)
c.row_factory = sqlite3.Row
for rid in ("DEC-003", "DEC-002"):
    r = c.execute("SELECT id,title,payload FROM records WHERE id=?", (rid,)).fetchone()
    print("=" * 60)
    print(r["id"], r["title"])
    print(json.dumps(json.loads(r["payload"]), ensure_ascii=False, indent=2))
