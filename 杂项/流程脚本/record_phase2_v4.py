import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"


def rev():
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def apply(action, payload, tag):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": rev(), "action": action, "payload": payload}
    p = f"{TMP}/env_{tag}.json"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", p], capture_output=True)
    print(("OK   " if r.returncode == 0 else "FAIL ") + tag)
    if r.returncode:
        print(r.stderr.decode("utf-8", "replace")[:1000])


payload = {
    "status": "complete",
    "documents": [
        ".project-log/docs/phase2_idea_screening_v0.3.md",
        ".project-log/docs/phase2_idea_population_v0.4.md",
        ".project-log/docs/phase2_d1_minimal_check.md",
        ".project-log/docs/phase2_branch_status_v0.4.md",
    ],
    "branch_status": {
        "I1": "killed: simulation preorder prior art",
        "I2": "killed: output controllability/reference governor plus control-aware embedding prior art",
        "I3": "killed unless a genuinely different obstruction and theorem is found; CCK covers generic actuator virtual dynamics",
        "M6": "deferred/likely killed standalone: MZ/memory Koopman prior art and full-state-measured project assumption",
        "D1": "exploratory-blocked: dissipativity/passivity route lacks confirmed physical supply-rate semantics for P1/P2",
    },
    "research_result": "No final innovation route has passed all prior-art and theory gates yet. This is a valid research result; do not promote candidate count into novelty.",
    "next": "Confirm P1/P2 state/input physical semantics. If no real supply rate exists, kill D1. Then regenerate candidates using structure constraints that do not depend on unverified energy semantics: input/output operator factorization, task-conditioned control-relevant subspaces, or verifiable observables.",
}

apply("record.create", {"kind": "research", "id": "PHASE2-SCREEN-003", "title": "阶段② 分支淘汰与 D1 门禁", "status": "complete", "payload": payload}, "t44-screen")
apply("task.resume", {"task_id": "TASK-004", "next_action": "已完成 I1/I2/M6 的 prior-art 淘汰或降级；D1 dissipativity route 因 P1/P2 physical supply semantics 未确认而 blocked。下一步确认两平台状态/输入物理语义；若不能定义真实 supply rate 则 kill D1，再生成不依赖未验证能量语义的结构候选。代码继续冻结。"}, "t44-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": "已完成 I1/I2/M6 的 prior-art 淘汰或降级；D1 dissipativity route 因 P1/P2 physical supply semantics 未确认而 blocked。下一步确认两平台状态/输入物理语义；若不能定义真实 supply rate 则 kill D1，再生成不依赖未验证能量语义的结构候选。代码继续冻结。"}, "t44-handoff")
print("revision:", rev())
