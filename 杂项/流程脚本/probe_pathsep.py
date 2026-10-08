import subprocess
from pathlib import Path

kb = r"D:\Project\My_knowledge_base"
fwd = "/".join(["工程记录", "vibe-coding", ".project-log", "ledger", "v1", "ledger.jsonl"])
back = str(Path("工程记录") / "vibe-coding" / ".project-log" / "ledger" / "v1" / "ledger.jsonl")
print("fwd =", fwd)
print("back=", back)
for label, spec in (("cat-file fwd ", ":" + fwd), ("cat-file back", ":" + back)):
    p = subprocess.run(["git", "-C", kb, "cat-file", "blob", spec], capture_output=True)
    print(label, "rc=", p.returncode, "bytes=", len(p.stdout))
for label, spec in (("ls-files fwd ", fwd), ("ls-files back", back)):
    p = subprocess.run(["git", "-C", kb, "ls-files", "--error-unmatch", "--", spec],
                       capture_output=True, text=True)
    print(label, "rc=", p.returncode, "out=", p.stdout.strip()[:70])
