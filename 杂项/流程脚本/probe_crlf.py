import subprocess
from pathlib import Path

log = Path(r"D:\Project\vibe-coding\.project-log")
kb = r"D:\Project\My_knowledge_base"
prefix = "工程记录/vibe-coding/.project-log/"

crlf = []
lf_only = []
binary = []
for p in sorted(log.rglob("*")):
    if p.is_dir():
        continue
    rel = p.relative_to(log).as_posix()
    if rel.startswith(".state/") or rel.startswith("ledger/"):
        continue
    b = p.read_bytes()
    if b"\x00" in b[:4096]:
        binary.append(rel)
        continue
    if b"\r\n" in b:
        crlf.append(rel)
    else:
        lf_only.append(rel)

print("== local .project-log (excl .state, ledger) ==")
print("CRLF files:", len(crlf))
for r in crlf:
    print("  CRLF", r)
print("LF files:", len(lf_only))
print("binary:", binary)

print("\n== KB HEAD EOL sample ==")
files = ["current-session.md", "progress.md", "requirements.md", "state-format.json", ".gitignore", "workflow.yaml"]
for f in files:
    spec = f"HEAD:{prefix}{f}"
    d = subprocess.run(["git", "-C", kb, "show", spec], capture_output=True).stdout
    if d == b"":
        print(f"  {f}: <absent in HEAD>")
    else:
        print(f"  {f}: len={len(d)} CRLF={d.count(chr(13).encode()+chr(10).encode())} LF={d.count(chr(10).encode())}")
