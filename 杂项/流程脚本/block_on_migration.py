import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"


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
    note = "" if ok else " -> " + r.stderr.decode("utf-8", "replace").strip()[:220]
    print(f"  {'OK  ' if ok else 'FAIL'} {label}{note}")
    return ok


print("== DEC-006 (proposed): target repo baseline + migration fork ==")
apply("record.create", {
    "kind": "decision", "id": "DEC-006",
    "title": "阶段① 代码迁移策略尚未决定：新仓库当前无任何代码", "status": "proposed",
    "payload": {
        "authority": "C",
        "status": "awaiting-user",
        "finding": "目标仓库 Transformer-Koopman 实际内容为空代码：训练代码=0 文件、结果备份=0、杂项=0；仅 数据备份=129 文件、论文=74 文件。git tracked=0，无 .gitignore，仅 2 个未跟踪顶层目录。",
        "implication": "DEC-004 的阶段① 整理代码 无法按 改已有文件 执行；FIX-01..FIX-10 的前置条件是从老仓库迁移代码。",
        "options": [
            "A 迁移后清理：整体拷贝老仓库训练代码到新仓库，再逐项执行 FIX-01..FIX-10。最快得到可验证流水线；缺点是把老结构债（重复 trainer、死代码）先继承再清理。",
            "B 洁净重建：只按已批准契约（REQ-001 + 5 项损失）重写最小包骨架 Data->Dataset->Train->Eval，按需移植必要模块。结构最好；缺点是最容易在无意识中偏离论文方法定义，追溯成本高。",
            "C 混合：核心（model / lifting / trainer）迁移并清理，外层（配置 schema、流水线编排、测试）重写。",
        ],
        "recommendation": "C 混合，且第一步先只迁移到能跑通最小 smoke 的范围（M1 on platform1），把 FIX-10 测试套件建起来作为迁移的安全网，再逐步扩大。",
        "second_question": "是否将 数据备份/ 与 论文/ 加入 .gitignore（二者共 203 个文件，含 5.9MB train_data.mat 等二进制），避免把数据与论文草稿纳入 git 跟踪。",
        "unknowns": "尚未确认用户期望代码在仓库中的最终目录布局（当前 杂项/结果备份 为空且未使用）。"}},
    "t7-dec6", "decision DEC-006")

print("\n== TASK-002 + RUN-002, then block on user decision ==")
apply("task.create", {
    "id": "TASK-002", "title": "阶段① 代码迁移与清理（scope A 第一批 D+A+B，strict）",
    "goal_id": "GOAL-001",
    "extensions": {"implementer": "vibe-main", "owner": "user", "risk_class": "strict"}},
    "t7-task2", "task.create TASK-002")

apply("task.begin", {
    "task_id": "TASK-002", "run_id": "RUN-002",
    "next_action": "阻塞于用户决策 Q-MIGRATE-001：选择代码迁移策略（A 迁移后清理 / B 洁净重建 / C 混合）并确认 .gitignore 处理 数据备份/ 与 论文/"}, "t7-begin2", "task.begin RUN-002")

apply("task.wait", {
    "task_id": "TASK-002", "kind": "user",
    "reason": ("新仓库当前无任何代码（训练代码/结果备份/杂项 均 0 文件），因此 DEC-004 的阶段① 无法按改已有文件执行。"
               "必须先决定迁移策略：(1) 迁移后清理 vs 洁净重建 vs 混合；"
               "(2) 是否将 数据备份/ 与 论文/（共 203 文件，含二进制）加入 .gitignore。"
               "推荐：混合方案并先建立 FIX-10 测试套件作为迁移安全网；建议 ignore 数据与论文草稿。"),
    "resume_when": "用户给出迁移策略选择与 .gitignore 决定",
    "question_ref": "Q-MIGRATE-001"}, "t7-wait2", "task.wait TASK-002")

print("\nfinal revision:", revision())
