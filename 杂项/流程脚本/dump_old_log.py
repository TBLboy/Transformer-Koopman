import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

OLD = r"D:\Project\论文3老版本\Transformer-Koopman"
OUT = r"C:\Users\12187\AppData\Local\Temp\opencode\old-project-log.txt"

FILES = [
    ".project-log/requirements.md",
    ".project-log/business-logic/main.md",
    ".project-log/business-logic/nodes.md",
    ".project-log/business-logic/edges.md",
    ".project-log/business-logic/constraints.md",
    ".project-log/business-logic/graph.md",
    ".project-log/business-logic/open-questions.md",
    ".project-log/business-logic/decision-records.md",
    ".project-log/architecture/software-architecture.md",
    ".project-log/config/config-schema.md",
    ".project-log/hardware/hardware-list.md",
    ".project-log/debugging/known-issues.md",
]

chunks = []
for rel in FILES:
    r = subprocess.run(["git", "-C", OLD, "show", f"HEAD:{rel}"], capture_output=True)
    if r.returncode != 0:
        chunks.append(f"\n\n{'#' * 78}\n# {rel}\n# GIT ERROR: {r.stderr.decode('utf-8', 'replace')}\n")
        continue
    body = r.stdout.decode("utf-8", "replace")
    chunks.append(f"\n\n{'#' * 78}\n# {rel}\n{'#' * 78}\n{body}")

text = "".join(chunks)
open(OUT, "w", encoding="utf-8", newline="\n").write(text)
print("written:", OUT)
print("bytes:", len(text.encode("utf-8")))
print("files:", len(FILES))
