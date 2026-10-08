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
    print(">>>", " ".join(args)[:150])
    p = subprocess.run([PY, VIBE, "--root", ROOT] + args,
                       capture_output=True, text=True, encoding="utf-8")
    print(p.stdout[-600:] if p.stdout else "")
    if p.stderr:
        print("STDERR:", p.stderr)
    return p.returncode


# ---- record 1: round-4 minor fixes applied ----
payload1 = {
    "artifact": "Transformer-Koopman/论文/新版本/Main.tex",
    "artifact_sha256": "01fc1955894bd8f8ae1fd4c8d1211ccabbf54604e9736ed12da2f7f873788fe8",
    "artifact_bytes": 82357,
    "recompiled_pdf": "Transformer-Koopman/论文/新版本/build/Main.pdf",
    "recompiled_pdf_sha256": "cd5f126ac1af1b3a2ba091a23ba990dd285fbf49298e228d883e1a9a3dbf8df8",
    "recompiled_pdf_bytes": 304115,
    "pages": 12,
    "review": "Fourth external review (Method-Theory Consistency): core theory PASS, proofs PASS w/ minor fixes, method-theory consistency NOT CLOSED (Priority 1), conditional pass.",
    "priority2_applied": {
        "1_thm1_ek0": "Theorem 1 e_k=0 condition tightened: requires the same measured history AND the corresponding encoder-consistent latent state (Xhat_k=X_k and z^P_k=g_theta(X_k)), not merely 'starts from a true measurement'.",
        "2_assumption1_domain": "Assumption 1 mismatch is now quantified over reference augmented states (xi*,u) in Omega.",
        "3_prop3_linesegment": "Prop.3 proof now bounds ||D^2 F|| on the line segment {bar_eta_i+s delta_eta_i} by Assumption 3, instead of claiming it 'on Omega'.",
        "4_diagnostics_typo": "Diagnostics text now reads 'absolute one-step defects epsilon_k against absolute rollout defects d^abs' (was 'absolute epsilon').",
        "5_prop3_not_one_iter": "Prop.3 no longer claims one RTI iteration is sufficient; it states local second-order accuracy and attributes single-iteration adequacy to the matched-oracle experiment (also updated in Section VI-C).",
    },
    "compile": "Tectonic 0.17.0; 12 pages; only remaining warning is the pre-existing 0.87pt overfull at the Corollary 1 equation; no new overfull, no undefined macros. Values and theorem statements unchanged.",
    "verdict": "Priority-2 applied; Priority-1 (method-theory unification) is confirmed real and is larger than the reviewer stated (see PHASE2-METHOD-CODE-TRACE-001).",
}
p1 = os.path.join(TMP, "r4_minorfix_payload.json")
write_json(p1, payload1)

covers1 = {
    "files": [
        "Transformer-Koopman/论文/新版本/Main.tex",
        "Transformer-Koopman/论文/新版本/build/Main.pdf",
    ],
    "requirements": [],
    "tasks": ["TASK-006"],
}
c1 = os.path.join(TMP, "r4_minorfix_covers.json")
write_json(c1, covers1)

# ---- record 2: code trace finding ----
payload2 = {
    "question": "Does the paper's Methodology (Section IV-B) match the actual training implementation?",
    "method": "Read-only static inspection of the migrated repo 训练代码/ and of the gate14 research surrogate scripts; cross-read against Main.tex Sections IV-B / V-B.",
    "finding_paper": "Main.tex Section IV-B + Algorithm 1 + Fig.2 describe a THREE-STAGE EDMD pipeline for a FIXED-A model: Stage 0 EDMD warm start of (A,B); Stage 1 joint optimization of (theta,A,B) with five losses (L_x, L_z, L_c, L_multi,x, L_multi,z) and a fixed-A rollout zhat_{k+i}=A zhat_{k+i-1}+B u_{k+i-1}; Stage 2 closed-form EDMD refit of (A,B).",
    "finding_repo": "The migrated repo 训练代码/ implements ONLY the old fixed-A dense route (models/koopman_dynamics.py single A; edmd_trainer.py 3-stage EDMD). It contains NO context network C_phi, NO g/U/V/A0, NO rank-r, NO scheduled-rollout objective. So Section IV-B literally describes the migrated repo's old-route training, not the paper's claimed model.",
    "finding_new_route": "The paper's actual new route is implemented as a research surrogate in the gate14 scripts: gate_context_koopman.py (class CtxKoopman) and gate14_stabilize.py (class BudgetedCtxKoopman). Model: PatchTST encoder + context MLP C_phi(in_ctx->64->16) + A(c)=A0+U diag(delta_A*pi*tanh(g(c))) V^T with column-normalized U,V, softmax budget pi, |a_i|<=delta_A, delta_A=0.07, r=2; B=B0 fixed; C=[I_n|0] fixed. Training: initialize from a one-step-trained fixed base (fixed.pt), then minimize an open-loop scheduled-propagation MSE over H=20 where the context is re-computed from the decoded history buffer at every step, optionally plus a spectral-radius penalty relu(rho(A)-rho_max)^2 with rho_max=0.99; the final model uses lam=0 (no rho penalty). No EDMD, no five losses, no Stage-2 refit.",
    "diagnostics_model": "gate16_diag_final.py loads BudgetedCtxKoopman from gate_states/A_stab_openloop_lam0.0_rho0.99.pt (r=2, P=8, d=10) - i.e. the frozen diagnostics were computed with the surrogate model, not with any migrated-repo model.",
    "consequence": "The reviewer's Priority-1 (Method != Theory) is correct, and deeper than stated: the fix is to rewrite Section IV-B + Algorithm 1 + Fig.2 caption to the actual new-route training (one-step initialization + rollout-aware scheduled objective, A(c), r=2, B/C fixed, no EDMD), and to update the single external reference to eq:loss_x at line 635.",
    "open_decision": "Whether to rewrite Section IV-B now, and how to handle Fig.2 (old fixed-A one-step schematic) while figures are paused.",
    "evidence_paths": [
        "训练代码/src/patchtst_koopman/models/koopman_dynamics.py",
        "训练代码/src/patchtst_koopman/training/edmd_trainer.py",
        "C:/Users/12187/AppData/Local/Temp/opencode/gate_context_koopman.py",
        "C:/Users/12187/AppData/Local/Temp/opencode/gate14_stabilize.py",
        "C:/Users/12187/AppData/Local/Temp/opencode/gate16_diag_final.py",
    ],
}
p2 = os.path.join(TMP, "r4_codetrace_payload.json")
write_json(p2, payload2)

covers2 = {
    "files": [
        "Transformer-Koopman/训练代码/src/patchtst_koopman/models/koopman_dynamics.py",
        "Transformer-Koopman/训练代码/src/patchtst_koopman/training/edmd_trainer.py",
        "Transformer-Koopman/论文/新版本/Main.tex",
    ],
    "requirements": [],
    "tasks": ["TASK-006"],
}
c2 = os.path.join(TMP, "r4_codetrace_covers.json")
write_json(c2, covers2)

next_action = (
    "TASK-006（论文新版本，strict）进行中。**目标**：论文理论部分的文字内容；实验与绘图暂停；与 GPT 迭代。"
    "**第四轮外部审阅（Method–Theory Consistency, Conditional Pass）已评估**。"
    "Priority-2 的 5 条小修已应用并重编译（Main.tex sha 01fc1955…, build/Main.pdf 304115 B / 12 页）："
    "(1) Thm.1 e_k=0 收紧（需同一实测历史+encoder 一致隐状态）；(2) Assumption 1 限定 reference augmented states (ξ*,u)；"
    "(3) Prop.3 证明 on Ω → line-segment（与 Assumption 3 neighborhood 一致）；(4) 诊断 ε → ε_k；"
    "(5) Prop.3 不再称单次 RTI 迭代充分（改第二阶精度 + oracle 实验评估）。"
    "**Priority-1 确认为真且更深**：论文 §IV-B/Algorithm 1/Fig.2 描述的是**旧固定-A 路线**（EDMD 三阶段 + 五损失 + Stage2 refit），"
    "而论文其余部分（Def.1/§IV-C/§V/§VI/摘要/引言）用 A(c)+L_R；**实际新路线实现**只在 gate14 研究脚本"
    "（BudgetedCtxKoopman：encoder+C_φ+A(c)=A0+U·diag(δ_A·π⊙tanh(g(c)))·Vᵀ, r=2/δ_A=0.07, B 固定, C=[I_n|0]；"
    "训练=一步物理 MSE 训底座 + 开环 scheduled 传播 MSE(H=20, 上下文沿 rollout 重算) + ρ 惩罚；无 EDMD/无五损失/无 Stage2）。"
    "迁移进仓库的 `训练代码/` 只有旧路线；gate16 诊断用的是 surrogate 模型。"
    "**待用户决策**：是否整体重写 §IV-B+Algorithm 1 为实际实现，以及 Fig.2（旧一步示意图）如何处理（现仅 1 处外部引用 eq:loss_x @ line 635）。"
    "**遗留**：颜色标记、P=8 模型重训(DEC-028)、§VII 空、图1–2、中英转换。"
    "**下一步**：用户确认 §IV-B 重写方向后执行并重编译。"
)

steps = [
    ["task", "resume", "--task-id", "TASK-006", "--next-action", next_action],
    ["record", "create", "--kind", "research", "--id", "PHASE2-ROUND4-MINORFIX-001",
     "--title", "Fourth-review Priority-2 (5 minor theory fixes) applied; paper recompiled",
     "--status", "complete", "--payload", "@" + p1],
    ["record", "create", "--kind", "research", "--id", "PHASE2-METHOD-CODE-TRACE-001",
     "--title", "Code trace: paper Section IV-B describes the OLD fixed-A route; the new A(c) route exists only in the gate14 surrogate",
     "--status", "complete", "--payload", "@" + p2],
    ["evidence", "record", "--id", "EV-PHASE2-ROUND4-MINORFIX-001", "--kind", "research",
     "--subject", "Fourth-review Priority-2 minor fixes applied and paper recompiled (12 pages); values unchanged",
     "--status", "valid", "--task-id", "TASK-006", "--covers", "@" + c1],
    ["evidence", "record", "--id", "EV-PHASE2-METHOD-CODE-TRACE-001", "--kind", "research",
     "--subject", "Static trace: migrated repo = old fixed-A route only; new A(c) route lives in gate14 surrogate scripts",
     "--status", "valid", "--task-id", "TASK-006", "--covers", "@" + c2],
    ["task", "handoff", "--task-id", "TASK-006", "--next-action", next_action],
]

for s in steps:
    rc = run(s)
    if rc != 0:
        print("STEP FAILED rc=", rc)
        sys.exit(rc)
print("ALL DONE")
