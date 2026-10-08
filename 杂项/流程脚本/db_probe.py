import sqlite3, json
db = r"C:\Users\12187\.local\share\opencode\opencode.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
cur = con.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("TABLES:", tables)
for t in tables:
    try:
        cols = [d[1] for d in cur.execute(f"PRAGMA table_info({t})")]
        print(t, cols)
    except Exception as e:
        print(t, "ERR", e)
