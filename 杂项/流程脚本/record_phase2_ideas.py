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


def apply(action, payload, tag, label):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(), "action": action, "payload": payload}
    p = f"{TMP}/env_{tag}.json"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", p], capture_output=True)
    print(("OK   " if r.returncode == 0 else "FAIL ") + label)
    if r.returncode:
        print(r.stderr.decode("utf-8", "replace")[:1000])


payload = {
    "status": "complete",
    "documents": [
        ".project-log/docs/phase2_idea_population_v0.2.md",
        ".project-log/docs/phase2_theory_feasibility_t0_t2.md",
    ],
    "prior_art_boundary": [
        "CCK structure manufacturing is itself prior art: Asada CDC 2024 and L-CSS 2025.",
        "Therefore actuator virtual dynamics cannot be copied as the central contribution.",
        "Robust tube Koopman MPC, Koopman-CBF, generic adaptive/residual Koopman are already occupied directions.",
    ],
    "candidate_branches": [
        "I1 control-aware approximate Koopman abstraction",
        "I2 reference-compatible controllable lifting",
        "I3 history-induced dynamic extension for control coherence",
        "I4 stabilizable-output Koopman control",
        "I5 Koopman-specific certified reference projection",
    ],
    "mathematical_checks": {
        "T0": "passed: pseudoinverse feedforward error includes -(I-BB†)(z_ref_next-A z_ref)",
        "T1": "unresolved: must distinguish a Koopman-specific feasible lifting from ordinary linear reference governor",
        "T2": "passed as correction tool: Lyapunov metric gives a valid ISS/UUB expression, but is not novel alone",
    },
    "current_recommendation": "Keep I1+I2 as the only active combined branch. Do not implement yet. First test whether reference-compatible lifting yields a new Koopman-specific feasibility condition and physical-output theorem; otherwise kill the branch.",
    "next": "Construct and analyze the minimal finite-dimensional T1 problem, compare exactly against ordinary reference governor/controllability decomposition, and audit CCK 2024/2025 for overlap.",
}

apply("record.create", {"kind": "research", "id": "PHASE2-IDEAS-002", "title": "阶段② 结构性理论路线候选与 T0-T2 检查", "status": "complete", "payload": payload}, "t43-ideas-record", "PHASE2-IDEAS-002")
apply("task.resume", {"task_id": "TASK-004", "next_action": "S1 已确认 CCK actuator virtual dynamics 及 robust/CBF/adaptive 方向已有先例。当前仅保留 I1+I2：control-aware approximate Koopman abstraction + reference-compatible controllable lifting。下一步构造最小 T1 问题，严格与普通 reference governor/controllability decomposition 对比，并审查 CCK 2024/2025 重叠；若无 Koopman-specific 新条件或物理输出定理则 kill。代码继续冻结。"}, "t43-resume", "TASK-004 resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": "S1 已确认 CCK actuator virtual dynamics 及 robust/CBF/adaptive 方向已有先例。当前仅保留 I1+I2：control-aware approximate Koopman abstraction + reference-compatible controllable lifting。下一步构造最小 T1 问题，严格与普通 reference governor/controllability decomposition 对比，并审查 CCK 2024/2025 重叠；若无 Koopman-specific 新条件或物理输出定理则 kill。代码继续冻结。"}, "t43-handoff", "TASK-004 handoff")
print("revision:", revision())
