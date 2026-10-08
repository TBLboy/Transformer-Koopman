import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
REP = Path(ROOT) / ".project-log" / "docs" / "phase2_round16_matched_oracle_theory_v1.md"
HOF = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v14.md"
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

# ---- decision: route-level research CLOSED, freeze RTI-SP ----
apply("record.create", {"kind": "decision", "id": "DEC-024",
      "title": "路线级研究 CLOSED：冻结 RTI-SP/N=5/1-iter，停止架构/控制器/runtime 搜索",
      "status": "active",
      "payload": {
        "level": "C",
        "basis": "GPT 第十六轮裁定（用户转发）+ matched oracle 实证 RTI-SP PASS",
        "decision": "阶段②/③ 路线级研究正式 CLOSED。模型冻结（A-only, r=2, fixed B/C, history-conditioned transition, rollout-aware scheduled training）；控制器冻结（HC-RKMPC + RTI-SP, N=5, 1 SQP iteration）。停止：B-only/AB/bilinear/mixture/stable-Koopman/higher-rank/新 encoder；2+ SQP 迭代；N=8 硬件路线；runtime 深度优化（当前 p95 78–120ms ≪ 200ms）。",
        "consequence": "唯一剩余离线控制实验（N=5 matched oracle）已完成并通过 → P2 真机 E1–E5 可开始（用户执行）。理论侧并行做 Theory Diagnostics（已完成）→ 正式化 Prop.1/2、Thm.1、Prop.3 → 论文理论章节。",
        "reopen_condition": "仅当 matched oracle 或真机出现灾难性反例，或完整真机 loop p95 ≳180ms 时才重开对应子问题。",
        "evidence": "phase2_round16_matched_oracle_theory_v1.md; phase2_gpt_handoff_v14.md",
      }}, "tX0-dec024")

# ---- matched oracle result ----
payload = {
    "document": ".project-log/docs/phase2_round16_matched_oracle_theory_v1.md",
    "document_sha256": sha(REP),
    "scope": "N-matched exact oracle vs RTI (same plant), N=5 and N=8",
    "plant": "DirectNN trained once and saved (plant_dnn.pt), val_loss 0.000285",
    "N5": {"oracle_sched": 0.1635, "rti_sp": 0.1618, "delta_rti_sp_pct": -1.04,
           "oracle_reencode": 0.1582, "rti_re": 0.1565, "delta_rti_re_pct": -1.05,
           "rti_sp_p50_ms": 78, "rti_sp_p95_ms": 120},
    "N8": {"oracle_sched": 0.1502, "rti_sp": 0.1496, "delta_rti_sp_pct": -0.37,
           "oracle_reencode": 0.1447, "rti_re": 0.1439, "delta_rti_re_pct": -0.60,
           "rti_sp_p50_ms": 200, "rti_sp_p95_ms": 215},
    "horizon_effect": "same plant N=8->N=5: oracle_sched +8.9%, oracle_reencode +9.3%, rti_sp +8.2% -> all controllers degrade ~8-9% -> earlier +16.8% was N/oracle mismatch artifact",
    "verdict": "Delta_RTI <= 0 (<<5-8% gate) -> RTI-SP PASS; matched oracle complete, no catastrophic result -> P2 hardware GO (GPT §22)",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GATE16-MATCHED-ORACLE-001",
      "title": "N-matched oracle：Δ_RTI_SP=-1.04% → RTI-SP 正式 PASS；退化主因是 horizon 非 RTI 近似", "status": "complete",
      "payload": payload}, "tX1-matched")

# ---- theory diagnostics ----
diag = {
    "document": ".project-log/docs/phase2_round16_matched_oracle_theory_v1.md",
    "document_sha256": sha(REP),
    "model": "A_openloop r=2 scheduled propagation (frozen deployment predictor)",
    "eps_k": {"median": 0.345, "q90": 0.516, "q95": 0.567, "q99": 0.655, "max": 0.800},
    "dM": {"H1": 0.120, "H5": 0.390, "H10": 0.574, "H20": 0.928},
    "prod_norm": {"H1": 1.046, "H5": 1.247, "H10": 1.541, "H20": 2.304},
    "dF_dxi": {"median": 1.445, "q90": 1.448, "q95": 1.450, "q99": 1.451, "max": 1.452},
    "bound_over_actual": {"H1": 4.71, "H5": 7.95, "H10": 12.1, "H20": 18.7},
    "lin_remainder_M_F": {"1e-3": 0.272, "1e-2": 0.015},
    "rti_runtime_ms": {"p50": 78, "p95": 120},
    "interpretation": "product norm grows (no contraction) matching dM growth -> §14; empirical L_F~1.45>1 -> Thm.1 finite-horizon applies; bound>=actual (Thm.1 sanity PASS); small linearization remainder (Prop.3); nonzero eps_k confirms train/deploy distribution gap (§15).",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GATE16-THEORY-DIAG-001",
      "title": "Theory Diagnostics：ε_k/d_M/乘积范数/经验 L_F/bound/线性化余项，全部与 Prop.1/2、Thm.1、Prop.3 一致", "status": "complete",
      "payload": diag}, "tX2-diag")

covers = {"files": [".project-log/docs/phase2_round16_matched_oracle_theory_v1.md",
                    ".project-log/docs/phase2_gpt_handoff_v14.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_gate16.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-GATE16-MATCHED-ORACLE-001", "--kind", "research",
                    "--subject", "Round-16 matched oracle + theory diagnostics",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tX3-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "Round-16（GPT 第十六轮 v1.0）完成：**路线级研究 CLOSED（DEC-024）**。"
    "**matched oracle（唯一剩余离线控制实验）通过**：同一 plant 下 N=5 Δ_RTI_SP=−1.04%（oracle 0.1635 vs RTI-SP 0.1618）、Δ_RTI_RE=−1.05%；N=8 Δ_RTI_SP=−0.37% → **RTI-SP 正式 PASS**（≪5–8% 门槛）。"
    "**关键澄清**：同 plant 下 N=8→N=5 使 exact 与 RTI **同步**退化 ~8–9%（oracle_sched +8.9%/oracle_reencode +9.3%/rti_sp +8.2%）→ 早先 '+16.8%' 系 N/oracle 不匹配假象，非 RTI 近似损失。"
    "**Theory Diagnostics 完成**：ε_k median 0.345；d_M(H) 0.120/0.390/0.574/0.928（H=1/5/10/20）；乘积范数 1.046/1.247/1.541/2.304（无收缩）；经验 L_F≈1.45>1；Prop.2 bound≥actual（保守 4.7–18.7×，Thm.1 sanity PASS）；线性化余项 M_F≤0.27（Prop.3 成立）。"
    "产出 phase2_round16_matched_oracle_theory_v1.md + phase2_gpt_handoff_v14.md；记录 DEC-024 / PHASE2-GATE16-MATCHED-ORACLE-001 / PHASE2-GATE16-THEORY-DIAG-001 / EV-PHASE2-GATE16-MATCHED-ORACLE-001。"
    "**下一步**：(1) 待 GPT 回复 handoff v14 确认最终真机配置与理论封稿；(2) **P2 真机 E1–E5 可开始（用户执行）**——multi-setpoint / circle / figure-eight / unseen / speed shift；真机完整 loop 接入后若 p95 ≳180ms 再开 runtime 优化；(3) 理论侧正式化 Prop.1/2、Thm.1、Prop.3 → 论文理论章节。GOAL-001 门禁仍拒绝（真机结果尚未产生）。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tX4-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tX5-handoff")
print("rep_sha:", sha(REP)); print("hof_sha:", sha(HOF))
print("revision:", revision())
