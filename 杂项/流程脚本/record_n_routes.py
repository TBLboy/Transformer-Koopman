import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

VAL = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_n_routes_validation_v1.md"
HO = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v2.md"

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
        print(p.stdout.decode("utf-8", "replace")[:800])
        print(p.stderr.decode("utf-8", "replace")[:1500])

npayload = {
    "document": ".project-log/docs/phase2_gpt_n_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scope": "GPT round-2 routes N1-N6 validation (prior-art + cheap experiments)",
    "verdicts": {
        "N1 policy-null defect / Gamma_H": "partial, concept occupied by 2603.27677 (control-equivalent optimality via Hamiltonian structure) + closed-loop model reduction",
        "N2 Riccati quotient": "renamed (bisimulation / closed-loop balanced reduction); triviality risk for static feedback (Z/ker K ~ R^m)",
        "N3 policy-neutral CAP": "partial, must distinguish from feedback linearization (2210.05046, 2211.07112)",
        "N4 policy-relevant residual": "degenerate on P1 (r_n ~ 0)",
        "N5 CAP obstruction rank": "partial, unverified",
        "N6 closed-loop Koopman embedding": "renamed (Koopman feedback linearization 2211.07112/2210.05046/2504.11959)",
    },
    "negative_scans": {"policy/control-equivalent": 30, "bisimulation+optimal control": 2,
                       "closed-loop model reduction/balancing": 1, "feedback linearization+Koopman": 6},
    "residual": "N1 (closed-loop/multi-step policy-equivalent with provable Gamma_H) > N3 (PolicyLinearizable ⊋ Exact) > rest",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-ROUTES-N-001",
      "title": "GPT 第二轮 N1-N6 路线验证：概念被占/退化，N1/N3 残余", "status": "complete",
      "payload": npayload}, "tA-nroutes")

epayload = {
    "document": ".project-log/docs/phase2_gpt_n_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scripts": ["N_P2_policy_null.py", "N_P1_residual.py"],
    "P2_policy_null": {
        "n_latent": 10, "m_input": 2, "rank_K": 2, "policy_null_dim": 8,
        "defect_energy_frac_policy_null_kerK": {"train_mean": 0.973, "train_median": 0.984, "val_mean": 0.974},
        "defect_energy_frac_policy_relevant_rowK": {"train_mean": 0.0267},
        "defect_policy_sensitivity": {"train_mean": 0.0204},
        "horizon_openloop_A^t_sensitivity": {"t0": 0.104, "t1": 0.268, "t2": 0.624, "t3": 1.309, "t5": 4.301},
        "horizon_closedloop_sensitivity": {"t0": 0.104, "t1": 0.083, "t3": 0.058, "t5": 0.011},
        "finding": "one-step defect ~97% policy-null; ker(K) NOT A-invariant (open-loop sens>1 at t=3); bounded under closed loop",
    },
    "P1_residual": {
        "A_spectral_radius": 0.9855, "rank_B": 3,
        "residual_energy_frac_in_im_B": 1.0,
        "position_dims_energy": 5.03e-6, "velocity_dims_energy": 0.3145,
        "policy_sensitivity_via_LQR_K": 0.573,
        "finding": "residual 100% in im(B) -> r_n ~ 0; N4 split degenerate on P1",
    },
}
apply("record.create", {"kind": "research", "id": "PHASE2-N-EXPERIMENTS-001",
      "title": "N 路线廉价证伪实验：P2 97% policy-null 缺陷、P1 残差 100% 在 im(B)", "status": "complete",
      "payload": epayload}, "tA-nexp")

next_action = (
    "已推进 GPT 第二轮 N1–N6 报告：完成 L1/L2 prior-art 对拍 + 负面扫描 + 两组廉价证伪实验，产出 phase2_gpt_n_routes_validation_v1.md 与独立交接稿 phase2_gpt_handoff_v2.md。"
    "结论：N1 部分可行但概念被 2603.27677（控制等价最优性/Hamiltonian 结构）+ 经典闭环降维占；N2 换名为 bisimulation/闭环降维且对静态反馈平凡；N3 需与反馈线性化划界；N4 在 P1 退化（r_n≈0）；N5 未验证；N6 被 Koopman 反馈线性化占。"
    "实验：P2 不可达缺陷 97% 落在 ker(K)（一步 policy-null），但 ker(K) 非 A-不变（开环 t=3 敏感度>1），闭环下有界；P1 残差 100% 在 im(B)。残余：N1（含可证 Γ_H）> N3。"
    "下一步：等待 GPT 依据交接稿 v2 返回第三轮机制级路线，返回后按同法验证。GOAL-001 门禁仍拒绝完成；DEC-018 未满足；代码/配置/论文冻结。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tA-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tA-handoff")
print("val_sha:", sha(VAL))
print("ho_sha:", sha(HO))
print("revision:", revision())
