import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
REP = Path(ROOT) / ".project-log" / "docs" / "phase2_gate_stage3_context_modulation_v1.md"
HOF = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v10.md"
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

rep_payload = {
    "document": ".project-log/docs/phase2_gate_stage3_context_modulation_v1.md",
    "document_sha256": sha(REP),
    "scope": "Full latent-pipeline structural gate for A+ (RSHC-TK): A/B/AB low-rank context modulation on real PatchTST-Koopman pipeline, P2 data, 2 seeds",
    "val_rollout_seed0": {
        "fixed": {"H1": 0.0234, "H5": 0.0728, "H10": 0.1075, "H20": 0.1689},
        "A_only": {"H1": 0.0090, "H5": 0.0209, "H10": 0.0310, "H20": 0.0444},
        "B_only": {"H1": 0.0190, "H5": 0.0688, "H10": 0.1129, "H20": 0.1824},
        "AB": {"H1": 0.0089, "H5": 0.0212, "H10": 0.0309, "H20": 0.0451},
    },
    "val_improve_pct_vs_fixed_seed0": {"A": {"H10": -71.1, "H20": -73.7}, "B": {"H10": 5.0, "H20": 8.0}, "AB": {"H10": -71.2, "H20": -73.3}},
    "val_improve_pct_vs_fixed_seed1": {"A": {"H10": -72.2, "H20": -74.3}, "B": {"H10": -4.3, "H20": -3.8}, "AB": {"H10": -70.6, "H20": -71.7}},
    "test_rollout_seed0": {"fixed": {"H20": 0.1754}, "A": {"H20": 0.0425}, "B": {"H20": 0.2017}, "AB": {"H20": 0.0456}},
    "deployed_anchor_edmd_P4": {"val_H20": 0.1588, "test_H20": 0.1610, "note": "comparable to end-to-end fixed -> baseline valid"},
    "falsification_seed0": {
        "A_modOFF_H20": 0.5072, "A_uhZERO_H20": 0.4927,
        "AB_modOFF_H20": 0.6059, "AB_uhZERO_H20": 0.4718,
        "note": "modulation-off and uh-history-zero both degrade H20 by ~11-13x -> gain is from modulation itself and depends on input history",
    },
    "verdicts": {
        "locus_is_A_not_B": "CONFIRMED - A-only -73.7%/-74.3% (2 seeds); B-only ~0 or worse at long horizon; contradicts round-11 observation-space proxy inference",
        "AB_vs_A_only": "no gain (73.3% vs 73.7% seed0; 71.7% vs 74.3% seed1) -> choose A-only",
        "why_not_transferable": "observation-space proxy d=J(phi)u can only modulate the input channel; latent A acts on z=[x;h] with h encoding history -> A(c) expresses history-dependent latent dynamics",
        "falsification": "PASS - gain from modulation (modOFF collapses) + uses input history (uhZERO collapses)",
    },
    "open": "boundedness/stability of modulation (needed for DEC-018), rank-r sensitivity, latent matched-state, CB(c) spectrum/PD, cross-sample history-shuffle",
}
apply("record.create", {"kind": "research", "id": "PHASE2-STAGE3-STRUCT-GATE-001",
      "title": "阶段③ 结构 gate（真实 latent 管线）：locus=A，非 B；AB 无增益；选 A-only", "status": "complete",
      "payload": rep_payload}, "tT0-gate")

exp_payload = {
    "document": ".project-log/docs/phase2_gate_stage3_context_modulation_v1.md",
    "document_sha256": sha(REP),
    "scripts": ["gate_context_koopman.py", "eval_deployed.py"],
    "artifacts": ["gate_result.json", "gate_result_s1.json", "gate_states/{fixed,A,B,AB}{,_s1}.pt"],
    "setup": "PatchTSTEncoder -> z=[x;h](d=10), z'=Az+Bu, decoder=first2; new context encoder over [x_history;u_history] -> c(16); low-rank modulation r=3; all modes identical training; seeds 0/1",
    "result": "A-only dominates (H20 -73.7%/-74.3%); B-only ~fixed (or worse at H>=10); AB ~= A-only; deployed EDMD P=4 anchor H20 0.1588 matches fixed baseline",
    "interpretation": "In the true latent pipeline the history-dependent modulation belongs on the state-transition A(c), reversing the round-11 observation-space proxy conclusion (which could not express A-modulation).",
}
apply("record.create", {"kind": "research", "id": "PHASE2-STRUCTGATE-EXPERIMENTS-001",
      "title": "结构 gate 实验：真实 latent 管线 A/B/AB 调制 + 证伪 + 部署锚点", "status": "complete",
      "payload": exp_payload}, "tT1-gateexp")

covers = {"files": [".project-log/docs/phase2_gate_stage3_context_modulation_v1.md",
                    ".project-log/docs/phase2_gpt_handoff_v10.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_structgate.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-STAGE3-STRUCT-GATE-001", "--kind", "research",
                    "--subject", "Stage-3 structural gate: latent-pipeline A/B/AB context modulation",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tT2-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "阶段③ 结构 gate 完成（DEC-023 解冻代码后首个实质实现）：在**真实 latent 管线**（PatchTSTEncoder→z=[x;h](d=10)、z'=Az+Bu、decoder=前2维）上，"
    "新增 context encoder（[x_history;u_history]→c∈R^16）+ 低秩调制（r=3），同流程训练 fixed/A/B/AB，两 seed。"
    "结果：A-only 支配（H20 val −73.7%/−74.3%），B-only ≈ fixed（seed0 长时域更差 −5~−8%），AB ≈ A-only（无增益）；"
    "部署 EDMD(P=4) 锚点 H20=0.1588 ≈ fixed 基线（可比）。证伪通过：modOFF H20 恶化 11.4×、uhZERO 11.1×。"
    "**结论：locus=A，不是 B；选 A-only**——第十/十一轮基于观测空间代理的 B-locus 推断不迁移（代理结构上无法表达 A 调制）。"
    "产出 phase2_gate_stage3_context_modulation_v1.md + phase2_gpt_handoff_v10.md；记录 PHASE2-STAGE3-STRUCT-GATE-001 / PHASE2-STRUCTGATE-EXPERIMENTS-001 / EV-PHASE2-STAGE3-STRUCT-GATE-001。"
    "下一步（待 GPT 回复 handoff v10 §6）：(1) 确认 locus=A 定稿 A+；(2) 调制有界性/稳定性界形式（配合 DEC-018 的 ρ(A)≤rho_max + 非平凡 T1′ 界）；(3) r 与 c 维度是否扫描；(4) 剩余 gate 项（latent matched-state、CB(c) 谱/PD、跨样本 history-shuffle）；(5) 阶段③ 实现清单与真机实验方案（用户执行）。"
    "GOAL-001 门禁仍拒绝；DEC-018 未满足（当前调制未加界）。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tT3-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tT4-handoff")
print("rep_sha:", sha(REP)); print("hof_sha:", sha(HOF))
print("revision:", revision())
