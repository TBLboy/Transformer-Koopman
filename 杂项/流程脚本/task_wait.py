import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"


def revision() -> int:
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


envelope = {
    "schema_version": 1,
    "command_id": "t009-task-wait",
    "expected_revision": revision(),
    "action": "task.wait",
    "payload": {
        "task_id": "TASK-001",
        "kind": "user",
        "reason": "需要用户裁决多步损失在双平台的统一策略；该决策影响 platform2 是否重训与论文数字，属 C 级结论性选择",
        "question_ref": "Q-MULTISTEP-UNIFY-001",
        "resume_when": "用户答复多步损失统一策略后，继续业务澄清与功能/技术双向对齐",
    },
}
path = f"{TMP}/env_t009_task_wait.json"
open(path, "w", encoding="utf-8", newline="\n").write(
    json.dumps(envelope, ensure_ascii=False, indent=2)
)
r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path],
                   capture_output=True)
out = r.stdout.decode("utf-8", "replace").strip()
err = r.stderr.decode("utf-8", "replace").strip()
print("rc:", r.returncode)
if r.returncode == 0:
    print(out)
else:
    print("STDERR:", err)
    print("STDOUT:", out)
