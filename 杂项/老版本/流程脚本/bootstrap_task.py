import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

SUCCESS = json.load(open(f"{TMP}/goal001_conditions.json", encoding="utf-8"))
EVIDENCE = json.load(open(f"{TMP}/goal001_evidence.json", encoding="utf-8"))
DEC = json.load(open(f"{TMP}/dec001.json", encoding="utf-8"))


def revision() -> int:
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def apply(action: str, payload: dict, tag: str) -> dict:
    envelope = {
        "schema_version": 1,
        "command_id": tag,
        "expected_revision": revision(),
        "action": action,
        "payload": payload,
    }
    path = f"{TMP}/env_{tag}.json"
    open(path, "w", encoding="utf-8", newline="\n").write(
        json.dumps(envelope, ensure_ascii=False, indent=2)
    )
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path],
                       capture_output=True)
    out = r.stdout.decode("utf-8", "replace").strip()
    err = r.stderr.decode("utf-8", "replace").strip()
    print(f"--- {tag} [{action}] rc={r.returncode}")
    print(f"    {out or err}")
    return json.loads(out) if out.startswith("{") else {}


apply("goal.create", {
    "id": "GOAL-001",
    "title": "把杂乱的老研究项目重构为干净的新版本（Transformer-Koopman）",
    "extensions": {"risk_level": "high"},
}, "t001-goal-create")

apply("goal.update", {
    "id": "GOAL-001",
    "success_conditions": SUCCESS,
    "required_evidence": EVIDENCE,
}, "t002-goal-update")

apply("task.create", {
    "id": "TASK-001",
    "title": "澄清重构的功能业务逻辑与技术业务逻辑（strict）",
    "goal_id": "GOAL-001",
    "extensions": {"risk_class": "strict"},
}, "t003-task-create")

apply("task.begin", {
    "task_id": "TASK-001",
    "run_id": "RUN-001",
    "next_action": "向用户提出重构保真度契约问题（C 级）：忠实重构 vs 允许修正已知缺陷 vs 允许方法论升级",
}, "t004-task-begin")

apply("task.update", {
    "task_id": "TASK-001",
    "implementer": "vibe-main",
    "owner": "user",
}, "t005-task-update")

apply("record.create", {
    "kind": "decision",
    "id": "DEC-001",
    "title": "本次重构任务按 strict 风险等级执行",
    "status": "active",
    "payload": DEC,
}, "t006-dec001")

print()
print("final revision:", revision())
