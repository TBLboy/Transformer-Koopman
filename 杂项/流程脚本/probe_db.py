import json
import re
import sqlite3
import sys

DB = r"C:\Users\12187\.local\share\opencode\opencode.db"

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = con.cursor()

print("=== tables ===")
cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY name")
tables = cur.fetchall()
for name, kind in tables:
    print(" ", kind, name)

print()
print("=== schemas of likely tables ===")
for name, kind in tables:
    if kind != "table":
        continue
    low = name.lower()
    if any(k in low for k in ("model", "agent", "config", "kv", "state", "project", "session")):
        try:
            cur.execute(f"PRAGMA table_info([{name}])")
            cols = [r[1] for r in cur.fetchall()]
            cur.execute(f"SELECT COUNT(*) FROM [{name}]")
            n = cur.fetchone()[0]
            print(f"--- {name} (rows={n}) cols={cols}")
        except Exception as exc:  # noqa: BLE001
            print(f"--- {name} ERR {exc}")

print()
print("=== rows containing 'codebase-onboarder' ===")
for name, kind in tables:
    if kind != "table":
        continue
    try:
        cur.execute(f"PRAGMA table_info([{name}])")
        cols = [r[1] for r in cur.fetchall()]
    except Exception:  # noqa: BLE001
        continue
    for col in cols:
        try:
            cur.execute(
                f"SELECT rowid, [{col}] FROM [{name}] WHERE CAST([{col}] AS TEXT) LIKE '%codebase-onboarder%' LIMIT 5"
            )
            rows = cur.fetchall()
        except Exception:  # noqa: BLE001
            continue
        for rowid, val in rows:
            text = val if isinstance(val, str) else repr(val)
            print(f"  [{name}.{col}] rowid={rowid}")
            if len(text) > 1200:
                idx = text.find("codebase-onboarder")
                text = text[max(0, idx - 400): idx + 600]
            print("   ", text.replace("\n", "\\n")[:1400])
            print()
