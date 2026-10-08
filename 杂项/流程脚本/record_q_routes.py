import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

VAL = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_q_routes_validation_v1.md"
HO = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v4.md"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def revision():
    p = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(p.stdout.decode("utf-8", "replace"))["revision"]

def apply(action, payload, tag):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(),
           "action": action, "payload": payload}
    path = f"{TMP}/env_{tag}.json"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    p = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path], capture_output=True)
    print(("OK   " if p.returncode == 0 else "FAIL ") + tag)
    if p.returncode:
        print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

val_payload = {
    "document": ".project-log/docs/phase2_gpt_q_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scope": "GPT round-4 routes Q0-Q6 validation (prior-art + cheap experiments T4-1..T4-6)",
    "verdicts": {
        "Q0 linear-prefeedback invariance": "CONFIRMED but trivial linear-algebra identity (row-space), not a contribution",
        "Q1 FSAKC": "KILLED on P2: even full-rank nonlinear drift only -0.25% val RMSE, residual rank unchanged; P1 -31% but = standard input-channel identification; exact case occupied by Fan 2401.08153",
        "Q2 FSMO": "KILLED: P2 residual block-Hankel rank 90%=78/99%=97 of 100 -> no low-order dynamic realization; D7 'low-rank' was instantaneous covariance only",
        "Q3 COMP": "WEAK/FAIL: mode placement rho_E best 0.9675, closed-loop rho=1.0; classical eigenstructure assignment",
        "Q4 FCH": "collapses on P2 (J2<J1 fails because Q1 killed)",
        "Q5 SNOK": "KILLED: obstruction subspace reproducible (top2-3 <1deg) but full-order dynamics + not feedback-shapeable",
        "Q6 CSKC": "KILLED: depends on Q1+Q2+Q3, all fail on P2",
    },
    "new_prior_art": {
        "Fan et al. 2401.08153": "stable/stabilizable Koopman embeddings with smooth prefeedback + generalized feedback linearizability (most dangerous)",
        "Strasser et al. 2509.02839": "Annual Reviews in Control 2026 survey: Koopman control from error bounds to closed-loop guarantees",
        "2510.05359": "Koopman Control Factorization (controller-model joint convex design)",
        "2606.10344": "exact bilinear via RKHS lifting", "2201.05098": "Neural Koopman Lyapunov Control",
    },
    "meta_conclusion": "After R(18)/N(6)/M(12)/Q(7) routes, none survives the gate; pattern: P2 closure error is small, non-reshapable by feedback, and full-order; P1 residual always in im(B). Diminishing returns under current gate -> C-level direction decision needed.",
    "user_directive": "validate + feedback only, do not invent new routes",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-Q-ROUTES-001",
      "title": "GPT 第四轮 Q0-Q6 验证：Q0 成立但平凡；Q1/Q2/Q3/Q5/Q6 在 P2 被经验杀死", "status": "complete",
      "payload": val_payload}, "t90-qroutes")

exp_payload = {
    "document": ".project-log/docs/phase2_gpt_q_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scripts": ["Q_P2.py", "Q_P1.py"],
    "P2_T4_1_linear_prefeedback": {"max_abs_dev_from_baseline": 0.0, "Q0_holds_exactly": True},
    "P2_T4_2_feedback_closure_val_rmse": {"baseline": 0.008029, "linear_Kz": 0.008031,
        "quadratic": 0.008005, "mlp_rank_m": 0.008030, "full_drift_rank_n": 0.008009,
        "residual_rank_90_99_all": [2, 4]},
    "P2_T4_3_hankel": {"L": 10, "rank90_train": 78, "rank99_train": 97, "rank90_val": 77, "rank99_val": 97,
        "top10_sv_flat": [1.0, 0.9929, 0.9899, 0.9864, 0.9796, 0.9740, 0.9722, 0.9676, 0.9645, 0.9566]},
    "P2_T4_4_reproducibility_deg": {"mean": [0.08, 0.2, 0.75, 7.03], "max": [0.36, 0.85, 2.78, 22.51], "n_traj": 70, "r": 4},
    "P2_T4_5_mode_placement": {"r": 4, "baseline_rho_A": 1.001, "optimized_leakage": 0.03511,
        "optimized_rho_E": 0.9675, "optimized_rho_closedloop": 1.0},
    "P1_T4_6": {"baseline_rmse": 0.133326, "baseline_rank90_99": [2, 3], "baseline_imB_frac": 1.0,
        "nonlinear_prefeedback_rmse": 0.091715, "full_drift_rmse": 0.0957,
        "finding": "P1 nonlinear prefeedback -31% but residual still 100% in im(B), rank 3 -> standard input-channel identification"},
}
apply("record.create", {"kind": "research", "id": "PHASE2-Q-EXPERIMENTS-001",
      "title": "Q 轮廉价实验 T4-1..T4-6：Q0 精确成立 / 反馈不可重塑 / Hankel 全阶 / 模态配置失败", "status": "complete",
      "payload": exp_payload}, "t91-qexp")

covers = {"files": [".project-log/docs/phase2_gpt_q_routes_validation_v1.md",
                    ".project-log/docs/phase2_gpt_handoff_v4.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_qroutes.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-GPT-Q-ROUTES-001", "--kind", "research",
                    "--subject", "GPT round-4 Q0-Q6 validation",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "t92-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "已推进 GPT 第四轮 Q0–Q6 报告：完成机制级 prior-art 对拍 + 廉价证伪实验 T4-1…T4-6，产出 phase2_gpt_q_routes_validation_v1.md 与独立交接稿 phase2_gpt_handoff_v4.md。"
    "判决：Q0（线性 prefeedback 不变性）精确成立但属平凡线性代数恒等式，非贡献；Q1/Q6 在 P2 被杀死（连全秩非线性漂移仅降 0.25%、残差秩不变；Q1 唯一退路 lifting+feedback 联合重训=被拒原路线且被 Fan 2401.08153 占）；"
    "Q2 被杀死（残差块 Hankel 秩 99%=97/100，无低阶动态，D7 低秩仅瞬时协方差）；Q3 弱（ρ_E 最优 0.9675、闭环 ρ=1.0，经典 eigenstructure assignment）；Q4 层级坍缩；Q5 子空间可复现但动态全阶+不可反馈重塑；Q6 依赖 Q1–Q3 全败。"
    "P1：非线性 prefeedback 降 RMSE 31% 但残差仍 100% 在 im(B)、秩 3（=标准输入通道辨识）。"
    "新增 prior-art 边界：Fan 2401.08153（smooth prefeedback + generalized feedback linearizability）、Strässer 2509.02839（Annual Reviews in Control 2026，error bounds→closed-loop guarantees 综述）、2510.05359、2606.10344。"
    "跨四轮元结论：R(18)/N(6)/M(12)/Q(7) 无候选存活；P2 闭合误差小、不可反馈后验重塑、且全阶动态；P1 残差恒在 im(B)。同数据+同门禁下边际收益趋零。"
    "下一步：向用户呈报，并就阶段② 目标本身做 C 级决策（A 收紧为严谨基线论文 / B 放宽门禁 / C 更换数据-平台 / D 更换建模范式；团队倾向 A 或 D）。等待用户裁决；未裁决前不出新构思。GOAL-001 门禁仍拒绝；DEC-018 未满足；代码/配置/论文冻结。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t93-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t94-handoff")
print("val_sha:", sha(VAL))
print("ho_sha:", sha(HO))
print("revision:", revision())
