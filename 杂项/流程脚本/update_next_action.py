import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

NEXT = ("FIX-01/04/10 已完成（ALN-003/006/008 resolved），deploy/ 与 src/patchtst_koopman/ablation/ "
        "已补齐迁移（EV-PHASE1-MIGRATE-002）。下一步：FIX-03 配置键读写收敛（ALN-004/005）、"
        "FIX-05..07，批次二 FIX-08/09；并待用户决定是否重指向 edmddl2 的 editable 安装（ALN-020）")


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
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:220]))


apply("task.handoff", {"task_id": "TASK-002", "next_action": NEXT}, "t18-handoff", "task.handoff")
apply("task.resume", {"task_id": "TASK-002", "next_action": NEXT}, "t18-resume", "task.resume")
print("\nfinal revision:", revision())
