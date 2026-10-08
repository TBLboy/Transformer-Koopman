import json, subprocess, sys
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

def revision():
    p = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(p.stdout.decode("utf-8", "replace"))["revision"]

def apply(action, payload, tag):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(),
           "action": action, "payload": payload}
    path = f"{TMP}/env_{tag}.json"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    p = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path], capture_output=True)
    print(("OK   " if p.returncode == 0 else "FAIL ") + tag)
    if p.returncode:
        print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

apply("record.create", {"kind": "decision", "id": "DEC-025",
      "title": "优先级调整：先完成论文理论章节，真机实验推迟",
      "status": "active",
      "payload": {
        "level": "C", "basis": "用户明确指令（2026-10-06）",
        "decision": "不急于 P2 真机。当前阶段目标改为：把论文理论部分（Prop.1/2、Thm.1、Cor.1、Prop.3 正式化 + 理论章节成稿）写好，之后再考虑真机 E1–E5。",
        "consequence": "TASK-004 的 matched oracle/理论路线已 CLOSED；新建 TASK-005 专门负责论文理论章节撰写。真机仍为后续阶段（GO 状态保留，不取消）。",
      }}, "tY0-dec025")

apply("task.create", {"id": "TASK-005", "goal_id": "GOAL-001",
      "title": "论文理论章节撰写：Prop.1/2、Thm.1、Cor.1、Prop.3 正式化与成稿（strict）",
      "extensions": {"implementer": "vibe-main", "owner": "user", "risk_class": "strict"}}, "tY1-task005")
apply("task.begin", {"task_id": "TASK-005"}, "tY2-begin")
print("revision:", revision())
