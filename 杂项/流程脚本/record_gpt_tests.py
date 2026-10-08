import json
import subprocess
import sys
import hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

DOC = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_route_tests_abc_v0.1.md"
sha = hashlib.sha256(DOC.read_bytes()).hexdigest()

def revision():
    p = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(p.stdout.decode("utf-8", "replace"))["revision"]

def apply(action, payload, tag):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(), "action": action, "payload": payload}
    path = f"{TMP}/env_{tag}.json"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    p = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path], capture_output=True)
    print(("OK   " if p.returncode == 0 else "FAIL ") + tag)
    if p.returncode:
        print(p.stderr.decode("utf-8", "replace")[:1500])

payload = {
    "document": ".project-log/docs/phase2_gpt_route_tests_abc_v0.1.md",
    "document_sha256": sha,
    "task": "验证 GPT 报告中的路线，只做验证与反馈，不构思新路线",
    "gpt_report_routes": ["R1 Reachability-Aligned", "R2 Gauge-Invariant", "R3 Residual-Dynamics",
                          "R4 Output-Predictive", "R5 Actuated/Transverse", "R6 Gramian Norm", "R7 Balanced",
                          "R8 Reference Manifold", "R9 Physical Metric", "R10 Control-effect Jacobian",
                          "R11 P2 Differential Quotient", "R12 Residual Whitening", "R13 Finite-Horizon Realization",
                          "R14 Control-relevant Error", "R15 Joint Reference Generator", "R16 Dual-Encoder",
                          "R17 Cross-Platform", "R18 Closed-loop Defect Decomposition"],
    "tests": {
        "A_gauge_pathology": {
            "physical_prediction_invariance_error": 1.5e-13,
            "control_law_rel_diff": {"condT_1": 1e-7, "condT_1e2": "0.37-0.77", "condT_1e4": "1.0-9.2", "condT_1e6": "0.9-1.5"},
            "physical_tracking_rel_diff": {"condT_1e2": "0.66-0.83", "condT_1e4": "1.3-2.8", "condT_1e6": "~1e87/inf"},
            "dare_failures_condT_1e6": "3/4",
            "verdict": "gauge dependence confirmed, BUT it is the known LQR covariant-invariance fact; fixing Q is a gauge choice; R2 novelty weak",
        },
        "B_ref_reachability_defect": {
            "median_relative_defect_train": 0.167, "median_relative_defect_val": 0.162,
            "mean_relative_defect_train": 0.216, "mean_relative_defect_val": 0.213,
            "verdict": "first-order unreachable component is ~16-21% of lifted reference increment; R1 premise supported; multi-step not tested",
        },
        "C_residual_predictability": {
            "AR1_improvement_joint1_2_3": [0.243, 0.194, 0.170],
            "AR4_improvement_joint1_2_3": [0.245, 0.205, 0.186],
            "verdict": "residual has predictable dynamics (17-25%); R3 premise supported",
        },
    },
    "prior_art_R1_R2_R3": {
        "R1": "delta exists but narrow; key delta = use reachability defect as representation-learning loss + multi-step reachable-subspace alignment; precedents: Korda-Mezic Automatica 2018 (arXiv:1611.03537), KTMPC arXiv:2208.12000, ScaRe-Kro arXiv:2601.01076, arXiv:2607.06459",
        "R2": "HIGH risk: LQR similarity invariance under covariant cost is a 1984 result (Majumdar 1984; Al-Iedani & Gajic 2020); fixing Q = choosing a gauge; physical-output cost (C^T Q C) is the standard fix (KF-LQR arXiv:2201.11640); KEEC arXiv:2312.01544 already enforces 'equivalent predictor -> equivalent control'",
        "R3": "method overlaps DEKC arXiv:2506.08319 and discrepancy modeling arXiv:2203.05164; needs a control-oriented theorem (identifiability / closed-loop bound / vs DOB-ESO condition)",
    },
    "scripts": [
        "testA_gauge_v2.py", "testA_gauge_v3.py", "testB_ref_defect.py", "testC_residual_ar.py",
    ],
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-ROUTES-001", "title": "GPT 路线验证：Test A/B/C 与 R1-R3 prior-art", "status": "complete", "payload": payload}, "t58-gpt")

next_action = (
    "已接收 GPT 18 条路线报告，按用户要求只做验证与反馈。已跑三项便宜测试："
    "Test A（R2 前提）gauge 病理成立：预测完全不变(1.5e-13)，固定 Q 的 LQR 在病态 gauge 下控制律/闭环显著改变、condT=1e6 时 DARE 失败；但本质是已知 LQR 协变不变性，固定 Q 只是选定 gauge → R2 新颖性弱。"
    "Test B（R1 前提）参考不可达缺陷成立：约 16~21% lifted 参考增量落在 im(B) 外（仅一阶，多步未验证）。"
    "Test C（R3 前提）P1 残差可预测：AR(1) 改善 17~25%。"
    "prior-art：R1 delta 窄但实在（关键=把不可达残差作表示学习损失+多步可达）；R2 风险最高（1984 已知结果，需新不变量）；R3 需面向控制的定理。"
    "R4-R18 prior-art 复核进行中。下一步：汇总 R1-R18 逐条可行性验证报告。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t58-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t58-handoff")
print("doc_sha256:", sha)
print("revision:", revision())
