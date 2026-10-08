import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

DOC = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_route_validation_v2_l3.md"
sha = hashlib.sha256(DOC.read_bytes()).hexdigest()

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

payload = {
    "document": ".project-log/docs/phase2_gpt_route_validation_v2_l3.md",
    "document_sha256": sha,
    "method": "L3 full-text comparison + R16 dedicated negative scan (arXiv API)",
    "l3_full_texts": [
        "2509.17010 (Generalized Momenta-Based Koopman)",
        "2606.02938 (Lazar Khatri-Rao GeKo)",
        "2603.27548 (Haseli-Cortes-Burdick Control Forward-Backward Consistency)",
        "2601.11901 (Wu et al. Least-Squares Multi-Step Koopman for MPC)",
    ],
    "key_collisions_confirmed": {
        "R1": "multi-step Koopman learning occupied: 2601.11901, 2606.02938, 2405.01292, Korda-Mezic; multi-step version trivial at H>=dim (full controllability)",
        "R2": "basis/gauge-invariant control-accuracy measure = CCI (2603.27548 Prop IV.4); also 2603.15091, 2311.13033",
        "R4": "2606.02938 + 2405.01292 Koopman-SPC",
        "R5": "2509.17010 actuated/unactuated decoupling, learn only passive dynamics",
        "R7": "GeKo input lifting",
        "R16": "control/action sufficiency concept occupied in RL/VLA: 2507.19437, 2601.22496, 2110.05721, 2605.24890, 2605.01694",
        "R18": "invariance proximity 2311.13033; 2603.27548",
    },
    "r16_negative_scan": {
        "phrase_goal_conditioned_koopman": 0,
        "phrase_action_or_control_sufficient": 22,
        "nearest_direct_hit": "arXiv:2601.22496 Action-Sufficient Goal Representations (GCRL, 2026)",
        "verdict": "concept occupied on RL/VLA side; naming space empty; only Koopman-specific control-sufficiency remains",
    },
    "r1_multistep_result": {
        "H=1_train_mean_rel": 0.2162, "H=2_train_mean_rel": 0.0909, "H=3_train_mean_rel": 0.0326,
        "H=4_train_mean_rel": 0.00385, "H=6_train_mean_rel": 1.9e-16,
        "interpretation": "defect -> 0 for H>=controllability index (rank 10/10); multi-step reachability trivially satisfied; only H=1 (~17-22%) has content, approx standard latent one-step consistency residual",
    },
    "combos": {"A(R1+R15+R18)": "mixed/not recommended", "B(R2+R9+R4)": "not recommended",
               "C(R3+R12+R18)": "best P1-fit but still insufficient", "D(R4+R13+R2)": "not recommended"},
    "feedback_to_gpt": "downgrade/rename R1,R2,R4,R5,R6,R9,R10,R13,R15,R18; R16 only conceptual space but must be distinguished from action/control-sufficiency and CCI; R3 needs P1 control theorem; next report must give mechanism-level (provable-proposition) differences, not names",
    "evidence_level": "L3 for 4 papers; L2 for others; some 2026 arXiv IDs need re-verification",
    "user_directive": "validate + feedback only, do not invent new routes",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-ROUTE-VALIDATION-003",
      "title": "GPT 18 路线 L3 全文对拍 + R16 负面扫描：R1/R2/R16 全部收窄，无新颖主结果",
      "status": "complete", "payload": payload}, "t70-val3")

next_action = (
    "GPT 18 路线验证完成（L1/L2 全覆盖 + 4 篇 L3 全文 + R16 负面扫描）。"
    "L3 结论：R1 多步版本对本系统（完全可控，秩10/10）在 H≥dim 平凡成立（缺陷→0；H=1 仅 17~22% 且≈标准隐空间一步残差），"
    "多步 Koopman 学习已被 2601.11901/2606.02938/2405.01292 占满；R2 的基不变控制精度量=CCO/CCI 已由 2603.27548 建立（gate 不变，作紧界与损失）；"
    "R5 被 2509.17010 广义动量解耦占位；R16 概念在 RL/VLA 侧被 2507.19437/2601.22496/2110.05721/2605.24890 占满，\"goal-conditioned Koopman\" 精确短语 arXiv 0 命中（仅 Koopman 专属控制充分性为残余）。"
    "无任何路线可作阶段② 主结果；DEC-018 未满足；GOAL-001 门禁仍拒绝。"
    "产出：phase2_gpt_route_validation_v2_l3.md + PHASE2-GPT-ROUTE-VALIDATION-003。"
    "下一步：向用户呈报反馈结论（不构思新路线，遵守用户指令），等待用户就'是否继续在残余空间（Koopman 专属控制充分性 / P1 残差控制定理）内深挖，或调整阶段②目标'做 C 级决策。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t70-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t70-handoff")
print("doc_sha256:", sha)
print("revision:", revision())
