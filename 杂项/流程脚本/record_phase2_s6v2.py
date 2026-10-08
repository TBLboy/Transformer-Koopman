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


dec = {
    "title": "阶段② 组合路线物理载体替换为量化/饱和接口 + 有效性域",
    "status": "active",
    "payload": {
        "decision": "A9（未指令张紧偏置 a_perp）载体经 S8 证不成立（P2 共模从不下发，a_perp=0 按设计）。组合路线的物理载体替换为：执行器接口量化+饱和项（P2 整数脉冲 Δ=1，|u|<=300）+ 张紧有效性域条件 Φ。T1 rigor 骨架保留。",
        "rationale": "量化项可估（e_max=Δ√m/2≈0.707 步）、物理真实；有效性域把'张紧'正确定位为定理适用范围而非有界输入扰动，并给出可在线计算的离域残差判据 r_k。",
        "alternatives_considered": ["纯 rigor+A2/A7", "只保留 rigor 修正 T1", "先补 ε 实证再选"],
        "impact": "决定 S6 v0.2 定理形式（T1′ + 定理2）与阶段③实验设计（量化/δ 项经验评估 + r_k 离域监控）。",
        "class": "C",
        "user_confirmed": True,
    },
}

next_action = (
    "S6 v0.2 完成（T1′ + 定理2 有效域/离域检测）。S8b：P2 部署模型 ‖B‖e_max=0.019（量化项可忽略），但 ρ(A)=2.0878、‖A‖=29.1，"
    "LQR(Q=I,R=I) 后 cond(P)~2e10、T1′ 常数 ~8e15 -> 界数学有效但**数值空泛**；根因 config 设 rho_max 但 svd_clipping=false，稳定性约束未生效（INV1 违规）。"
    "因此理论实用性要求'稳定化模型 + 非空泛界'作为设计前提。下一步候选：确认是否将稳定化作为阶段③硬前提，并进入 S6 入论文 + 阶段③；C11（离域阈值标定）未决。"
)

payload = {
    "status": "complete",
    "documents": [
        ".project-log/docs/phase2_theory_construction_v0.1.md",
        ".project-log/docs/phase2_theory_construction_v0.2.md",
    ],
    "theory_v0_2": {
        "carrier": "input quantization+saturation interface term + taut validity domain Phi",
        "T1_prime": "||e^z_k|| <= sqrt(lmax/lmin)(1-lam)^{k/2}||e^z_0|| + sqrt(lmax/lmin) D/(1-sqrt(1-lam)), D = eps + ||B|| Delta sqrt(m)/2 + delta",
        "theorem_2": "conditional guarantee while x_k in Phi (taut envelope) + online departure test r_k = ||g_theta(X_{k+1})-(A z_k+B a_k)|| > eps",
    },
    "S8b_terms": {
        "script": "C:/Users/12187/AppData/Local/Temp/opencode/s8b_p2_terms.py",
        "P2_A": "rho=2.0878, ||A||_2=29.1152",
        "P2_B": "||B||_2=0.0265",
        "stabilizable": "controllability rank 10/10, PBH ranks 10 for all 3 unstable modes -> stabilizable",
        "e_max": "0.7071 steps, ||B|| e_max = 0.0187 (quantization term negligible)",
        "LQR": "Q=I,R=I: rho(A_cl)~1.0000, cond(P)~2.2e10, T1' constant ~8.36e15 -> bound numerically vacuous",
        "root_cause": "config sets koopman.rho_max=0.9999 but svd_clipping=false -> stability constraint not enforced (INV1 violation)",
    },
    "resolved": ["C10: quantization term magnitude evaluated -> negligible for P2"],
    "open": ["C11: departure-test threshold calibration under distribution shift"],
    "verdict": "Theory valid but practical usefulness requires a stabilized (non-vacuous) learned model; the current pipeline violates this. Candidate next: make stabilization a hard prerequisite for phase 3.",
}

rc = apply("record.create", {"kind": "decision", "id": "DEC-017", "title": dec["title"], "status": "active", "payload": dec["payload"]}, "t49-dec017")
if rc == 0:
    apply("record.create", {"kind": "research", "id": "PHASE2-S6-002", "title": "阶段② S6 v0.2 定理（量化/饱和+有效域）+ S8b 项评估", "status": "complete", "payload": payload}, "t49-s6v2")
    apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t49-resume")
    apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t49-handoff")
print("revision:", rev())
