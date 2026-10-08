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
    print(p.stdout[-500:] if p.stdout else "")
    if p.stderr:
        print("STDERR:", p.stderr)
    return p.returncode


payload = {
    "artifact": "Transformer-Koopman/论文/新版本/Main.tex",
    "artifact_sha256": "c8a21abb91ee7ffbd0c78a23846b38f3fff3df5b595c123a234fb55d0a017c97",
    "recompiled_pdf": "Transformer-Koopman/论文/新版本/build/Main.pdf",
    "recompiled_pdf_sha256": "aa411ef55a5826872ff43560ec8f1e0e9e605a55441e04901c32b76e70361753",
    "recompiled_pdf_bytes": 303433,
    "pages": 12,
    "review": "Third external theory review (Minor Revision). Its 'previous errors fixed' table re-confirms that the second-version review was a misreading (it claims epsilon_k / eq.(53) / eq.(51)-numbering were 'fixed', but none of those were ever changed by the round-19/T1-T4 edits).",
    "must_fix_applied": {
        "1_context_defined": "Definition 2 now defines the scheduled context c_{k+i}=C_phi(Xhat_{k+i}) re-computed from the predictor's own rollout.",
        "2_assumption2_prereqs": "Assumption 2 now states that the bound holds whenever C_phi, g, and c->A(c) are Lipschitz on Omega and the lifted state is bounded there (standing regularity conditions), instead of the informal 'inherits' phrasing.",
        "3_def3_positioning": "Section V-C now states Definition 3 is an algorithmic design rather than a theoretical result; no statement below uses L_R and no bound is claimed from minimizing it.",
        "4_assumption1_trajectory": "Assumption 1 now additionally requires that the reference and predicted trajectories remain in Omega over the horizon, used explicitly in Theorem 1.",
        "5_remove_redundant_alias": "Removed the redundant 'zhat := z^P' alias in Proposition 2 (it was declared and never used; the training-side binding remains in Section IV-B).",
    },
    "suggested_applied": {
        "thm1_epsilon_note": "Theorem 1 now states explicitly that epsilon is the uniform model-mismatch bound of Assumption 1, not the trajectory-wise defect epsilon_k.",
        "sec4c_explicit": "Section IV-C now writes ||w_k||_2 = epsilon_k explicitly and notes both are at the encoder-consistent latent.",
    },
    "not_applied": [
        "2x2 counterexample for Remark 2 (optional)",
        "abstract wording 'finite-horizon prediction consistency only' (optional)",
        "tighter empirical bound for Corollary 1 (optional)",
    ],
    "compile": "Tectonic 0.17.0; 12 pages; only remaining warning is the pre-existing 0.87pt overfull at the Corollary 1 equation; no new overfull, no undefined macros.",
    "verdict": "Applied; values and theorem statements unchanged. Theory package now at 'Minor Revision addressed' level.",
}
pfile = os.path.join(TMP, "minor_rev_payload.json")
write_json(pfile, payload)

covers = {
    "files": [
        "Transformer-Koopman/论文/新版本/Main.tex",
        "Transformer-Koopman/论文/新版本/build/Main.pdf",
    ],
    "requirements": [],
    "tasks": ["TASK-006"],
}
cfile = os.path.join(TMP, "minor_rev_covers.json")
write_json(cfile, covers)

next_action = (
    "TASK-006（论文新版本，strict）进行中。**目标**：论文理论部分的文字内容；实验与绘图暂停；与 GPT 迭代。"
    "**第三版外部审阅（Minor Revision）已处理（PHASE2-MINOR-REVISION-001 / EV-PHASE2-MINOR-REVISION-001）**。"
    "v3 把前两版\"错误\"标记为已修，但其确认表反证了 v2 是误读（ε_k/(53)/(51)编号 我从未改动）。"
    "v3 新提的 5 条必改经核验**全部为真但属小修级**，已应用："
    "(1) Def.2 补 c_{k+i}=C_φ(X̂_{k+i})（rollout 重算的 scheduled context）；"
    "(2) Assumption 2 改为显式前提（C_φ、g、c↦A(c) Lipschitz、z 有界）；"
    "(3) §V-C 声明 Def.3 为 algorithmic design（无定理使用 L_R）；"
    "(4) Assumption 1 补轨迹保持条件（与 Thm.1 呼应）；"
    "(5) 删除 Prop.2 冗余别名 ẑ≡z^P。"
    "**另应用 2 条建议**：Thm.1 明确 ε≠ε_k；§IV-C 显式写 ‖w_k‖₂=ε_k。"
    "**重新编译**：`论文/新版本/build/Main.pdf`（303433 字节，12 页），逐页核对通过；"
    "无新增 overfull/未定义宏；仅旧有 0.87pt overfull（Cor.1）。**数值与定理陈述零变化**。"
    "**遗留（非理论 Gate）**：(a) 旧稿修订颜色标记待用户审阅后决定；(b) 待训练 P=8 最终模型并重导部署资产（DEC-028）；"
    "(c) Experiments/Results/Discussion（§VII 空标题）、图 1–2 适配、中英转换。"
    "**下一步**：用户审阅新 PDF；可把本轮小修回执交 GPT 确认理论封稿。"
)

steps = [
    ["task", "resume", "--task-id", "TASK-006", "--next-action", next_action],
    ["record", "create", "--kind", "research", "--id", "PHASE2-MINOR-REVISION-001",
     "--title", "Third-review (Minor Revision) 5 must-fix + 2 suggested edits applied; paper recompiled",
     "--status", "complete", "--payload", "@" + pfile],
    ["evidence", "record", "--id", "EV-PHASE2-MINOR-REVISION-001", "--kind", "research",
     "--subject", "Minor-revision clarity edits applied and paper recompiled (12 pages); values unchanged",
     "--status", "valid", "--task-id", "TASK-006", "--covers", "@" + cfile],
    ["task", "handoff", "--task-id", "TASK-006", "--next-action", next_action],
]

for s in steps:
    rc = run(s)
    if rc != 0:
        print("STEP FAILED rc=", rc)
        sys.exit(rc)
print("ALL DONE")
