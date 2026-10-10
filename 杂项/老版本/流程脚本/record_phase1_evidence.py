import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
CODE = Path(ROOT) / "Transformer-Koopman" / "训练代码"

DELIVERABLES = [
    "Transformer-Koopman/训练代码/pyproject.toml",
    "Transformer-Koopman/训练代码/requirements.txt",
    "Transformer-Koopman/训练代码/configs/platform1.yaml",
    "Transformer-Koopman/训练代码/configs/platform2.yaml",
    "Transformer-Koopman/训练代码/scripts/prepare_data.py",
    "Transformer-Koopman/训练代码/scripts/smoke_train.py",
    "Transformer-Koopman/训练代码/tests/conftest.py",
    "Transformer-Koopman/训练代码/tests/test_imports.py",
    "Transformer-Koopman/训练代码/tests/test_data_contract.py",
    "Transformer-Koopman/训练代码/tests/test_config_contract.py",
]
file_hashes = {}
for rel in DELIVERABLES:
    p = Path(ROOT) / rel
    file_hashes[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
print("hashed", len(file_hashes), "deliverables")

VB = {"git_commit": None, "diff_hash": None, "file_hashes": file_hashes}


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
    note = "" if ok else " -> " + r.stderr.decode("utf-8", "replace").strip()[:200]
    print(f"  {'OK  ' if ok else 'FAIL'} {label}{note}")


print("\n== evidence: code migration ==")
apply("evidence.record", {
    "id": "EV-PHASE1-MIGRATE-001", "kind": "artifact",
    "subject": "代码迁移：31 个 .py 模块 + platform1/2.yaml + requirements.txt + .gitignore，全部与老仓库字节相同",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"],
               "files": [r for r in DELIVERABLES]},
    "version_binding": VB}, "t13-ev-mig", "EV-PHASE1-MIGRATE-001")

print("\n== evidence: data adapter reproduces legacy data ==")
apply("evidence.record", {
    "id": "EV-PHASE1-DATA-001", "kind": "artifact",
    "subject": "数据适配层：P1 输出 x/u/t/trajectory_id 四个数组与老 experiment_001 逐元素相同，且三个 npz 的 sha256 完全相同（train E3BC5252…, val 15A3BD3E…, test 51BDE080…）",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"],
               "files": ["Transformer-Koopman/训练代码/scripts/prepare_data.py"]},
    "version_binding": VB}, "t13-ev-data", "EV-PHASE1-DATA-001")

print("\n== evidence: regression suite ==")
apply("evidence.record", {
    "id": "EV-PHASE1-TESTS-001", "kind": "test",
    "subject": "FIX-10 回归套件骨架：pytest 112 passed / 1 xfailed / 0 failed（xfail 记录 platform2 五项损失缺失的已知缺陷 ALN-001/002）",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"],
               "files": [r for r in DELIVERABLES if "/tests/" in r]},
    "version_binding": VB}, "t13-ev-tests", "EV-PHASE1-TESTS-001")

print("\n== evidence: M1 smoke ==")
apply("evidence.record", {
    "id": "EV-PHASE1-SMOKE-001", "kind": "test",
    "subject": "M1 冒烟：platform1 完整跑通 Stage0 EDMD -> Stage1 预训练(1 epoch) -> Stage2 闭式重拟合 -> Stage3 跳过SVD限制 -> Stage4/5，A=(64,64) B=(64,3) 谱半径 0.999753，train RMSE 0.119457",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"],
               "files": ["Transformer-Koopman/训练代码/scripts/smoke_train.py"]},
    "version_binding": VB}, "t13-ev-smoke", "EV-PHASE1-SMOKE-001")

print("\n== update TASK-002 next_action ==")
apply("task.update", {"task_id": "TASK-002", "implementer": "vibe-main", "owner": "user"},
      "t13-task-upd", "task.update TASK-002")

print("\nfinal revision:", revision())
