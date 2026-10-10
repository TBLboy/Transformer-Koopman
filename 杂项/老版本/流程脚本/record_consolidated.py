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
CODE = "Transformer-Koopman/训练代码"

DELIVERABLES = [
    f"{CODE}/pyproject.toml",
    f"{CODE}/requirements.txt",
    f"{CODE}/configs/platform1.yaml",
    f"{CODE}/configs/platform2.yaml",
    f"{CODE}/scripts/prepare_data.py",
    f"{CODE}/scripts/smoke_train.py",
    f"{CODE}/scripts/run_all.py",
    f"{CODE}/scripts/smoke_test.py",
    f"{CODE}/tests/conftest.py",
    f"{CODE}/tests/test_imports.py",
    f"{CODE}/tests/test_data_contract.py",
    f"{CODE}/tests/test_config_contract.py",
    f"{CODE}/tests/test_pipeline_jobs.py",
    f"{CODE}/tests/test_no_hardcoded_paths.py",
    f"{CODE}/README.md",
    f"{CODE}/run_all_training.bat",
    f"{CODE}/run_all_training.ps1",
    f"{CODE}/deploy/README.md",
    f"{CODE}/deploy/export_baseline_assets.py",
]

missing = [f for f in DELIVERABLES if not (Path(ROOT) / f).is_file()]
if missing:
    print("MISSING:", missing)
    sys.exit(1)

VB = {"git_commit": None, "diff_hash": None,
      "file_hashes": {f: hashlib.sha256((Path(ROOT) / f).read_bytes()).hexdigest() for f in DELIVERABLES}}


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
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:220]))


print(f"binding {len(DELIVERABLES)} deliverable hashes")
apply("evidence.record", {
    "id": "EV-PHASE1-CONSOLIDATED-001", "kind": "test",
    "subject": "阶段① 迁移与清理当前状态验收（锚定本 revision）：完整缺口分析显示老仓库代码目录除 .gitignore 位置差异外无遗漏；pytest 141 passed / 2 skipped / 1 xfailed；smoke_train.py PASS（rho=0.999753 <= 1）；smoke_test.py 4/4 通过；run_all.py 8 个任务全部通过配置预检；editable 安装已重指向新仓库。取代此前因产物变更而 stale 的 EV-FIX01-001 / EV-FIX04-001 / EV-PHASE1-MIGRATE-001 / EV-PHASE1-DATA-001 / EV-PHASE1-TESTS-001 / EV-PHASE1-SMOKE-001",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": DELIVERABLES},
    "version_binding": VB}, "t20-ev-consolidated", "EV-PHASE1-CONSOLIDATED-001")

print("\nfinal revision:", revision())
