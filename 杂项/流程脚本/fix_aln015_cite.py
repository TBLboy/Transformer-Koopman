import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
O = r"D:\Project\论文3老版本\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
DOC_REL = ".project-log/docs/business-logic/clarification.yaml"
DOC_ABS = Path(ROOT) / DOC_REL

# --- establish ground truth straight from the log ---
LOG = Path(O) / "results/logs/p2_patchtst_koopman.log"
lines = LOG.read_text(encoding="utf-8", errors="replace").split("\n")
hits = []
for i, ln in enumerate(lines, 1):
    m = re.search(r"(?:rho|谱半径)[^0-9\n]{0,24}([0-9]+(?:\.[0-9]+)?)", ln)
    if m and float(m.group(1)) > 1.0:
        hits.append((i, float(m.group(1)), ln.strip()))
print("GROUND TRUTH  p2_patchtst_koopman.log  rho>1 occurrences:")
for i, v, raw in hits:
    print(f"  line {i}: {v}   << {raw}")

citation = "      - results/logs/p2_patchtst_koopman.log (" + "; ".join(
    f"line {i} = {v}" for i, v, _ in hits) + ")\n"
print("\nNEW citation line:", citation.strip())

text = DOC_ABS.read_text(encoding="utf-8")
OLD = "      - results/logs/p2_patchtst_koopman.log (rho=1.0005, lines 58 and 3022)\n"
if OLD in text:
    text = text.replace(OLD, citation)
    DOC_ABS.write_text(text, encoding="utf-8", newline="\n")
    print("  citation FIXED")
else:
    print("  PATTERN NOT FOUND -- aborting")
    sys.exit(1)

raw = DOC_ABS.read_bytes()
NEW_SHA = hashlib.sha256(raw).hexdigest()
data = yaml.safe_load(raw.decode("utf-8"))
ids = [a["id"] for a in data["alignment"]]
print(f"\nYAML VALID  bytes={len(raw)}  sha256={NEW_SHA}  alignments={len(ids)} unique={len(set(ids))}")

DB = next(Path(ROOT, ".project-log", ".state").rglob("state.sqlite3"))
conn = sqlite3.connect(DB)


def revision():
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def apply(action, payload, tag, label):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(),
           "action": action, "payload": payload}
    p = f"{TMP}/env_{tag}.json"
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(env, ensure_ascii=False, indent=2))
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", p], capture_output=True)
    ok = r.returncode == 0
    print(f"  {'OK ' if ok else 'FAIL'} {label}" + ("" if ok else " " + r.stderr.decode("utf-8", "replace").strip()[:150]))


print("\n== refresh doc_ref hashes ==")
carriers = [(k, i, rev) for k, i, rev, pl in conn.execute(
    "SELECT kind, id, revision, payload FROM records ORDER BY kind, id") if "doc_ref" in (pl or "")]
print(f"  carriers: {len(carriers)}")
for kind, rid, rev in carriers:
    apply("record.update",
          {"kind": kind, "id": rid, "expected_record_revision": rev,
           "payload": {"doc_ref": {"path": DOC_REL, "sha256": NEW_SHA}}},
          f"t4-ref-{kind}-{rid}".lower().replace("_", "-"), f"{kind}/{rid}")

print("\nfinal revision:", revision())
