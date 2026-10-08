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
        print(r.stderr.decode("utf-8", "replace")[:1200])
    return r.returncode


next_action = (
    "S8 数据/规格侧完成：P2 数据仅 2D 光点（无张力/模式标签）、输入为整数脉冲 |u|<=300、共模从不下发 -> A9 的 a_perp 偏置载体不成立（a_perp=0 按设计）。"
    "T1 rigor 骨架保留且必要（C9 数值验证通过）。组合路线需局部调整：A9 载体替换为 (i) 量化+饱和接口项、(ii) 有效性域/张紧 regime 条件，或改用 A2/A7。"
    "P2 部署 checkpoint 存在但 rho(A)=2.0878>1 且 history_length=4 与 config=8 不一致；P1 无 checkpoint（结果备份为空）。等待用户 C 级确认方向微调后进入 S6 修订与阶段③。"
)

payload = {
    "status": "complete",
    "documents": [".project-log/docs/phase2_theory_construction_v0.1.md"],
    "data_facts": {
        "P1": "processed x (N,6) full state pos+vel, u (N,3); NO checkpoint (结果备份 empty, results/ absent)",
        "P2": "processed x (N,2) light point only, u (N,2); no velocity/tension/mode labels",
        "P2_deploy_ckpt": "koopman_A(10,10), koopman_B(10,2), spectral_radius=2.0878>1, metadata history_length=4 vs config 8 (ALN-010 residual)",
    },
    "spec_facts": {
        "source": "软控逻辑.txt V3.6",
        "input": "integer pulse (dx,dy), |u_max| = V_max*(Ts-0.05) = 2000*0.15 = 300 steps",
        "differential": "lower controller executes ONLY differential (L/R, U/D) actions; common-mode never commanded",
        "tension": "tautness guaranteed by initial critical-tensioning calibration; NO tension sensor, NO runtime mode label",
    },
    "A9_verdict": "INVALID as physical carrier: a_perp = 0 by construction (common mode never driven); A3 not estimable and has no independent drive source; beta degenerates to 0 (C4 no-effect branch). Tension is a validity-domain condition, not a bounded input disturbance.",
    "alternatives": [
        "(i) input quantization + saturation interface term: ||B eps_q|| <= ||B|| sqrt(m)/2, |v|<=300 (estimable, but A3-like / weak novelty standalone)",
        "(ii) validity-domain / taut-regime condition: theorem holds within taut envelope Phi with a departure-detection condition (physically real; adjacent to killed A4)",
        "(iii) fallback: keep T1 rigor backbone; drop A9; use A2/A7 as physical carrier",
    ],
    "verdict": "T1 rigor backbone survives (necessary + numerically verified). Combination route needs a C-level micro-adjustment of the physical carrier.",
}

rc = apply("record.create", {"kind": "research", "id": "PHASE2-S8-002", "title": "阶段② S8 数据/规格侧发现与 A9 载体失效", "status": "complete", "payload": payload}, "t48-s8b")
if rc == 0:
    apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t48-resume")
    apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t48-handoff")
print("revision:", rev())
