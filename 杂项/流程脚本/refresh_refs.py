import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
DOC_REL = ".project-log/docs/business-logic/clarification.yaml"
DOC_ABS = Path(ROOT) / DOC_REL

raw = DOC_ABS.read_bytes()
NEW_SHA = hashlib.sha256(raw).hexdigest()
print("doc bytes:", len(raw), " sha256:", NEW_SHA)

data = yaml.safe_load(raw.decode("utf-8"))
print("YAML VALID  alignment entries:", len(data["alignment"]), " invariants:",
      len(data["functional_business_logic"]["invariants"]))
print()

DB = next(Path(ROOT, ".project-log", ".state").rglob("state.sqlite3"))
conn = sqlite3.connect(DB)


def revision() -> int:
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def apply(action: str, payload: dict, tag: str, label: str) -> bool:
    envelope = {"schema_version": 1, "command_id": tag,
                "expected_revision": revision(), "action": action, "payload": payload}
    path = f"{TMP}/env_{tag}.json"
    open(path, "w", encoding="utf-8", newline="\n").write(
        json.dumps(envelope, ensure_ascii=False, indent=2))
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path],
                       capture_output=True)
    ok = r.returncode == 0
    note = "" if ok else r.stderr.decode("utf-8", "replace").strip()[:150]
    print(f"  {'OK ' if ok else 'FAIL'} {label} {note}")
    return ok


print("== refresh doc_ref hashes on records that carry one ==")
carriers = []
for kind, rid, rev, payload_json in conn.execute(
        "SELECT kind, id, revision, payload FROM records ORDER BY kind, id"):
    if "doc_ref" in (payload_json or ""):
        carriers.append((kind, rid, rev))
print(f"  carriers: {len(carriers)}")
for kind, rid, rev in carriers:
    apply("record.update",
          {"kind": kind, "id": rid, "expected_record_revision": rev,
           "payload": {"doc_ref": {"path": DOC_REL, "sha256": NEW_SHA}}},
          f"t-refresh-{kind}-{rid}".lower().replace("_", "-"),
          f"{kind}/{rid}")

print()
print("== create the four new alignment entries ==")
NEW_ALN = [
    ("ALN-015", "constraint-conflict", "稳定性不变量 INV1 在实际配置与产物中被违反（两平台均关闭稳定机制，日志出现 rho=1.0138/1.0842/1.2351）"),
    ("ALN-016", "implementation-drift", "MLP/LSTM 基线的 consistency 项用 detached 预测做目标，与论文 L_c 的重编码语义不同"),
    ("ALN-017", "constraint-conflict", "论文谱系未收敛：论文.txt 与 paper_notes.txt 内容不同，43 份 tex 草稿中仅 2 份含多步损失"),
    ("ALN-018", "implementation-drift", "多步损失用 F.mse_loss 均值归约，论文定义为 sum_{i=1..N_L}，缩放不一致"),
]
for aid, klass, subject in NEW_ALN:
    apply("record.create",
          {"kind": "alignment", "id": aid, "title": subject, "status": "open",
           "payload": {"class": klass, "subject": subject,
                       "doc_ref": {"path": DOC_REL, "sha256": NEW_SHA}}},
          f"t-new-{aid.lower()}", f"alignment/{aid}")

print()
print("final revision:", revision())
