import glob
import sqlite3

p = glob.glob(r"D:\Project\Transformer-Koopman\.project-log\.state\**\state.sqlite3", recursive=True)[0]
print("DB:", p)
c = sqlite3.connect(p)
tables = [r[0] for r in c.execute("select name from sqlite_master where type='table'")]
print("tables:", tables)
for t in tables:
    if "evid" in t.lower() or "review" in t.lower():
        cols = [r[1] for r in c.execute(f"PRAGMA table_info({t})")]
        print(f"\n== {t} cols: {cols}")
        for row in c.execute(f"select * from {t} limit 3"):
            print(row)
