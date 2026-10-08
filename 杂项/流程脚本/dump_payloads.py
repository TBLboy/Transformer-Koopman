import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

db = next(Path(r"D:\Project\Transformer-Koopman\.project-log\.state").rglob("state.sqlite3"))
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
for rid in ("ALN-019", "ALN-007", "ALN-009", "ALN-012", "ALN-014", "ALN-015", "ALN-016", "ALN-017", "ALN-018", "ALN-005", "ALN-001", "ALN-002"):
    r = con.execute("SELECT payload FROM records WHERE id=?", (rid,)).fetchone()
    print("=" * 70)
    print(rid)
    print(json.dumps(json.loads(r["payload"]), ensure_ascii=False, indent=2))
con.close()
