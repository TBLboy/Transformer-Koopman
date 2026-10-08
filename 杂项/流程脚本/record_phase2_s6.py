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
    "title": "阶段② 论文核心创新主张取向 = 组合路线",
    "status": "active",
    "payload": {
        "decision": "论文核心创新取向锁定为组合路线：以可验证闭环 task-tracking 界为理论骨架（修复 Schur 缺陷、统一编码器/有限数据/history 截断/输入秩缺陷），以 A9（执行器冗余/零空间门控）为物理载体，P1 刚体臂 + P2 绳驱软臂两平台实机验证。",
        "rationale": "目标为 RA-L/T-RO/机器人会议，需要理论 + 实机；通用 operator 方向（A1/A3/A4/A5）已被 prior-art 覆盖，纯 rigor 路线可能与 Strasser 2026 综述重叠，故采用组合以形成具体结构 + 可证定理。",
        "alternatives_considered": ["严谨性路线（纯闭环界修正）", "软体物理结构路线（纯 A9）", "先做 A2/A7/A9 对比原型"],
        "impact": "决定后续 S6-S8 的定理构建、实验设计与阶段③代码改动；论文核心 claim 由此确定。",
        "class": "C",
        "user_confirmed": True,
    },
}

next_action = (
    "组合路线（DEC-016）已进入 S6/S7：已写 phase2_theory_construction_v0.1.md，给出修正定理 T1（Lyapunov 形式，去除错误的 ‖A_cl‖<1 假设）、"
    "显式纳入前馈不可达残差 δ（G2）与未指令执行/零空间影响 β（A9）、误差项分离（G1/G4），并通过 C1-C8 反例/边界审查。"
    "下一步 S8 最小数据验证（代码继续冻结）：(1) 用 P1/P2 冻结 checkpoint/验证数据估计 ε_data/ε_enc；(2) 检查 P2 数据是否有张紧/松弛模式代理量以界定 a_max 可估性；"
    "(3) 最小数值仿真验证 T1 的界随 δ,β 单调且比原式有意义；(4) 若 A3 不可界且零空间对动力学无影响则复合载体失效，回退纯 rigor+A2/A7。"
)

payload = {
    "status": "complete",
    "documents": [".project-log/docs/phase2_theory_construction_v0.1.md"],
    "theory": {
        "backbone": "Corrected Lyapunov-form UUB tracking bound (T1/T1') replacing the invalid epsilon/(1-||A_cl||) bound; uses DARE identity A_cl^T P A_cl = P - Q - K_c^T R K_c and lambda = lambda_min(Q+K_c^T R K_c)/lambda_max(P).",
        "new_assumptions": ["A3 bounded uncommanded actuator component a_perp (A9)", "A4 bounded feedforward infeasibility delta = ||P_G (z_ref+ - A z_ref)|| (G2)"],
        "new_terms_in_bound": ["beta = ||B|| a_max (redundancy/nullspace pricing)", "delta = feedforward infeasibility"],
        "error_separation": "epsilon <= eps_enc + eps_data + eps_hist (G1/G4)",
    },
    "proof_audit": {
        "C1": "verified counterexample A=[[0.95,3],[0,0.95]]: rho<1 but ||A||_2=3.2755>1 -> old bound invalid",
        "C2": "Schur does not imply norm<1 (non-normal matrices)",
        "C3": "omitted feedforward infeasibility term -> no convergence to reference; demo B_G=[1;0], d=[0;1], delta=1",
        "C4": "if B a_perp = 0 then beta=0 even with ker G != 0",
        "C5": "degenerate consistency: eps=beta=delta=0 -> 0; Q->0 -> lambda->0, bound->inf (expected)",
        "C6": "lambda in (0,1] => denominator positive, no division by zero",
        "C7": "dimensional consistency checked",
        "C8": "open: A3 physical boundability for P2, explicit eps_hist bound, P conservatism",
    },
    "verdict": "T1 mathematically self-consistent and fixes the verified Schur defect; novelty NOT yet established until C8 resolved via S8 data-side minimal validation.",
}

rc = apply("record.create", {"kind": "decision", "id": "DEC-016", "title": dec["title"], "status": "active", "payload": dec["payload"]}, "t46-dec016")
if rc == 0:
    apply("record.create", {"kind": "research", "id": "PHASE2-S6-001", "title": "阶段② S6 定理构建 + S7 证明审查（组合路线）", "status": "complete", "payload": payload}, "t46-s6")
    apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t46-resume")
    apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t46-handoff")
print("revision:", rev())
