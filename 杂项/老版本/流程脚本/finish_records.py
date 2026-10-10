import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
DOC_REL = ".project-log/docs/business-logic/clarification.yaml"


def revision() -> int:
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def apply(payload: dict, tag: str, label: str) -> None:
    envelope = {
        "schema_version": 1,
        "command_id": tag,
        "expected_revision": revision(),
        "action": payload.pop("__action__"),
        "payload": payload,
    }
    path = f"{TMP}/env_{tag}.json"
    open(path, "w", encoding="utf-8", newline="\n").write(
        json.dumps(envelope, ensure_ascii=False, indent=2)
    )
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path],
                       capture_output=True)
    ok = r.returncode == 0
    note = "" if ok else r.stderr.decode("utf-8", "replace").strip()[:200]
    print(f"  {'OK ' if ok else 'FAIL'} {label} {note}")


import hashlib
DOC_SHA = hashlib.sha256(
    open(r"D:\Project\Transformer-Koopman\.project-log\docs\business-logic\clarification.yaml", "rb").read()
).hexdigest()

print("== REQ-001 (with approval.status) ==")
apply({
    "__action__": "record.create",
    "kind": "requirement", "id": "REQ-001",
    "title": "阶段① 重构业务逻辑澄清基线", "status": "draft",
    "payload": {
        "doc_ref": {"path": DOC_REL, "sha256": DOC_SHA},
        "approval": {"status": "pending", "note": "待用户批准后提升为 approved / active"},
        "scope": "功能业务逻辑 + 技术业务逻辑 + 双向对齐，覆盖双平台主链路与消融",
        "covers": ["BA-MP1", "BA-PLATFORMS", "BA-METHODS", "BA-LOSS-STRUCT", "BA-ABLATION", "BA-SCOPE"],
    },
}, "t013-req001", "REQ-001")

print("== mark the user's C-level decisions as C / approved ==")
for rid, tag in (("DEC-002", "t014-dec002-c"), ("DEC-003", "t015-dec003-c"), ("DEC-004", "t016-dec004-c")):
    apply({
        "__action__": "record.update",
        "kind": "decision", "id": rid, "expected_record_revision": 1,
        "payload": {"authority": "C", "user_approval": "approved"},
    }, tag, rid)

print()
print("final revision:", revision())
