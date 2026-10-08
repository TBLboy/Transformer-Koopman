import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

CANCEL_REASON = (
    "用户重新定义阶段②：论文理论路线未定稿，代码也非最终版，二者对齐不再是重点；"
    "损失契约定值推迟到理论路线确定之后。TASK-003 的对齐产出（PAPER-ALIGN-001）保留为输入，"
    "任务本身被 TASK-004（理论路线重构）取代。"
)

NEXT = (
    "阶段② 重新界定为『论文理论路线重构』：建模 + 控制器两块，重点在控制器。"
    "目标：构思新理论路线与 idea -> 排除筛选 -> 找到更具创新性与理论性的路线 -> 最后落地代码。"
    "代码暂时冻结。下一步：确认理论重构的自由度与目标定位，然后开始诊断现有理论的薄弱点并生成候选路线。"
)


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


print("== cancel TASK-003 ==")
apply("task.cancel", {"task_id": "TASK-003", "reason": CANCEL_REASON}, "t37-cancel003", "task.cancel")

print("\n== create TASK-004 ==")
apply("task.create", {"id": "TASK-004",
                      "title": "阶段② 论文理论路线重构：建模与控制器的新理论构思与筛选（strict）",
                      "goal_id": "GOAL-001",
                      "extensions": {"implementer": "vibe-main", "owner": "user", "risk_class": "strict"}},
      "t37-task004", "TASK-004")

print("\n== begin RUN-004 ==")
apply("task.begin", {"task_id": "TASK-004", "run_id": "RUN-004", "next_action": NEXT},
      "t37-begin", "task.begin")

print("\nfinal revision:", revision())
