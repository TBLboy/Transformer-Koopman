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
DOC = ".project-log/docs/business-logic/clarification.yaml"
DOC_SHA = "39de4ac263088864d65c75f27a2df036767bbc9905c3c8da68579d6ffad95349"

NEXT = ("阶段① 代码整理全部 ALN 已处理：ALN-003/005/006/007/008/011/012/013/019/020 resolved，"
        "ALN-014 accepted（中文目录名经 DEC-014 接受），ALN-004 partially-resolved。"
        "剩余 ALN-001/002/004残余/009/010残余/015/016/017/018 属阶段②/③（理论方法讨论与重训）。"
        "下一步：阶段① 收尾——运行 vibe goal 门禁评估 GOAL-001 是否可完成，或转入阶段②。")

DEC_PAYLOAD = {
    "decision": "新项目保留中文目录名（数据备份/论文/结果备份/训练代码/杂项），仅修复脚本层硬编码；ALN-014 记为已接受权衡",
    "rationale": (
        "用户决策（OQ-001）：保持中文目录名。DEC-008/DEC-010 已按中文名锁定仓库布局，"
        "Windows 下工具链正常；全量改 ASCII 需重命名目录并同步 configs/README/.gitignore，"
        "改动面大且需修订已批准决策。ALN-014 的原始验收『非 ASCII 路径扫描断言为 0』不可达，"
        "改为『无中文 Python 标识符 + 中文目录名经决策接受』。"
    ),
    "alternatives": [
        "全部改 ASCII（数据备份→data_backup 等）——改动面大、需修订 DEC-008/DEC-010，否决",
        "只改代码层并集中路径常量——收益有限，否决",
    ],
    "consequences": [
        "保留 5 个中文顶层目录及其子目录、论文/草稿 下 4 个中文 .tex 文件名",
        "scripts/test_platform2_pth.py 的硬编码 平台2.pth 改为 argparse（--checkpoint/--save-dir），默认值仍指向旧产物",
        "新增 tests/test_ascii_identifiers.py：tokenize 扫描断言无中文 Python 标识符；钉住已接受的中文顶层目录集合",
        "ALN-014 状态 accepted（非 resolved）",
    ],
    "level": "C",
    "decided_by": "user",
}

ALN014_PAYLOAD = {
    "class": "constraint-conflict",
    "doc_ref": {"path": DOC, "sha256": DOC_SHA},
    "status_note": "accepted",
    "resolution": (
        "用户决策（OQ-001 / DEC-014）：保留中文目录名，接受该权衡。"
        "扫描结果：非 ASCII 顶层目录 5 个（数据备份/论文/结果备份/训练代码/杂项）+ 子目录（机械臂数据/软体平台数据/"
        "原始数据/处理后的数据/论文草稿）+ 4 个中文 .tex 文件名；中文 Python 标识符 0 个。"
        "修复：scripts/test_platform2_pth.py 的硬编码 平台2.pth 改为 argparse（--checkpoint/--save-dir）。"
        "新增 tests/test_ascii_identifiers.py（2 项：tokenize 断言无中文标识符、钉住已接受的中文顶层目录集合）。"
        "验收改为『无中文 Python 标识符 + 中文目录名经决策接受』。套件 220 passed / 2 skipped / 1 xfailed。"
        "证据 EV-ALN014-001。"
    ),
    "subject": "中文路径/文件名造成的工具链隐患",
}

FILES = [
    f"{C}/scripts/test_platform2_pth.py",
    f"{C}/tests/test_ascii_identifiers.py",
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
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:400]))


def rec_rev(rid):
    c = sqlite3.connect(DB)
    row = c.execute("SELECT revision FROM records WHERE id=?", (rid,)).fetchone()
    c.close()
    return row[0]


print("== decision DEC-014 ==")
apply("record.create", {"kind": "decision", "id": "DEC-014",
                        "title": "ALN-014：保留中文目录名，仅修脚本硬编码（用户决策 C）",
                        "status": "active", "payload": DEC_PAYLOAD},
      "t34-dec014", "DEC-014")

print("\n== evidence EV-ALN014-001 ==")
apply("evidence.record", {
    "id": "EV-ALN014-001", "kind": "test",
    "subject": (
        "ALN-014 处理：保留中文目录名（DEC-014），修复脚本层硬编码。"
        "scripts/test_platform2_pth.py 的模块级硬编码 平台2.pth 改为 argparse（--checkpoint/--save-dir，"
        "默认值仍指向旧产物）；新增 tests/test_ascii_identifiers.py（2 项：tokenize 扫描断言无中文 Python 标识符、"
        "钉住已接受的中文顶层目录集合 {数据备份,论文,结果备份,训练代码,杂项}）。"
        "扫描：中文顶层目录 5 + 子目录若干 + 4 个中文 .tex 文件名；中文 Python 标识符 0。"
        "套件 220 passed / 2 skipped / 1 xfailed。"
    ),
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES},
    "version_binding": VB}, "t34-ev-aln014", "EV-ALN014-001")

print("\n== ALN-014 -> accepted ==")
apply("record.update", {"kind": "alignment", "id": "ALN-014",
                        "expected_record_revision": rec_rev("ALN-014"),
                        "status": "accepted", "payload": ALN014_PAYLOAD},
      "t34-aln014", "ALN-014")

print("\n== refresh next_action ==")
apply("task.handoff", {"task_id": "TASK-002", "next_action": NEXT}, "t34-handoff", "task.handoff")
apply("task.resume", {"task_id": "TASK-002", "next_action": NEXT}, "t34-resume", "task.resume")

print("\nfinal revision:", revision())
