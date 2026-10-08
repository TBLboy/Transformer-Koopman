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
    print(">>>", " ".join(args)[:140])
    p = subprocess.run([PY, VIBE, "--root", ROOT] + args,
                       capture_output=True, text=True, encoding="utf-8")
    print((p.stdout[-300:] if p.stdout else ""))
    if p.stderr:
        print("STDERR:", p.stderr[-300:])
    return p.returncode


payload = {
    "artifact": "Transformer-Koopman/论文/新版本/Main.tex",
    "artifact_sha256": "3302060bdf09c59950d22fdb2d59c72cf27ebf95b2f7768c9eb2dd1507e56023",
    "artifact_bytes": 78934,
    "recompiled_pdf": "Transformer-Koopman/论文/新版本/build/Main.pdf",
    "recompiled_pdf_sha256": "c0a025c6eb94309e2be937f069fcc5e7931174fe435f352270c2d6a7fe433170",
    "recompiled_pdf_bytes": 300859,
    "pages": 11,
    "what_changed": {
        "section_iv_b": "Rewritten to the actual implementation: two stages. Stage 0 (initialization) = one-step physical prediction loss L_1 (new eq:loss_one_step) over the encoder-generated latent distribution, yielding a time-invariant base (A_0,B). Stage 1 (rollout-aware scheduled training) = minimize L_R (Def. rollout_aware, eq:loss_rollout) where the latent is propagated through A(c) and the context is re-scheduled from the predictor's own rolled-out history; jointly train theta, phi, A_0, U, V, g; B and C fixed; H_R=20.",
        "removed": "Deleted the old-route EDMD three-stage pipeline: eq:edmd_solution (Stage 0 EDMD warm start, Stage 2 closed-form refit), the five losses (eq:loss_x, eq:loss_z, eq:loss_c, eq:loss_multi_x, eq:loss_multi_z, eq:pretraining_loss), the fixed-A multi-step rollout (eq:multi_step_lifted_rollout, eq:multi_step_state_rollout). Verified no dangling labels remain.",
        "algorithm_1": "Rewritten: Output = (theta*, phi*, A_0*, U*, V*, g*); Stage 0 one-step init loop; Stage 1 scheduled-rollout loop re-scheduling the context from the rolled-out history.",
        "fig2_caption": "Now 'One-step lifting and prediction (initialization, Stage~0)'; describes (A_0,B) one-step and the one-step loss, and states Stage 1 replaces A_0 by A(c).",
        "fig1_caption": "Fixed-A dynamics zhat_{k+1}=A z_k+B u_k -> zhat_{k+1}=A(c_k) z_k+B u_k, for consistency with Definition 1.",
        "external_ref": "The single external reference to eq:loss_x in Section IV-C was repointed to eq:loss_one_step.",
    },
    "compile": "Tectonic 0.17.0; 11 pages (was 12); only remaining warning is the pre-existing 0.87pt overfull at the Corollary 1 equation; no undefined references, no errors.",
    "known_limitation": "Fig.1 and Fig.2 schematics are still the old one-step drawings (figures paused per DEC-025); captions are now accurate to what the drawings show and forward-point to Stage 1, but the schematics should be redrawn to depict A(c) and the scheduled rollout.",
    "verdict": "Reviewer Priority-1 (Method-Theory consistency) addressed; Method now matches Theory/Controller on A(c) and the rollout-aware scheduled objective.",
}
pfile = os.path.join(TMP, "r4_ivb_payload.json")
write_json(pfile, payload)

covers = {
    "files": [
        "Transformer-Koopman/论文/新版本/Main.tex",
        "Transformer-Koopman/论文/新版本/build/Main.pdf",
    ],
    "requirements": [],
    "tasks": ["TASK-006"],
}
cfile = os.path.join(TMP, "r4_ivb_covers.json")
write_json(cfile, covers)

next_action = (
    "TASK-006（论文新版本，strict）进行中。**目标**：论文理论部分的文字内容；实验与绘图暂停；与 GPT 迭代。"
    "**第四轮审阅 Priority-1（Method–Theory 一致性）已处理（PHASE2-IVB-REWRITE-001 / EV-PHASE2-IVB-REWRITE-001）**。"
    "§IV-B 整体重写为实际实现：Stage 0 一步初始化（L_1，新 eq:loss_one_step）+ Stage 1 rollout-aware scheduled 训练"
    "（L_R，上下文沿 rollout 重算），A(c)、r=2、B/C 固定，显式声明不使用 EDMD refit/谱稳定；Algorithm 1 重写；"
    "Fig.2 caption 改为 'Stage-0 一步初始化'；Fig.1 caption 固定 A → A(c_k)；删除旧 EDMD/五损失/多步方程（无悬空引用）。"
    "重编译 Main.tex sha 3302060b…（78934 B）、build/Main.pdf sha c0a025c6…（300859 B，11 页），仅剩旧有 0.87pt overfull。"
    "**遗留**：Fig.1/2 示意图仍为旧一步图（待重绘）、颜色标记、P=8 模型重训(DEC-028)、§VII 空、中英转换。"
    "**下一步**：用户审阅新 §IV-B；可把本轮（Priority-1 重写 + Priority-2 小修）回执交 GPT 复核。"
)

steps = [
    ["task", "resume", "--task-id", "TASK-006", "--next-action", next_action],
    ["record", "create", "--kind", "research", "--id", "PHASE2-IVB-REWRITE-001",
     "--title", "Section IV-B + Algorithm 1 rewritten to the actual A(c) rollout-aware scheduled training; Fig.1/2 captions fixed",
     "--status", "complete", "--payload", "@" + pfile],
    ["evidence", "record", "--id", "EV-PHASE2-IVB-REWRITE-001", "--kind", "research",
     "--subject", "Methodology unified with theory/controller on A(c) and the rollout-aware scheduled objective; paper recompiled (11 pages)",
     "--status", "valid", "--task-id", "TASK-006", "--covers", "@" + cfile],
    ["task", "handoff", "--task-id", "TASK-006", "--next-action", next_action],
]

for s in steps:
    rc = run(s)
    if rc != 0:
        print("STEP FAILED rc=", rc)
        sys.exit(rc)
print("ALL DONE")
