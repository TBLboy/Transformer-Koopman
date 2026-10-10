import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"


def revision():
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def apply(action, payload, tag):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(), "action": action, "payload": payload}
    p = f"{TMP}/env_{tag}.json"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", p], capture_output=True)
    print(r.stdout.decode("utf-8", "replace"))
    if r.returncode:
        print(r.stderr.decode("utf-8", "replace"))


apply("task.resume", {"task_id": "TASK-004", "next_action": "继续 S1 文献结构化映射与主文献 L2/L4 阅读。"}, "t42-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": "S1 v0.1 已完成初筛：robust tube Koopman MPC、Koopman-CBF、generic residual/adaptive Koopman、history lifting alone、bilinear Koopman alone 均不能作为单独创新。下一步 L2/L4 阅读 Zhang 2022、Folkestad 2021、Singh 2025、CCK source、Korda-Mezic 2018 与 input-dependent Koopman，抽取精确定理/假设/限制，并验证 lifted-reference feasibility / constant-B obstruction。代码继续冻结。"}, "t42-handoff")
print("revision:", revision())
