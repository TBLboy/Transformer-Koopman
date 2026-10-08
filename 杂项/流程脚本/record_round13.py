import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
REP = Path(ROOT) / ".project-log" / "docs" / "phase2_gate_stage3_gate13_v1.md"
HOF = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v11.md"
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

payload = {
    "document": ".project-log/docs/phase2_gate_stage3_gate13_v1.md",
    "document_sha256": sha(REP),
    "scope": "Gate-13A/B/C/D finalization gate for A-only HCLT-K (GPT round-13 v1.2)",
    "gate13A_prediction_variants_val_pct_vs_fixed": {
        "R_reencode": {"H1": -61.6, "H5": -71.3, "H10": -71.1, "H20": -73.7},
        "F_reencode": {"H1": -61.6, "H5": -207.1, "H10": -384.8, "H20": -556.5},
        "F_prop": {"H1": -61.6, "H5": -223.3, "H10": -443.0, "H20": -738.2},
        "R_prop": {"H1": -61.6, "H5": 31.6, "H10": -22.8, "H20": -114.9},
    },
    "gate13A_verdict": "Open-loop latent propagation (frozen OR scheduled) collapses; only re-encoding predictor (encoder in the loop each step) retains the gain. eta_F negative (<<0.4). Model is an encoder-anchored one-step predictor, not a standalone dynamical system.",
    "gate13B_rank_sweep_Sr": {"1": 0.11311, "2": 0.03722, "3": 0.03774, "5": 0.03744},
    "gate13B_chosen_r": 2,
    "gate13C_diagnostics": {
        "rho_Ak": {"median": 1.0318, "q99": 1.0424, "max": 1.0433},
        "A0_rho": 1.0299, "A0_norm2": 1.0399,
        "dA_spec2": {"median": 0.0357, "q99": 0.0590, "max": 0.0682},
        "drift_fro_ratio": {"median": 0.00576, "max": 0.0182},
        "product_growth_gH_H20": {"median": 1.0391, "max": 1.0450},
        "gate_modes_active_frac": [0.828, 0.800, 0.774],
        "gate_corr_with_speed_du_dx": [-0.026, -0.0008, -0.026],
    },
    "gate13D_conditional_shuffle": {"n_pairs": 600, "err_normal": 0.00763, "err_swapped": 0.05057, "ratio": 6.63, "verdict": "PASS"},
    "decision_table": {
        "A_only_H20_vs_fixed": "GO (-73.7% val / -75.8% test, 2 seeds)",
        "frozen_gain_retention": "NEGATIVE -> frozen MPC unusable",
        "scheduled_propagation": "fails at H>=10 -> scheduled propagation also unusable",
        "reencoding_predictor": "usable, gain real (-73.7%)",
        "rank_r": 2, "conditional_shuffle": "PASS", "rho": ">1 (marginally unstable)",
        "product_growth": "~1.04/step",
    },
    "open_for_gpt": "controller architecture: (i) re-encoding MPC vs (ii) stabilized latent (DEC-018 becomes MPC-usability prerequisite); bounded-modulation parameterization; common-P beta*; r=2 finalization; real-time cost of per-step encoder",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GATE13-FINALIZATION-001",
      "title": "Gate-13 定稿检验：开环传播失效（frozen/scheduled 均崩），增益依赖每步重编码；ρ(A)>1；r=2", "status": "complete",
      "payload": payload}, "tU0-gate13")

exp_payload = {
    "document": ".project-log/docs/phase2_gate_stage3_gate13_v1.md",
    "document_sha256": sha(REP),
    "scripts": ["gate13_analyze.py", "gate13b_rsweep.py"],
    "artifacts": ["gate13_result.json", "gate13b_result.json", "gate_states/A_r{1,2,5}.pt"],
    "gate13A": "Four predictors compared; only re-encoding (encoder each step) preserves the -74% gain; frozen and scheduled open-loop propagation diverge (rho>1).",
    "gate13B": "r=1 insufficient; r=2 minimal near-optimal (S_r 0.03722); r=3/5 within noise.",
    "gate13C": "rho(A_k) median 1.032 (>1); ||dA|| q99 0.059; slow drift 0.006; product growth ~1.04/step.",
    "gate13D": "Matched-current history shuffle -> 6.63x next-step error -> history context genuinely used.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GATE13-EXPERIMENTS-001",
      "title": "Gate-13 实验：四种预测器 / rank 扫描 / A-family 诊断 / conditional shuffle", "status": "complete",
      "payload": exp_payload}, "tU1-gate13exp")

covers = {"files": [".project-log/docs/phase2_gate_stage3_gate13_v1.md",
                    ".project-log/docs/phase2_gpt_handoff_v11.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_gate13.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-GATE13-FINALIZATION-001", "--kind", "research",
                    "--subject", "Gate-13 A-only finalization (propagation vs re-encoding)",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tU2-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "Gate-13（GPT 第十三轮 v1.2：A-only 定稿性检验）完成。**关键负结果**：13A 四种预测器对比——R_reencode（每步重编码，第12轮强结果）H20 −73.7%；"
    "F_reencode −556%、F_prop（frozen+开环传播）−738%、R_prop（scheduled+开环传播）−115% → **开环传播（frozen 或 scheduled）全部崩溃**，只有每步重编码保留增益；η_F 为负。"
    "13C 根因：ρ(A_k) median 1.032/max 1.043（>1，边际不稳定），A0 ρ=1.0299，乘积增长 ≈1.04/步 → 模型是'encoder 锚定的一步预测器'，非可独立传播的动力系统。"
    "13B：r=1 不足、r=2 最小近优（S_r 0.03722）；13D：matched-current history shuffle 下一步误差 6.63×（PASS）；13C 诊断：‖ΔA‖ q99 0.059/max 0.068、漂移 0.006、三模态活跃、gate 与速度/Δu 相关性≈0。"
    "产出 phase2_gate_stage3_gate13_v1.md + phase2_gpt_handoff_v11.md；记录 PHASE2-GATE13-FINALIZATION-001 / PHASE2-GATE13-EXPERIMENTS-001 / EV-PHASE2-GATE13-FINALIZATION-001。"
    "下一步（待 GPT 回复 handoff v11 §6）：(1) 控制架构二选一——(i) 重编码 MPC（encoder 在环，增益保留但预测器对 u 非线性）或 (ii) 稳定化 latent（budgeted low-rank + ‖ΔA‖≤δ_A + ρ/共同 P 约束，使开环传播可用；DEC-018 升级为 MPC 可用性前提）；"
    "(2) 有界性参数化与 δ_A（建议 0.065–0.09）；(3) common-P β* 是否要求；(4) r=2 定稿；(5) 重编码 MPC 实时性（P2 Ts≈0.2s）。GOAL-001 门禁仍拒绝；DEC-018 未满足。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tU3-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tU4-handoff")
print("rep_sha:", sha(REP)); print("hof_sha:", sha(HOF))
print("revision:", revision())
