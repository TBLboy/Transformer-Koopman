import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
REP = Path(ROOT) / ".project-log" / "docs" / "phase2_gate_stage3_gate14_v1.md"
HOF = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v12.md"
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
    "document": ".project-log/docs/phase2_gate_stage3_gate14_v1.md",
    "document_sha256": sha(REP),
    "scope": "Gate-14: manifold defect, stabilization rescue, open-loop training, direct NN baseline, control proxy, runtime",
    "gate14A_manifold_defect": {"R_prop_dM_H1_5_10_20": [0.19, 0.64, 0.94, 1.45],
                                "R_prop_err_H1_5_10_20": [0.0075, 0.042, 0.107, 0.287],
                                "corr_dM_err_H5_10_20": [0.54, 0.57, 0.49], "verdict": "PASS"},
    "gate14B_stabilization": {
        "baseline_A_r2": {"R_reencode_H20": 0.0439, "F_prop_H20": 1.412, "R_prop_H20": 0.368, "rho": 1.032},
        "one_step_rho099": {"R_reencode_H20": 0.0486, "F_prop_H20": 1.817, "R_prop_H20": 1.568, "rho": 0.989},
        "openloop_rho099": {"R_reencode_H20": 0.0403, "F_prop_H20": 1.138, "R_prop_H20": 0.0412, "rho": 0.989},
        "openloop_norho": {"R_reencode_H20": 0.0430, "F_prop_H20": 1.129, "R_prop_H20": 0.0418, "rho": 1.030},
        "verdict": "stabilization alone FAILS (stable route closed); open-loop training RESCUES scheduled propagation (0.368->0.041, 9x), independent of rho"},
    "direct_nn": {"val_H20": 0.2596, "A_only_val_H20": 0.0439, "params": [6570, 6714], "verdict": "Koopman 5.9x better"},
    "gate14C_control": {"C0_fixed": 0.1367, "C2_aonly": 0.1360, "C2b_aol_sched": 0.1411, "C1_frozen": 0.2135,
                        "plant_sensitivity_C2_vs_C0_pct": {"dnn": 2.7, "aonly": 3.8, "fixed": -8.5},
                        "verdict": "C1 fails; A-only control gain only ~3% (<< 10% gate); modeling gain does not translate proportionally to closed-loop gain"},
    "gate14E_runtime_ms": {"C0": [2965, 5502], "C2": [3533, 4213], "C2b": [2349, 2818], "C1": [952, 1273], "verdict": "oracle SLSQP FAIL (>200ms); RTI needed"},
    "open_for_gpt": "how to handle ~3% control gain vs 10% gate; adopt open-loop-trained scheduled predictor?; implement RTI (14D)?; hardware timing",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GATE14-ANALYSIS-001",
      "title": "Gate-14：manifold defect PASS；稳定化 FAIL 但开环训练修复 scheduled 传播；Koopman 胜 DirectNN 5.9×；控制增益仅 ~3%", "status": "complete",
      "payload": payload}, "tV0-gate14")

exp_payload = {
    "document": ".project-log/docs/phase2_gate_stage3_gate14_v1.md",
    "document_sha256": sha(REP),
    "scripts": ["gate14_stabilize.py", "gate14a_manifold.py", "gate14_directnn.py", "gate14c_control.py", "gate14c2_plantsens.py"],
    "artifacts": ["gate14_result.json", "gate14a_result.json", "gate14_directnn_result.json", "gate14c_result.json"],
    "gate14A": "d_M grows 0.19->1.45, corr with RMSE 0.49-0.57; open-loop training reduces defect and error 0.287->0.037.",
    "gate14B": "Budgeted low-rank + rho<=0.99 does NOT rescue propagation (R_prop 0.368->1.568); open-loop (scheduled) training rescues it (0.368->0.041) even without rho penalty.",
    "direct_nn": "DirectNN H20 0.2596 vs Koopman 0.0439 at equal params.",
    "gate14C": "Closed-loop proxy (plant=DirectNN): C1 frozen fails (0.2135 vs 0.136); C0~C2 (~3% gain).",
    "gate14E": "Oracle SLSQP med 2965ms; RTI required.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GATE14-EXPERIMENTS-001",
      "title": "Gate-14 实验：稳定化/开环训练/DirectNN/闭环控制代理/实时性", "status": "complete",
      "payload": exp_payload}, "tV1-gate14exp")

covers = {"files": [".project-log/docs/phase2_gate_stage3_gate14_v1.md",
                    ".project-log/docs/phase2_gpt_handoff_v12.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_gate14.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-GATE14-ANALYSIS-001", "--kind", "research",
                    "--subject", "Gate-14 manifold/stabilization/directNN/control",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tV2-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "Gate-14（GPT 第十四轮 v1.3）完成。**两个关键负结果**："
    "(1) 稳定化救不了传播——budgeted low-rank+ρ≤0.99 使 R_prop 更差（0.368→1.568），GPT 预判正确，stable-latent 主路线关闭；"
    "**但开环（scheduled 传播）训练把 R_prop 从 0.368 修到 0.041（9×，≈重编码），且不压 ρ 也行**（修复来自训练目标）→ 可用更便宜的 scheduled-propagation 预测器替代每步重编码。F_prop（冻结）仍失败。"
    "(2) **控制增益只有 ~3%**：闭环代理（plant=独立 DirectNN，N=8 SLSQP oracle）C0 0.1367 vs C2 0.1360（plant 敏感 +2.7~3.8%），远低于 GPT §40 的 10% 门槛——**建模增益(−74%)不能按比例转化为闭环控制增益**（receding-horizon+重锚定抵消了多步优势）；C1 frozen 差 56%（确认不可用）。"
    "其余：14A manifold defect PASS（d_M 0.19→1.45，corr 0.49–0.57，证实 GPT 根因）；DirectNN H20 0.2596 vs Koopman 0.0439（5.9×，回答为何用 Koopman）；14E oracle SLSQP med 2965ms/p95 5502ms（FAIL，需 RTI）。"
    "产出 phase2_gate_stage3_gate14_v1.md + phase2_gpt_handoff_v12.md；记录 PHASE2-GATE14-ANALYSIS-001 / PHASE2-GATE14-EXPERIMENTS-001 / EV-PHASE2-GATE14-ANALYSIS-001。"
    "下一步（待 GPT 回复 handoff v12 §6）：(1) 控制增益仅 ~3% 如何处理（接受 model 为主创新进真机 / 改进离线代理 / 重定位 controller）；(2) 是否采用开环训练的 scheduled-propagation 预测器；(3) 是否实现 14D RTI；(4) 真机时序。GOAL-001 门禁仍拒绝；DEC-018 重新解释（稳定化非主路线）。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tV3-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tV4-handoff")
print("rep_sha:", sha(REP)); print("hof_sha:", sha(HOF))
print("revision:", revision())
