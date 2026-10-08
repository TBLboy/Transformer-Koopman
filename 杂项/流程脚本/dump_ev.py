import json
import sqlite3

db = r"D:\Project\Transformer-Koopman\.project-log\.state\271cf77f97434766a070e848f74d069f\d8f50b21fb5bd1698e18ef414c298bd22c818e7b14e96aa2320a17b0fd03d3b9\state.sqlite3"
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
cur = con.cursor()
cur.execute("PRAGMA table_info(evidence)")
print("COLS:", [r[1] for r in cur.fetchall()])
cur.execute("SELECT * FROM evidence WHERE id=?", ("EV-ALN010-POSENC-001",))
for r in cur.fetchall():
    d = dict(r)
    for k, v in d.items():
        if isinstance(v, str) and v.startswith("{"):
            try:
                d[k] = json.loads(v)
            except Exception:
                pass
    print(json.dumps(d, ensure_ascii=False, indent=2))
con.close()
