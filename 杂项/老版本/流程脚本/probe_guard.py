import os
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

print("== expanduser with HOME ==")
os.environ["HOME"] = r"C:\Users\12187\AppData\Local\Temp\probe-home"
try:
    print("  ~/kb ->", Path("~/kb").expanduser())
except Exception as e:
    print("  ~/kb raised", type(e).__name__, e)
try:
    print("  ~vibe-no-such-user-9f3a/kb ->", Path("~vibe-no-such-user-9f3a/kb").expanduser())
except Exception as e:
    print("  ~user raised", type(e).__name__, e)

print("== urlsplit file:// forms ==")
for u in (
    "file://localhost/C:/Users/x/kb",
    "file://localhostC:\\Users\\x\\kb",
    "file:///C:/Users/x/kb",
):
    p = urlsplit(u)
    print(f"  {u!r} -> scheme={p.scheme!r} netloc={p.netloc!r} path={p.path!r}")

print("== Path forms ==")
for s in ("/C:/Users/x/kb", "C:/Users/x/kb", "C:\\Users\\x\\kb"):
    p = Path(s)
    print(f"  {s!r} -> {p!r} absolute={p.is_absolute()}")

print("== repository_identity comparison ==")
kb = r"D:\Project\My_knowledge_base"
linked = r"C:\Users\12187\AppData\Local\Temp\opencode\probe-linked-wt"
subprocess.run(["git", "-C", kb, "worktree", "remove", "--force", linked], capture_output=True)
subprocess.run(["git", "-C", kb, "worktree", "add", "-q", "-b", "probe-wt", linked], capture_output=True)
for label, path in (("kb", kb), ("linked", linked)):
    for args in (("rev-parse", "--path-format=absolute", "--git-common-dir"), ("rev-parse", "--git-common-dir")):
        p = subprocess.run(["git", "-C", path, *args], capture_output=True, text=True)
        print(f"  {label} {args[-1]}: rc={p.returncode} out={p.stdout.strip()!r}")
subprocess.run(["git", "-C", kb, "worktree", "remove", "--force", linked], capture_output=True)
subprocess.run(["git", "-C", kb, "branch", "-D", "probe-wt"], capture_output=True)