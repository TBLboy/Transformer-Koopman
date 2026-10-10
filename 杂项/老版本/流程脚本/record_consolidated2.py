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
C = "Transformer-Koopman/训练代码"

DELIVERABLES = [
    f"{C}/pyproject.toml", f"{C}/requirements.txt",
    f"{C}/configs/platform1.yaml", f"{C}/configs/platform2.yaml",
    f"{C}/scripts/prepare_data.py", f"{C}/scripts/smoke_train.py",
    f"{C}/scripts/run_all.py", f"{C}/scripts/smoke_test.py",
    f"{C}/scripts/ablation/train_ablation.py",
    f"{C}/scripts/experiment4/train_experiment4.py",
    f"{C}/tests/conftest.py", f"{C}/tests/test_imports.py",
    f"{C}/tests/test_data_contract.py", f"{C}/tests/test_config_contract.py",
    f"{C}/tests/test_pipeline_jobs.py", f"{C}/tests/test_no_hardcoded_paths.py",
    f"{C}/tests/test_config_immutability.py",
    f"{C}/src/patchtst_koopman/models/mlp_koopman_model.py",
    f"{C}/src/patchtst_koopman/models/lstm_koopman_model.py",
    f"{C}/src/patchtst_koopman/training/performance.py",
    f"{C}/README.md", f"{C}/run_all_training.bat", f"{C}/run_all_training.ps1",
    f"{C}/deploy/README.md", f"{C}/deploy/export_baseline_assets.py",
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
    "id": "EV-PHASE1-CONSOLIDATED-002", "kind": "test",
    "subject": "阶段① 迁移与清理当前状态验收（锚定本 revision，取代 EV-PHASE1-CONSOLIDATED-001 等 stale 记录）：完整缺口分析无遗漏；pytest 161 passed / 2 skipped / 1 xfailed；smoke_train.py PASS（rho=0.999753）；smoke_test.py 4/4；run_all.py 8 任务预检全过；ALN-003/006/008/011/020 resolved，ALN-004 partially-resolved；editable 安装已重指向新仓库",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": DELIVERABLES},
    "version_binding": VB}, "t24-ev-consolidated2", "EV-PHASE1-CONSOLIDATED-002")

print("\nfinal revision:", revision())
