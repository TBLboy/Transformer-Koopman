import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
db = next(Path(r"D:\Project\Transformer-Koopman", ".project-log", ".state").rglob("state.sqlite3"))
c = sqlite3.connect(db)
print("kind/status:", c.execute("select distinct kind,status from records").fetchall())
print("decision statuses:", c.execute("select distinct status from records where kind='decision'").fetchall())
