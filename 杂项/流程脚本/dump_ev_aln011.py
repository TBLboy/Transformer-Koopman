import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

db = next(Path(r"D:\Project\Transformer-Koopman\.project-log\.state").rglob("state.sqlite3"))
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
r = con.execute("SELECT * FROM evidence WHERE id='EV-ALN011-001'").fetchone()
d = dict(r)
for k, v in d.items():
    if isinstance(v, str) and v.startswith("{"):
        try:
            d[k] = json.loads(v)
        except Exception:
            pass
print(json.dumps(d, ensure_ascii=False, indent=2))
con.close()
