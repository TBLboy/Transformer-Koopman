import json
import sqlite3
import sys

db = r"D:\Project\Transformer-Koopman\.project-log\.state\271cf77f97434766a070e848f74d069f\d8f50b21fb5bd1698e18ef414c298bd22c818e7b14e96aa2320a17b0fd03d3b9\state.sqlite3"
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("TABLES:", [r[0] for r in cur.fetchall()])
for tbl in ("records", "record"):
    try:
        cur.execute(f"SELECT * FROM {tbl} WHERE id=?", ("ALN-010",))
        rows = cur.fetchall()
        if rows:
            for r in rows:
                print("TABLE", tbl)
                print(json.dumps(dict(r), ensure_ascii=False, indent=2))
            break
    except Exception as e:
        print(tbl, "ERR", e)
con.close()
