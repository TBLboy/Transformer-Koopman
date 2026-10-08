import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
DB = next(Path(ROOT, ".project-log", ".state").rglob("state.sqlite3"))

FILES = [
    "Transformer-Koopman/训练代码/configs/platform1.yaml",
    "Transformer-Koopman/训练代码/configs/platform2.yaml",
    "Transformer-Koopman/训练代码/tests/test_config_contract.py",
]
VB = {"git_commit": None, "diff_hash": None,
      "file_hashes": {f: hashlib.sha256((Path(ROOT) / f).read_bytes()).hexdigest() for f in FILES}}


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
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:260]))
    return ok


def rec_rev(rid):
    c = sqlite3.connect(DB)
    row = c.execute("SELECT revision FROM records WHERE id=?", (rid,)).fetchone()
    c.close()
    return row[0]


print("== evidence: FIX-03 (ALN-004 partial) ==")
apply("evidence.record", {
    "id": "EV-FIX03-001", "kind": "test",
    "subject": "FIX-03 配置键读写收敛（ALN-004 部分）：把 utils/seed.py 的 5 个静默默认值显式写入配置——platform1.yaml 补 float32_matmul_precision；platform2.yaml 补 deterministic/amp/float32_matmul_precision。复核：platform1 缺失键 0，platform2 缺失键 3（均为 ALN-002 的 multi_step.*，属阶段②）。新增 test_cuda_performance_keys_are_explicit（5 键 x 2 平台）并把 data_dir 检查扩展到两平台；套件 152 passed / 2 skipped / 1 xfailed",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES},
    "version_binding": VB}, "t21-ev-fix03", "EV-FIX03-001")

print("\n== ALN-004: record partial resolution (stays open) ==")
ok = apply("record.update", {
    "kind": "alignment", "id": "ALN-004",
    "expected_record_revision": rec_rev("ALN-004"),
    "status": "open",
    "payload": {
        "class": "implementation-drift",
        "doc_ref": {"path": ".project-log/docs/business-logic/clarification.yaml",
                    "sha256": "632aa4ffb82e6ceb254107524f4c733535719db92211a7db456be514ee3dac6e"},
        "status_note": "partially-resolved",
        "subject": "代码读取但 YAML 缺失的配置键（含 platform2 缺 6 项）",
        "resolved_part": "experiment.* 四项已显式化：platform1 补 float32_matmul_precision；platform2 补 deterministic/amp/float32_matmul_precision。守卫 test_cuda_performance_keys_are_explicit 已就位（EV-FIX03-001）。",
        "residual": "platform2 仍缺 training.edmd.pretrain.multi_step.horizon 与 loss_weights.multi_step_physical / multi_step_latent 三项；这三项即 ALN-002 的五项损失缺口，属阶段②（DEC-003/DEC-004），由 test_stage1_loss_declares_five_terms 的 xfail 记录。",
        "residual_owner": "ALN-002 / FIX-02（阶段②）",
    }}, "t21-aln004", "ALN-004 payload updated")
if not ok:
    print("  (payload update rejected; ALN-004 left unchanged)")

print("\nfinal revision:", revision())
