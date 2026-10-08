import subprocess

kb = r"D:\Project\My_knowledge_base"
local = r"D:\Project\vibe-coding\.project-log\ledger\v1\ledger.jsonl"
spec = ":工程记录/vibe-coding/.project-log/ledger/v1/ledger.jsonl"

local_bytes = open(local, "rb").read()
staged = subprocess.run(["git", "-C", kb, "cat-file", "blob", spec], capture_output=True).stdout
print("local  len =", len(local_bytes), "CRLF=", local_bytes.count(b"\r\n"), "LF=", local_bytes.count(b"\n"))
print("staged len =", len(staged), "CRLF=", staged.count(b"\r\n"), "LF=", staged.count(b"\n"))
print("equal =", local_bytes == staged)
# first difference
n = min(len(local_bytes), len(staged))
for i in range(n):
    if local_bytes[i] != staged[i]:
        print("first diff at", i, "local=", local_bytes[i:i+20], "staged=", staged[i:i+20])
        break
else:
    print("common prefix identical; length differs" if len(local_bytes) != len(staged) else "identical")

for cfg in ("core.autocrlf", "core.eol", "core.safecrlf"):
    p = subprocess.run(["git", "-C", kb, "config", "--get", cfg], capture_output=True, text=True)
    print("KB", cfg, "=", repr(p.stdout.strip()))
p = subprocess.run(["git", "config", "--global", "--get", "core.autocrlf"], capture_output=True, text=True)
print("global core.autocrlf =", repr(p.stdout.strip()))
p = subprocess.run(["git", "config", "--system", "--get", "core.autocrlf"], capture_output=True, text=True)
print("system core.autocrlf =", repr(p.stdout.strip()))
