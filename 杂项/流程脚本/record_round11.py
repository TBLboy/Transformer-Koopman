import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
VAL = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_round11_routeAplus_validation_v1.md"
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
    "document": ".project-log/docs/phase2_gpt_round11_routeAplus_validation_v1.md",
    "document_sha256": sha(VAL),
    "scope": "GPT round-11 A+ (RSHC-TK) two core claims validation on existing P2 data",
    "ablation_rollout_val_rmse": {
        "base_additive_context": {"H1": 0.0590, "H5": 0.4190, "H10": 1.0622, "H20": 2.0140},
        "A_only": {"H1": 0.0451, "H5": 0.2392, "H10": 0.6126, "H20": 1.1719},
        "B_only": {"H1": 0.0415, "H5": 0.2196, "H10": 0.4191, "H20": 0.6583},
        "AB": {"H1": 0.0361, "H5": 0.1933, "H10": 0.3798, "H20": 0.6081},
    },
    "vs_base_pct": {"A": {"H10": -42.3, "H20": -41.8}, "B": {"H10": -60.5, "H20": -67.3}, "AB": {"H10": -64.2, "H20": -69.8}},
    "B_vs_AB_pct": {"H1": 12.8, "H5": 12.0, "H10": 9.4, "H20": 7.6},
    "matched_state_history_test": {"n_pairs": 199, "resp_diff_similar_history": 0.0892,
                                   "resp_diff_different_history": 0.2889, "ratio": 3.24},
    "verdicts": {
        "claim1_B_is_locus": "CONFIRMED - B-only (H20 -67%) >> A-only (H20 -42%); history modulates the control channel",
        "claim2_matched_state": "CONFIRMED - same x,u with different history gives 3.24x larger next-response difference",
        "structure_choice": "AB only 7.6-9.4% better than B-only -> grey zone; recommend B-only first (simpler, more distinct from generic time-varying Koopman)",
    },
    "prior_art": "arXiv 2606.23957 and 2505.00354 verified real; MamKO (ICLR 2025) not on arXiv; journal DOIs unverifiable. GPT map directionally correct.",
    "proxy_caveat": "observation-space proxy, not full latent pipeline; needs Phase-3 reproduction.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-ROUND11-APLUS-001",
      "title": "第十一轮 A+ 验证：B(c) 是历史依赖主要载体（B-only>>A-only），matched-state 差异 3.24x", "status": "complete",
      "payload": val_payload}, "tS0-aplus")

exp_payload = {
    "document": ".project-log/docs/phase2_gpt_round11_routeAplus_validation_v1.md",
    "document_sha256": sha(VAL),
    "scripts": ["V_APLUS.py"],
    "ablation": "On top of additive-context base, B-modulation beats A-modulation decisively (H20: -67.3% vs -41.8%); AB adds only 7.6-9.4% over B-only.",
    "matched_state": "Same current state + similar command, different history -> 3.24x larger next-step response difference (n=199).",
    "interpretation": "History-conditioned control-channel B(c) modulation is the empirically dominant mechanism; strong motivation for A+ (RSHC-TK).",
}
apply("record.create", {"kind": "research", "id": "PHASE2-APLUS-EXPERIMENTS-001",
      "title": "A+ 结构 gate：A/B/AB 消融 + matched-state history test", "status": "complete",
      "payload": exp_payload}, "tS1-aplusexp")

covers = {"files": [".project-log/docs/phase2_gpt_round11_routeAplus_validation_v1.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_aplus.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-GPT-ROUND11-APLUS-001", "--kind", "research",
                    "--subject", "Round-11 A+ (RSHC-TK) structural validation",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tS2-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "第十一轮（GPT 深度重规划 v1.1，A+ = Response-Structured History-Conditioned Transformer-Koopman）验证完成。"
    "① A/B/AB 结构消融（P2 现有数据，加法 context 基线上叠加低秩调制）：B-only 大幅优于 A-only（H=20：−67% vs −42%，相对 base），证实 GPT 修正——history 主要调制控制通道 B(c) 而非 A；AB 仅比 B-only 好 7.6–9.4%（灰区）。"
    "② matched-state history test：相同 x、相似 u、不同 history 的下一步响应差异是相似 history 的 3.24×（n=199）——强动机。"
    "③ prior-art：2606.23957/2505.00354 真实；MamKO(ICLR2025) 未在 arXiv 检索到；其余期刊 DOI 无法独立核实；GPT 文献图方向正确。"
    "产出 phase2_gpt_round11_routeAplus_validation_v1.md；记录 PHASE2-GPT-ROUND11-APLUS-001 / PHASE2-APLUS-EXPERIMENTS-001 / EV-PHASE2-GPT-ROUND11-APLUS-001。"
    "结构推荐：优先 B-only（≈AB 的 90%，且更简洁、更易与 generic 时变 Koopman 划界）；若真实 pipeline 上 AB 稳定 >8–10% 再切 AB。"
    "待用户裁定（延续前轮）：(1) 更新 DEC-021 解读（接受工程型 novelty 定位）；(2) 阶段③范围（重采 P2 + 真机闭环）与代码/论文冻结、DEC-022 的边界；(3) B-only vs AB 结构终选。"
    "下一步按 GPT §60：在**真实 latent pipeline** 上跑 fixed/A-only/B-only/AB 结构 gate + history-shuffle + modulation-nullification + matched-state，再决定是否进入阶段③。GOAL-001 门禁仍拒绝；代码/配置/论文冻结。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tS3-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tS4-handoff")
print("val_sha:", sha(VAL))
print("revision:", revision())
