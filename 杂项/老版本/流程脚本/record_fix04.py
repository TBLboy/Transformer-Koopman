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
    "Transformer-Koopman/训练代码/README.md",
    "Transformer-Koopman/训练代码/run_all_training.bat",
    "Transformer-Koopman/训练代码/run_all_training.ps1",
    "Transformer-Koopman/训练代码/scripts/inspect_ckpt.py",
    "Transformer-Koopman/训练代码/scripts/check_model_prediction.py",
    "Transformer-Koopman/训练代码/scripts/smoke_test.py",
    "Transformer-Koopman/训练代码/scripts/test_platform2_pth.py",
    "Transformer-Koopman/训练代码/tests/test_no_hardcoded_paths.py",
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
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:200]))


def rec_rev(rid):
    c = sqlite3.connect(DB)
    row = c.execute("SELECT revision FROM records WHERE id=?", (rid,)).fetchone()
    c.close()
    return row[0]


print("== evidence: FIX-04 ==")
apply("evidence.record", {
    "id": "EV-FIX04-001", "kind": "test",
    "subject": "FIX-04 修复：清除 4 处硬编码机器路径（run_all_training.bat 用 %~dp0、.ps1 用 $PSScriptRoot、inspect_ckpt.py 与 check_model_prediction.py 改 argparse），README 与两处 docstring 去除旧项目名，新增 tests/test_no_hardcoded_paths.py 守卫。套件 140 passed / 2 skipped / 1 xfailed；inspect_ckpt 合成 checkpoint 通过、缺文件干净报错；.ps1 PARSE OK",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES},
    "version_binding": VB}, "t16-ev-fix04", "EV-FIX04-001")

print("\n== resolve ALN-006 (FIX-04) and ALN-008 (FIX-10) ==")
apply("record.update", {"kind": "alignment", "id": "ALN-006",
                        "expected_record_revision": rec_rev("ALN-006"), "status": "resolved"},
      "t16-aln006", "ALN-006 -> resolved")
apply("record.update", {"kind": "alignment", "id": "ALN-008",
                        "expected_record_revision": rec_rev("ALN-008"), "status": "resolved"},
      "t16-aln008", "ALN-008 -> resolved")

print("\n== ALN-019: persist the FIX<->ALN mapping (traceability gap) ==")
apply("record.create", {
    "id": "ALN-019", "kind": "alignment", "status": "open",
    "title": "FIX-01..FIX-10 工作清单只存在于会话上下文，未落库（traceability gap）",
    "payload": {
        "category": "traceability-gap",
        "observation": "TASK-002 的 next_action 反复引用 FIX-01..FIX-10，但任何记录（task/decision/alignment）都未定义该清单；它只存在于会话上下文与 next_action 字符串中。",
        "impact": "换会话或换机器后无法重建工作清单，只能从 ALN 记录反推。",
        "recovered_mapping": {
            "FIX-01": "ALN-003 run_all 调度 LSTM x platform2 缺 lstm_koopman 段（已 resolved）",
            "FIX-02": "ALN-001/ALN-002 platform2 五项损失缺失（阶段② 处理，当前 xfail 记录）",
            "FIX-03": "ALN-004/ALN-005 配置键读写不一致（KNOWN_UNREAD 已钉住，待收敛）",
            "FIX-04": "ALN-006 硬编码机器绝对路径（已 resolved）",
            "FIX-10": "ALN-008 无可机器判定的回归信号（已 resolved，tests/ + pytest 配置就位）",
            "FIX-05..09": "对应 ALN-007/009/010/011/012/013/014/015/016/017/018 中尚未处理者，编号映射未落库",
        },
        "authoritative_source": "ALN-001..ALN-018 是缺陷的权威清单；FIX 编号只是派生的工作分层。",
        "recommended_action": "后续以 ALN 记录为准推进；如需保留 FIX 编号，应把完整清单写入一条 decision 记录。",
    }}, "t16-aln019", "ALN-019 created")

print("\nfinal revision:", revision())
