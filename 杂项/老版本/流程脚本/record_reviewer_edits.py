# -*- coding: utf-8 -*-
import json, subprocess, sys, os

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"


def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def run(args):
    print(">>>", " ".join(args)[:160])
    p = subprocess.run([PY, VIBE, "--root", ROOT] + args,
                       capture_output=True, text=True, encoding="utf-8")
    print(p.stdout[-600:] if p.stdout else "")
    if p.stderr:
        print("STDERR:", p.stderr)
    return p.returncode


# ---- decision: reopen frozen theory text for reviewer-driven rigor edits ----
dec_payload = {
    "decision": "Reopen the frozen theory text for the four reviewer-validated rigor edits (T1-T4) plus four low-risk clarifications (F5-F8).",
    "rationale": "Both an external Major-Revision review and a second independent theory review converge on the same four rigor interfaces (operating-set condition, joint-variable Taylor notation, empirical-claim wording, measured-state definition). The theory-close condition explicitly allows reopening when a reviewer points out a new mathematical/rigor problem. None of the edits change any theorem statement value, numeric diagnostic, or result; they are clarifying/additive.",
    "scope": "Transformer-Koopman/论文/新版本/Main.tex only",
    "not_changed": [
        "all frozen diagnostics (epsilon_k 0.345, d_abs, d_M, product norms, L_F 1.445, M_F 0.007, RMSE, RTI runtime)",
        "Theorem 1 bound form, Proposition 2/3 bounds, Corollary 1 form",
        "model/controller structure",
    ],
}
dfile = os.path.join(TMP, "dec029_payload.json")
write_json(dfile, dec_payload)

# ---- research record: the triage + edits ----
payload = {
    "artifact": "Transformer-Koopman/论文/新版本/Main.tex",
    "artifact_sha256": "017fa1c14769c0d94dbcf70eabebe2d67d2798925e4ff3fb2738be828496deee",
    "recompiled_pdf": "Transformer-Koopman/论文/新版本/build/Main.pdf",
    "recompiled_pdf_sha256": "83f92b9758b34fc40f0b8575d0a8a5054f98f28b5581509f87568c8d9d9dfc28",
    "recompiled_pdf_bytes": 302232,
    "pages": 12,
    "sources_reviewed": [
        "external Major-Revision review of the theory section (GPT)",
        "second independent theory review: 'current theory part strict check and final closure' (DeepSeek)",
    ],
    "already_fixed_before_this_round": [
        "Prop.3 Eq (62) missing delta_u_i -> current Eq (62) already contains [delta_xi_i; delta_u_i] (reviewer used an older draft)",
        "Remark 2 '!=' -> current uses \\not\\Rightarrow",
        "F* definition -> already explicit (reference augmented transition, not plant dynamics)",
        "A(c) is not an exact Koopman operator -> already stated in Scope (vi)",
        "Def.3 rollout-aware objective has no guarantee -> already stated 'mitigates ... does not guarantee strict manifold invariance'",
        "epsilon vs epsilon_k -> already separated by Remark 3",
    ],
    "must_fix_applied": {
        "T1_operating_set": "Theorem 1 now supposes the reference and predicted trajectories remain in Omega over horizon H; proof notes the assumptions apply at every step.",
        "T2_joint_variable": "Prop.3 rewritten with the joint variable eta=col(xi,u): F_Theta(eta_bar_i+delta_eta_i)=F_Theta(eta_bar_i)+D F_Theta delta_eta_i+r_i, and r_i = integral_0^1 (1-s) D^2 F_Theta(eta_bar_i+s delta_eta_i)[delta_eta_i,delta_eta_i] ds (dimensionally consistent).",
        "T3_empirical_wording": "Abstract/intro/contributions/section title/line-643 no longer claim to 'validate every assumption'; Section V-G renamed 'Numerical Diagnostics for the Theoretical Analysis' and a sentence added that these are empirical measurements on the validation distribution, not worst-case certificates over Omega.",
        "T4_measured_state": "Problem formulation now states x_k is the measured task-space state (output) available to predictor/controller, not necessarily the complete physical state; the one-step map is a modeling abstraction and the finite history supplies the missing context.",
    },
    "minor_fixes_applied": {
        "F5": "Prop.2 uses d_k = d^abs_k, unified with Def.2.",
        "F6": "Assumption 2 notes the learned transition inherits Lipschitz continuity from C_phi, g, and the linear transition; compactness of Omega bounds the lifted state.",
        "F7": "Prop.2 notes the bound is a trajectory-wise (posterior) recursion.",
        "F8": "Modeling-error section notes C z_{k+1}=x_{k+1} compatibility is enforced by the state-consistency loss, not structurally.",
    },
    "deliberately_not_done": [
        "No new global-stability / recursive-feasibility / JSR / terminal-invariant-set theory (out of scope, both reviews agree).",
        "No context-Lipschitz theorem (both reviews say not needed).",
        "No counterexample for Remark 2 (optional; classical citation already given).",
    ],
    "compile": "Tectonic 0.17.0; 12 pages; only remaining warning is the pre-existing 0.87pt overfull at the Corollary 1 equation; the new Prop.3 proof equation was split with align* to remove a 12.9pt overfull.",
    "verdict": "Applied; theory text reopened then re-closed for reviewer edits. No numeric or structural change.",
}
pfile = os.path.join(TMP, "reviewer_edits_payload.json")
write_json(pfile, payload)

covers = {
    "files": [
        "Transformer-Koopman/论文/新版本/Main.tex",
        "Transformer-Koopman/论文/新版本/build/Main.pdf",
    ],
    "requirements": [],
    "tasks": ["TASK-006"],
}
cfile = os.path.join(TMP, "reviewer_edits_covers.json")
write_json(cfile, covers)

next_action = (
    "TASK-006（论文新版本，strict）进行中。"
    "**目标**：论文理论部分的文字内容（含证明/定理/参考文献）；实验与绘图暂停；与 GPT 迭代。"
    "**本轮：外部双审阅意见处理（PHASE2-REVIEWER-EDITS-001 / EV-PHASE2-REVIEWER-EDITS-001 / DEC-029）**。"
    "收到两份理论审阅（GPT 大修意见 + DeepSeek 严格检查/收口建议）。逐条对照当前稿："
    "**已在此前修复、审阅者用了旧稿**：Prop.3 (62) 漏 δu_i（现式已含 [δξ_i;δu_i]）、Remark 2 ≠（现为 ⇏）、F* 定义、A(c) 非精确 Koopman、Def.3 无保证、ε vs ε_k。"
    "**本轮已应用的必改项**：T1 Theorem 1 增加 operating-set 条件（轨迹保持在 Ω）；T2 Prop.3 改用联合变量 η=col(ξ,u) 重写 Taylor 余项（消除量纲不一致）；"
    "T3 全文 \"validate every assumption\" 措辞降级为 \"empirical diagnostics\"，§V-G 更名 Numerical Diagnostics；T4 明确 x_k 为 measured task-space state/output（非完整物理状态）。"
    "**另应用 4 项低风险澄清**：F5 Prop.2 d_k≡d^abs_k；F6 Assumption 2 补 C_φ/g 的 Lipschitz 说明；F7 Prop.2 路径依赖注记；F8 C 投影兼容性由训练损失保证。"
    "**未做**：不新增全局稳定性/递归可行性/JSR/终端不变集理论（双审阅一致同意超范围）。"
    "**重新编译**：`论文/新版本/build/Main.pdf`（302232 字节，12 页）已更新，逐页核对通过；新证明等式改 align* 消除 12.9pt overfull；"
    "剩余仅旧有 0.87pt overfull（Cor.1 等式）+ ptm 字体替代警告。**数值与结构零变化**。"
    "**遗留（非理论 Gate）**：(a) 全文旧稿修订颜色标记待用户审阅后决定；(b) 待训练 P=8 最终模型并重导部署资产（DEC-028）；"
    "(c) Experiments/Results/Discussion（§VII 空标题）、图 1–2 适配、中英转换。"
    "**下一步**：把本轮修订整理为 handoff 交 GPT 复核（尤其 T2 联合变量记号、T3 措辞）；用户审阅新 PDF。"
)

steps = [
    ["task", "resume", "--task-id", "TASK-006", "--next-action", next_action],
    ["record", "create", "--kind", "decision", "--id", "DEC-029",
     "--title", "Reopen frozen theory text for reviewer-driven rigor edits (T1-T4 + F5-F8); no numeric/structural change",
     "--status", "active", "--payload", "@" + dfile],
    ["record", "create", "--kind", "research", "--id", "PHASE2-REVIEWER-EDITS-001",
     "--title", "Triage of GPT + DeepSeek theory reviews and application of the 4 must-fix + 4 minor edits; paper recompiled",
     "--status", "complete", "--payload", "@" + pfile],
    ["evidence", "record", "--id", "EV-PHASE2-REVIEWER-EDITS-001", "--kind", "research",
     "--subject", "Reviewer-driven theory rigor edits applied and paper recompiled (12 pages); values unchanged",
     "--status", "valid", "--task-id", "TASK-006", "--covers", "@" + cfile],
    ["task", "handoff", "--task-id", "TASK-006", "--next-action", next_action],
]

for s in steps:
    rc = run(s)
    if rc != 0:
        print("STEP FAILED rc=", rc)
        sys.exit(rc)
print("ALL DONE")
