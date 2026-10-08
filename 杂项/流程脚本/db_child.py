import sqlite3, json
db = r"C:\Users\12187\.local\share\opencode\opencode.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True); con.row_factory = sqlite3.Row
cur = con.cursor()
print("=== sessions with agent onboarding ===")
for r in cur.execute("SELECT id,parent_id,agent,directory,title,time_created,time_updated,cost,tokens_input,tokens_output,providerID FROM (SELECT s.*, json_extract(s.model,'$.providerID') AS providerID FROM session s) WHERE agent LIKE '%onboard%' ORDER BY time_created DESC LIMIT 10"):
    print(dict(r))
print("=== children of main session ===")
for r in cur.execute("SELECT id,parent_id,agent,title,time_created,time_updated,tokens_input,tokens_output FROM session WHERE parent_id='ses_f231aa70dffeeUTgK6WrHc6jov' ORDER BY time_created DESC LIMIT 20"):
    print(dict(r))
