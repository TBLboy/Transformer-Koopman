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
    note = "" if ok else " -> " + r.stderr.decode("utf-8", "replace").strip()[:200]
    print(f"  {'OK  ' if ok else 'FAIL'} {label}{note}")


apply("record.create", {
    "kind": "decision", "id": "DEC-005",
    "title": "修正 GOAL-001 门禁载荷形状并记录两处门禁配置缺口", "status": "active",
    "payload": {
        "authority": "B",
        "decision": "将 GOAL-001 的 success_conditions/required_evidence 由字符串数组改为门禁期望的对象数组（{id,statement,status} / {id,subject,evidence_refs}），status 一律 pending。",
        "rationale": "state_store.py:1136-1138 与 1163-1166 要求每项为对象；字符串会产出 'not an object' 畸形错误而非真实未达成，属埋雷。",
        "gate_gaps": [
            "TASK-001 的 extensions.risk 不可通过 CLI 设置：task.update 仅允许 implementer/owner（state_store.py:1549-1553），任务级高风险独立复核门禁无法由 CLI 启用。",
            "GOAL-001 的 extensions 缺少 implementer/owner：_goal_completion_problems（state_store.py:1196-1213）在 implementer 非字符串时跳过复核人独立性校验，目标级复核独立性目前空转。",
        ],
        "mitigation": "本轮仍以 reviewer != 实现者 真实执行并记录复核；建议后续由用户决定是否为工作流补一个可写 extensions 的受控入口。",
        "status_note": "不影响本轮 TASK-001 的完成判定，TASK-001 完成门禁只要求覆盖它的有效证据。"}},
    "t6-dec5", "decision DEC-005")

print("\nfinal revision:", revision())
