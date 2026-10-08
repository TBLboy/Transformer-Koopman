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
DOC = ".project-log/docs/business-logic/clarification.yaml"
DOC_SHA = "39de4ac263088864d65c75f27a2df036767bbc9905c3c8da68579d6ffad95349"

NEXT = ("ALN-019 已 resolved（FIX 编号退役，工作清单以 ALN 记录为权威，DEC-013 落库）。"
        "下一步：ALN-007（MATLAB 死接口）/ ALN-012（孤儿数据目录）/ ALN-014（中文路径扫描）"
        "三项阶段① 清理；ALN-001/002/015/016/017/018 与 ALN-010 残余属阶段②")

DEC_PAYLOAD = {
    "decision": "工作清单以 ALN 记录为权威；FIX-01..10 编号退役，仅作为历史别名保留",
    "rationale": (
        "ALN-019 记录：TASK-002 的 next_action 反复引用 FIX-01..FIX-10，但没有任何记录定义该清单，"
        "它只存在于会话上下文与 next_action 字符串中，换会话/换机器后无法重建。"
        "ALN-001..ALN-020 是缺陷的权威清单，FIX 编号只是派生的工作分层。"
    ),
    "recovered_mapping": {
        "FIX-01": "ALN-003 run_all 调度 LSTM x platform2 缺 lstm_koopman 段（resolved）",
        "FIX-02": "ALN-001/ALN-002 platform2 五项损失缺失（阶段②，当前 xfail 记录）",
        "FIX-03": "ALN-004/ALN-005 配置键读写不一致（ALN-005 resolved；ALN-004 残余属阶段②）",
        "FIX-04": "ALN-006 硬编码机器绝对路径（resolved）",
        "FIX-05": "ALN-007 MATLAB 适配器期望的 checkpoint 格式无人写入（阶段① 待处理）",
        "FIX-06": "ALN-012 data/experiment_002..005 孤儿数据目录用途不明（阶段① 待处理）",
        "FIX-07": "ALN-014 中文路径/文件名工具链隐患（阶段① 待处理）",
        "FIX-08": "ALN-015 稳定性不变量 INV1 被违反（阶段② 方法论）",
        "FIX-09": "ALN-016/ALN-017/ALN-018 损失语义与论文谱系（阶段② 方法论）",
        "FIX-10": "ALN-008 无可机器判定的回归信号（resolved，tests/ + pytest 就位）",
    },
    "mapping_caveat": (
        "FIX-05..09 的原始编号映射未落库、不可精确恢复；上表是按 ALN 类别与阶段归属的重建，"
        "仅作历史别名参考，不作为权威。"
    ),
    "remaining_work_by_phase": {
        "阶段①（代码整理，本阶段）": [
            "ALN-007 MATLAB 死接口：实现或删除/文档化",
            "ALN-012 孤儿数据目录：查明用途或标记为不迁移",
            "ALN-014 中文路径：扫描并显式接受或修复",
        ],
        "阶段②（理论方法讨论）": [
            "ALN-001/ALN-002 platform2 五项损失补键与定值",
            "ALN-015 INV1 稳定性机制统一",
            "ALN-016 MLP/LSTM consistency 语义对齐",
            "ALN-017 论文谱系收敛",
            "ALN-018 多步损失归约（mean vs sum）",
            "ALN-010 残余：部署侧模型栈副本一致性测试",
        ],
        "阶段③（重训）": [
            "ALN-009 论文数字与产生它们的配置绑定",
        ],
    },
    "level": "B",
    "decided_by": "vibe-main",
}

ALN019_PAYLOAD = {
    "category": "traceability-gap",
    "observation": (
        "TASK-002 的 next_action 反复引用 FIX-01..FIX-10，但任何记录（task/decision/alignment）"
        "都未定义该清单；它只存在于会话上下文与 next_action 字符串中。"
    ),
    "impact": "换会话或换机器后无法重建工作清单，只能从 ALN 记录反推。",
    "authoritative_source": "ALN-001..ALN-020 是缺陷的权威清单；FIX 编号只是派生的工作分层。",
    "recommended_action": "后续以 ALN 记录为准推进；如需保留 FIX 编号，应把完整清单写入一条 decision 记录。",
    "status_note": "resolved",
    "resolution": (
        "已按 recommended_action 落库：DEC-013 记录 FIX-01..10 的历史别名映射（含不可精确恢复的说明）"
        "与按阶段划分的剩余工作清单。此后 next_action 与推进一律以 ALN 记录为准，FIX 编号退役。"
    ),
    "doc_ref": {"path": DOC, "sha256": DOC_SHA},
}


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


print("== decision DEC-013 ==")
apply("record.create", {"kind": "decision", "id": "DEC-013",
                        "title": "工作清单以 ALN 记录为权威，FIX 编号退役（ALN-019）",
                        "status": "active", "payload": DEC_PAYLOAD},
      "t32-dec013", "DEC-013")

print("\n== ALN-019 -> resolved ==")
apply("record.update", {"kind": "alignment", "id": "ALN-019",
                        "expected_record_revision": rec_rev("ALN-019"),
                        "status": "resolved", "payload": ALN019_PAYLOAD},
      "t32-aln019", "ALN-019")

print("\n== refresh next_action ==")
apply("task.handoff", {"task_id": "TASK-002", "next_action": NEXT}, "t32-handoff", "task.handoff")
apply("task.resume", {"task_id": "TASK-002", "next_action": NEXT}, "t32-resume", "task.resume")

print("\nfinal revision:", revision())
