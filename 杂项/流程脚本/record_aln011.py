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
C = "Transformer-Koopman/训练代码"

FILES = [
    f"{C}/src/patchtst_koopman/models/mlp_koopman_model.py",
    f"{C}/src/patchtst_koopman/models/lstm_koopman_model.py",
    f"{C}/src/patchtst_koopman/training/performance.py",
    f"{C}/scripts/ablation/train_ablation.py",
    f"{C}/scripts/experiment4/train_experiment4.py",
    f"{C}/tests/test_config_immutability.py",
]
VB = {"git_commit": None, "diff_hash": None,
      "file_hashes": {f: hashlib.sha256((Path(ROOT) / f).read_bytes()).hexdigest() for f in FILES}}

NEXT = ("FIX-01/03(部分)/04/10 与 ALN-011 已完成：ALN-003/006/008/011/020 resolved，ALN-004 部分解决"
        "（余 3 项属 ALN-002/阶段②）。下一步：FIX-05..07（ALN-007/009/010/012/013/014/015/016/017/018 中未处理者），"
        "批次二 FIX-08/09")


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


print("== evidence: ALN-011 ==")
apply("evidence.record", {
    "id": "EV-ALN011-001", "kind": "test",
    "subject": "ALN-011 修复：MLPKoopmanModel/LSTMKoopmanModel 的 _patch_config 改为 _patched_config（deepcopy 后打补丁，沿用 ablation/models.py 既有模式）；apply_gpu_training_defaults 改为返回副本并同步更新两个忽略返回值的调用方。验证：platform2 上 encoder.latent_dim 保持文件值 10 而 MLP/LSTM 模型内部 koopman.d=8；配置序列化前后一致；新增 tests/test_config_immutability.py（9 项）；套件 161 passed / 2 skipped / 1 xfailed；smoke_train PASS、smoke_test 4/4",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES},
    "version_binding": VB}, "t23-ev-aln011", "EV-ALN011-001")

print("\n== ALN-011 -> resolved ==")
apply("record.update", {"kind": "alignment", "id": "ALN-011",
                        "expected_record_revision": rec_rev("ALN-011"), "status": "resolved"},
      "t23-aln011", "ALN-011 -> resolved")

print("\n== refresh next_action ==")
apply("task.handoff", {"task_id": "TASK-002", "next_action": NEXT}, "t23-handoff", "task.handoff")
apply("task.resume", {"task_id": "TASK-002", "next_action": NEXT}, "t23-resume", "task.resume")

print("\nfinal revision:", revision())
