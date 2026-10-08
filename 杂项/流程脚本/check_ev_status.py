import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

db = next(Path(r"D:\Project\Transformer-Koopman\.project-log\.state").rglob("state.sqlite3"))
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
for rid in ("EV-ALN011-001", "EV-ALN010-ROLLOUT-001"):
    r = con.execute(
        "SELECT id,status,invalidated_sequence,invalidation_reason FROM evidence WHERE id=?",
        (rid,),
    ).fetchone()
    print(dict(r))
con.close()
