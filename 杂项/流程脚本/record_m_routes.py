import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

VAL = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_m_routes_validation_v1.md"
HO = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v3.md"
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
        print(p.stdout.decode("utf-8", "replace")[:600])
        print(p.stderr.decode("utf-8", "replace")[:1200])

val_payload = {
    "document": ".project-log/docs/phase2_gpt_m_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scope": "GPT round-3 routes M1-M12 / C1-C4 validation (prior-art + negative scan + cheap experiments D1-D7)",
    "verdicts": {
        "M1 Defect-Coherent Koopman": "KILLED - D1 shows V*=0 (no output-nulling/controlled-invariant subspace on P2); geometric disturbance decoupling classical",
        "M2 Projected Harmful-Error Certificate": "DOWNGRADED - D3 only ~4x radius reduction, benign=imB (classical matched); collides 2603.15091/2608.11808",
        "M3 Dual-Weighted Goal-Oriented": "DOWNGRADED - D4 corr(DWR,dJ)=1.0 is exactness of linear-model adjoint (=standard LQR costate); DWR classical PDE/ROM",
        "M4 KKT-Coherent MPC": "KILLED - D5 |u|max 65.3<<300, constraints never active",
        "M5/M12 CAP-Core+Obstruction": "SURVIVES EMPIRICALLY - D7 low-rank obstruction (rank 2-4/10); but occupied by CAP 2602.14537, PAD 2603.15091, 2603.29001, 2605.24666",
        "M6 almost decoupling": "KILLED - Hinf + Koopman residual = ordinary robust control",
        "M7 matched virtual input": "DOWNGRADED - D6 no predictability gain",
        "M8 shielding horizon": "KILLED - finite-horizon observability Gramian",
        "M9 task-family envelope": "KILLED - D2 strategy-null rank 2->10 within 10 tasks",
        "M10/M11": "unassessed",
    },
    "prior_art_negative_scans": {
        "Koopman disturbance decoupling": 4, "dual-weighted residual control": 26,
        "goal-oriented Koopman": 0, "Koopman output nulling invariant subspace": 0,
        "Koopman goal-oriented error certificate": 0, "Koopman invariant subspace control": 28,
    },
    "key_new_collisions": ["2608.11808 (Koopman+HJB error bounds + closed-loop stability + optimality gap)",
                            "2603.29001 (principal-vector subspace pruning)", "2605.24666 (PageRank invariant subspaces)"],
    "gate_result": "no M route passes all 6 hard-gate criteria",
    "residual": "C2 (M5/M12 low-rank obstruction) > C3 (M3 classical DWR) > C1 (collapsed to M2; M9/M1-shielding killed)",
    "user_directive": "validate + feedback only, do not invent new routes",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-M-ROUTES-001",
      "title": "GPT 第三轮 M1-M12/C1-C4 验证：M1/M4/M9 死、M2/M3/M7 降级、M5/M12 唯一经验残余", "status": "complete",
      "payload": val_payload}, "t80-mroutes")

exp_payload = {
    "document": ".project-log/docs/phase2_gpt_m_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scripts": ["D_P2.py", "D_P1.py", "D_P2_DWR.py", "D_P2_D7.py"],
    "D1": {"V_star_dim": 0, "kerC_dim": 8, "imB_dim": 2, "benign_dim": 2, "rho_V": 0.0,
           "finding": "no output-nulling controlled-invariant subspace -> M1 shielding branch dead"},
    "D2": {"rank_curve_task_counts_1_10_50_200": [2, 10, 10, 10],
           "finding": "task-family strategy-null rank saturates to n=10 by ~10 tasks -> no universal policy-null -> M9 dead"},
    "D3": {"rho_matched_train_mean": 0.848, "rho_harmful_train_mean": 0.152,
           "q95_ratio_train": 0.2507, "q95_ratio_val": 0.2365,
           "finding": "only ~4x radius reduction; benign=imB -> M2 = classical matched compensation"},
    "D4": {"n_windows": 5220, "H": 10, "corr_DWR_vs_dJ": 1.0000, "corr_raw_defect_vs_dJ": 0.1215,
           "finding": "DWR weight = exact adjoint of linear nominal model (analytically exact) -> standard costate, not novel; M3 downgraded"},
    "D5": {"u_abs_max_train": 65.29, "u_abs_max_val": 59.17, "u_max": 300,
           "finding": "constraints never active -> M4 lacks physical anchor"},
    "D6": {"recon_err": 3.68e-12, "du_std": [0.607, 1.807, 0.824], "cross_joint_corr_2_3": 0.785,
           "finding": "no lower-dim/more-predictable Delta-u structure -> M7 downgraded"},
    "D7": {"residual_cov_eigvals_normalized": [0.5166, 0.4227, 0.0310, 0.0228, 0.0041, 0.0020, 0.0003, 0.0003, 0.00007, 0.0],
           "effective_rank_90pct": 2, "effective_rank_99pct": 4,
           "two_step_over_one_step_median": 2.21, "two_step_over_one_step_q95": 5.36, "n": 26640,
           "finding": "defect concentrated in low-dim subspace (rank 2-4/10) -> M5/M12 empirically survives"},
    "P1_residual_ref": {"residual_energy_frac_in_im_B": 1.0, "r_n": "~0"},
}
apply("record.create", {"kind": "research", "id": "PHASE2-M-EXPERIMENTS-001",
      "title": "M 轮廉价证伪实验 D1-D7：V*=0 / 任务族满秩 / 约束不激活 / DWR 精确伴随 / 低秩 obstruction", "status": "complete",
      "payload": exp_payload}, "t81-mexp")

covers = {"files": [".project-log/docs/phase2_gpt_m_routes_validation_v1.md",
                    ".project-log/docs/phase2_gpt_handoff_v3.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_mroutes.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-GPT-M-ROUTES-001", "--kind", "research",
                    "--subject", "GPT round-3 M1-M12/C1-C4 validation",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "t82-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "已推进 GPT 第三轮 M1–M12/C1–C4 报告：完成机制级 prior-art 对拍 + 6 条负向扫描 + 廉价证伪实验 D1–D7，产出 phase2_gpt_m_routes_validation_v1.md 与独立交接稿 phase2_gpt_handoff_v3.md。"
    "判决：M1（D1 V*=0，屏蔽支路死）、M4（D5 约束从不激活）、M9（D2 任务族秩 2→10）被经验杀死；M2（D3 仅 ~4×缩减，=经典匹配）、M3（D4 corr(DWR,ΔJ)=1 是线性模型伴随精确性，=标准协态）、M7（D6 无预测增益）降级；"
    "M5/M12 经验存活（D7 缺陷低秩，有效秩 90%=2/99%=4），但撞 2602.14537(CAP)/2603.15091(PAD)/2603.29001(principal 剪枝)/2605.24666(PageRank)，且新增撞车 2608.11808（Koopman+HJB 误差界+闭环稳定+最优性间隙）。"
    "负向扫描：goal-oriented Koopman=0、Koopman output nulling invariant subspace=0；Koopman disturbance decoupling=4、dual-weighted residual control=26（全 PDE/ROM）。"
    "无任何 M 路线过 6 条硬门禁。残余：C2(M5/M12) > C3(M3) > C1(塌缩为 M2)。"
    "下一步：等待 GPT 依据交接稿 v3 返回第四轮（要求聚焦闭环/随控制器变化的机制）；返回后按同法验证。GOAL-001 门禁仍拒绝完成；DEC-018 未满足；代码/配置/论文冻结。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t83-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t84-handoff")
print("val_sha:", sha(VAL))
print("ho_sha:", sha(HO))
print("revision:", revision())
