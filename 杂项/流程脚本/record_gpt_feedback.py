import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

DOC = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_feedback_v1.md"
sha = hashlib.sha256(DOC.read_bytes()).hexdigest()

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
        print(p.stdout.decode("utf-8", "replace")[:800])
        print(p.stderr.decode("utf-8", "replace")[:1500])

dec = {
    "class": "standard",
    "files_touched": 2,
    "minimum_verification": ["回传稿自包含，含机制级占位、复现数据与下一轮要求"],
    "notes": [
        "选项：①继续在残余空间深挖 ②回传外部构思方重出路线 ③调整阶段②目标 ④暂停先做 DEC-018",
        "用户选择②：回传 GPT 重出路线（符合'验证方只验证+反馈、不构思新路线'约束）",
        "产出：.project-log/docs/phase2_gpt_feedback_v1.md",
    ],
    "reason": "GPT 18 条路线 L3 后无任何一条可作阶段② 主结果；由外部构思方在机制级重构路线，验证方保持不构思",
    "reversible": True,
    "signals": ["conclusion"],
}
apply("record.create", {"kind": "decision", "id": "DEC-019", "status": "active",
      "title": "阶段② 下一步：把 L3 验证反馈回传外部构思方(GPT)重出路线",
      "payload": dec}, "t80-dec019")

next_action = (
    "用户决定（DEC-019）：把 L3 验证反馈回传外部构思方 GPT，要求其以机制级（可证命题/假设）差异重出路线；验证方不构思新路线。"
    "已产出回传稿 phase2_gpt_feedback_v1.md（含 R1–R18 机制级占位、Test A/B/B′/C 复现数据、R16 负面扫描、对下一轮 7 条具体要求）。"
    "下一步：等待 GPT 新路线报告返回后，继续按同法做 L1/L2/L3 验证（先机制级对拍，再便宜证伪实验）。"
    "GOAL-001 门禁仍拒绝完成；DEC-018 未满足。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t80-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t80-handoff")
print("feedback_sha256:", sha)
print("revision:", revision())
