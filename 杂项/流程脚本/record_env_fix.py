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
    "Transformer-Koopman/训练代码/pyproject.toml",
    "Transformer-Koopman/训练代码/scripts/smoke_test.py",
    "Transformer-Koopman/训练代码/scripts/smoke_train.py",
    "Transformer-Koopman/训练代码/tests/conftest.py",
]
VB = {"git_commit": None, "diff_hash": None,
      "file_hashes": {f: hashlib.sha256((Path(ROOT) / f).read_bytes()).hexdigest() for f in FILES}}

NEXT = ("FIX-01/04/10 已完成（ALN-003/006/008 resolved），deploy/ 与 src/patchtst_koopman/ablation/ "
        "已补齐迁移（EV-PHASE1-MIGRATE-002），editable 安装已重指向新仓库（ALN-020 resolved）。"
        "下一步：FIX-03 配置键读写收敛（ALN-004/005）、FIX-05..07，批次二 FIX-08/09")


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


def rec_rev(rid):
    c = sqlite3.connect(DB)
    row = c.execute("SELECT revision FROM records WHERE id=?", (rid,)).fetchone()
    c.close()
    return row[0]


print("== evidence: editable install repointed ==")
apply("evidence.record", {
    "id": "EV-PHASE1-ENV-001", "kind": "test",
    "subject": "ALN-020 修复：在 训练代码/ 执行 pip install -e . --no-deps --no-build-isolation，editable 安装由旧副本 D:\\Project\\code-projectv2 重指向新仓库。验证：无 sys.path 干预时 import patchtst_koopman 解析到 训练代码\\src\\patchtst_koopman；pip show Editable project location = 训练代码；pytest 141 passed / 2 skipped / 1 xfailed；smoke_train.py PASS（rho=0.999753）；smoke_test.py 4/4 通过",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES},
    "version_binding": VB}, "t19-ev-env", "EV-PHASE1-ENV-001")

print("\n== ALN-020 -> resolved ==")
apply("record.update", {"kind": "alignment", "id": "ALN-020",
                        "expected_record_revision": rec_rev("ALN-020"), "status": "resolved"},
      "t19-aln020", "ALN-020 -> resolved")

print("\n== refresh next_action ==")
apply("task.handoff", {"task_id": "TASK-002", "next_action": NEXT}, "t19-handoff", "task.handoff")
apply("task.resume", {"task_id": "TASK-002", "next_action": NEXT}, "t19-resume", "task.resume")

print("\nfinal revision:", revision())
