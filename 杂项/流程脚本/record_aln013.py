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

FILES = [f"{C}/README.md", f"{C}/tests/test_ablation_registry.py"]
VB = {"git_commit": None, "diff_hash": None,
      "file_hashes": {f: hashlib.sha256((Path(ROOT) / f).read_bytes()).hexdigest() for f in FILES}}

NEXT = ("FIX-01/03(部分)/04/10 与 ALN-011/013 已完成：ALN-003/006/008/011/013/020 resolved，"
        "ALN-004 部分解决（余 3 项属 ALN-002/阶段②）。下一步：FIX-05..07"
        "（ALN-007/009/010/012/014/015/016/017/018/019 中未处理者），批次二 FIX-08/09")


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


print("== evidence: ALN-013 ==")
apply("evidence.record", {
    "id": "EV-ALN013-001", "kind": "test",
    "subject": "ALN-013 修复：README 删除错误的 PLATFORM_CONFIGS 宣称（该常量实际定义在未迁移的 figures/ablation/plot_ablation.py）；新增 tests/test_ablation_registry.py 守卫注册表 vs 可达集合一致性——ABLATION_MODELS 11 项中 readout_max/readout_last/pure_feature 不可达，按旧仓库 docs/ABLATION_DESIGN.md 属已设计未接线，显式钉住为阶段② 项。套件 165 passed / 2 skipped / 1 xfailed",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES},
    "version_binding": VB}, "t25-ev-aln013", "EV-ALN013-001")

print("\n== ALN-013 -> resolved ==")
apply("record.update", {"kind": "alignment", "id": "ALN-013",
                        "expected_record_revision": rec_rev("ALN-013"), "status": "resolved"},
      "t25-aln013", "ALN-013 -> resolved")

print("\n== refresh next_action ==")
apply("task.handoff", {"task_id": "TASK-002", "next_action": NEXT}, "t25-handoff", "task.handoff")
apply("task.resume", {"task_id": "TASK-002", "next_action": NEXT}, "t25-resume", "task.resume")

print("\nfinal revision:", revision())
