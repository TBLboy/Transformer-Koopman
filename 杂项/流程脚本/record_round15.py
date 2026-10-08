import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
REP = Path(ROOT) / ".project-log" / "docs" / "phase2_gate_stage3_gate14d_v1.md"
HOF = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v13.md"
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
    "document": ".project-log/docs/phase2_gate_stage3_gate14d_v1.md",
    "document_sha256": sha(REP),
    "scope": "Gate-14D: RTI-SQP real-time MPC, RTI-RE vs RTI-SP, N-sensitivity, iteration count",
    "N8_iter1": {"RTI_RE": {"rmse": 0.1438, "degradation_vs_oracle_pct": 5.8, "total_p50_ms": 292, "total_p95_ms": 347},
                 "RTI_SP": {"rmse": 0.1498, "degradation_vs_oracle_pct": 10.2, "total_p50_ms": 179, "total_p95_ms": 261}},
    "N5_iter1": {"RTI_RE": {"rmse": 0.1528, "total_p50_ms": 117, "total_p95_ms": 128},
                 "RTI_SP": {"rmse": 0.1588, "total_p50_ms": 69, "total_p95_ms": 78}},
    "N5_iter2": {"RTI_RE": {"rmse": 0.1554, "total_p95_ms": 651}, "RTI_SP": {"rmse": 0.1624, "total_p95_ms": 349},
                 "verdict": "no accuracy gain, 2x slower -> reject"},
    "runtime_gate": {"RTI_SP_N5": "Strong GO (<100ms, 78ms)", "RTI_RE_N5": "GO (100-150ms, 128ms)",
                     "both_N8": "NO-GO (>=180ms)"},
    "perf_gate": {"RTI_SP_vs_oracle": "FAIL (+10.2% N8 / +16.8% N5 vs 5-8% gate)",
                  "RTI_RE_vs_oracle_N8": "PASS (+5.8%)",
                  "caveat": "oracle ref is N=8; N=5 oracle would be worse -> N=5 degradation overestimated"},
    "verdict": "Conditional GO: runtime passes (RTI-SP N=5 78ms); accuracy borderline (proxy plant-limited + N-mismatched oracle). RTI-SP ~1.6x faster than RTI-RE. N is the decisive knob.",
    "open_for_gpt": "accept RTI-SP N=5 1-iter for hardware?; re-measure N=5 matched oracle?; optimize rollout impl?; proceed to P2 hardware?",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GATE14D-RTI-001",
      "title": "Gate-14D：RTI-SP N=5 p95=78ms（Strong GO），RTI-RE 128ms（GO）；1 次迭代足够", "status": "complete",
      "payload": payload}, "tW0-gate14d")

exp_payload = {
    "document": ".project-log/docs/phase2_gate_stage3_gate14d_v1.md",
    "document_sha256": sha(REP),
    "scripts": ["gate14d_rti.py"],
    "artifacts": ["gate14d_result.json", "gate14d_result_N5.json", "gate14d_result_N5_it2.json"],
    "method": "RTI-SQP 1-iter: warm start -> nominal rollout -> autograd Jacobian linearization -> LTV-QP (L-BFGS-B, box) -> apply first step.",
    "RTI_RE": "re-run full PatchTST encoder each stage (A-only r2 model).",
    "RTI_SP": "rollout-trained scheduled propagation (latent propagated, context rescheduled; A_openloop model); no PatchTST per stage.",
    "findings": "RTI-SP 1.6x faster than RTI-RE; N=5 brings RTI-SP to Strong GO (78ms); 2 iterations do not improve RMSE and double runtime.",
    "solver_fail_pct": 0.0,
}
apply("record.create", {"kind": "research", "id": "PHASE2-GATE14D-EXPERIMENTS-001",
      "title": "Gate-14D 实验：RTI-SQP 实时性（RTI-RE vs RTI-SP, N=8/5, 1/2 iter）", "status": "complete",
      "payload": exp_payload}, "tW1-gate14dexp")

covers = {"files": [".project-log/docs/phase2_gate_stage3_gate14d_v1.md",
                    ".project-log/docs/phase2_gpt_handoff_v13.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_gate14d.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-GATE14D-RTI-001", "--kind", "research",
                    "--subject", "Gate-14D RTI real-time MPC",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tW2-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "Gate-14D（GPT 第十五轮 v1.0，唯一剩余 Gate）完成。**实时性**：RTI-SP 比 RTI-RE 快 ~1.6×（每 stage 不跑 PatchTST）。"
    "**N 是决定性旋钮**：N=8 两者 NO-GO（RTI-SP p95 261ms / RTI-RE 347ms）；**N=5 时 RTI-SP p95=78ms（Strong GO）、RTI-RE 128ms（GO）**。"
    "**迭代数**：2 次 SQP 无精度改善且耗时翻倍（SP 349ms / RE 651ms）→ **1 次迭代为准**。"
    "**精度**：RTI-SP vs oracle +10.2%(N=8)/+16.8%(N=5)（超 5–8% 门槛）；RTI-RE N=8 +5.8%（在门槛内）。"
    "**关键 caveat**：oracle 参考是 N=8（0.1360），N=5 的 oracle 会更差→N=5 退化百分比被高估；闭环代理 plant=DirectNN 限制精度（绝对差异 0.14–0.16 很小）。"
    "**判决**：实时性 GO；精度 borderline；**综合 Conditional GO**——建议以 RTI-SP N=5（或 N=6）进真机，进入前补 (a) N=5 匹配 oracle、(b) 更快 rollout 实现。严格按 §14=NO-GO、按 §13=GO，张力源于 N/oracle 不匹配。"
    "产出 phase2_gate_stage3_gate14d_v1.md + phase2_gpt_handoff_v13.md；记录 PHASE2-GATE14D-RTI-001 / PHASE2-GATE14D-EXPERIMENTS-001 / EV-PHASE2-GATE14D-RTI-001。"
    "下一步（待 GPT 回复 handoff v13 §请 GPT 裁定）：(1) 是否接受 RTI-SP N=5 1-iter 为真机配置；(2) 是否补 N=5 匹配 oracle；(3) 是否优化 rollout 实现；(4) 是否直接进 P2 真机（E1–E5，用户执行）。GOAL-001 门禁仍拒绝。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tW3-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tW4-handoff")
print("rep_sha:", sha(REP)); print("hof_sha:", sha(HOF))
print("revision:", revision())
