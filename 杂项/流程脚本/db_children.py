import sqlite3, json
db = r"C:\Users\12187\.local\share\opencode\opencode.db"
con=sqlite3.connect(f"file:{db}?mode=ro",uri=True); con.row_factory=sqlite3.Row; cur=con.cursor()
print("children (agent like verification|codebase|business|solution|implementation|alignment|paper|workflow):")
q="""SELECT s.id, s.agent, s.model, s.tokens_input, s.tokens_output, s.time_created FROM session s WHERE s.parent_id IS NOT NULL ORDER BY s.time_created DESC LIMIT 25"""
for r in cur.execute(q):
    print(dict(r))
