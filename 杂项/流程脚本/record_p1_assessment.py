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

DOC = Path(ROOT) / ".project-log" / "docs" / "phase2_p1_only_assessment_v0.1.md"
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
    "document": ".project-log/docs/phase2_p1_only_assessment_v0.1.md",
    "document_sha256": sha,
    "p1_input_semantics_confirmed": "joint torque / current command",
    "p1_structure": "fully observed 3-DOF Euler-Lagrange arm, x=(q,qdot), torque input, gravity offset on joint 2",
    "prior_art_direct_occupation": {
        "arxiv_2509.17010": "Generalized Momenta-Based Koopman Formalism for Robust Control of Euler-Lagrangian Systems (Singh et al., 2025-09/v2 2026-02): decouples known linear actuation channel, learns unactuated dynamics, GESO, manipulator experiments.",
        "cdc_2024_event_triggered_el_koopman": "Zheng et al., 10.1109/cdc56724.2024.10886671",
        "ieee_access_2026_arm_koopman": "Hancioglu & Efe, 10.1109/access.2026.3652500",
    },
    "structured_lifting_spike": {
        "raw_affine_val_rmse": 0.22556271591053131,
        "structured_physics_val_rmse": 0.22292837258961862,
        "multi_step_structured_h2_val_rmse": 0.36781751195039136,
        "multi_step_structured_h3_val_rmse": 0.4820584726617948,
        "verdict": "handcrafted physics features give no meaningful advantage; structured lifting is not a route by itself",
    },
    "candidate_p1_deltas_not_yet_approved": [
        "finite-data closed-loop tracking bound for momentum-structured torque-driven arm",
        "passivity/positive-definiteness preserving data-driven lifting with passive controller",
        "unified full-state and partial-observation closed-loop bound with history-as-observer",
    ],
    "verdict": "P1-only is crowded and the naive structured lifting shows no data advantage. A P1-only route requires a specific, defended delta; otherwise escalate to data collection or scope decision.",
    "scripts": [
        "C:/Users/12187/AppData/Local/Temp/opencode/profile_p1_data.py",
        "C:/Users/12187/AppData/Local/Temp/opencode/spike_p1_structured_lifting.py",
    ],
}
apply("record.create", {"kind": "research", "id": "PHASE2-P1-ONLY-ASSESS-001", "title": "P1 输入语义确认与 P1-only 物理路线评估", "status": "complete", "payload": payload}, "t55-p1")

next_action = (
    "用户确认 P1 输入=关节力矩/电流指令（第2关节力矩含明显重力偏置），P1 为全状态 EL 系统；选择先评估 P1-only。"
    "评估结论：P1-only 主结构（EL+力矩+动量结构+Koopman+鲁棒控制）已被 arXiv:2509.17010 直接占据，另有 Zheng CDC2024、Hancioglu IEEE Access2026 等。"
    "最小结构化 lifting spike：原始 affine val RMSE 0.22556 vs 物理结构化 0.22293，几无收益，说明手工物理特征不构成路线。"
    "三个可能 delta（有限数据闭环界 / 保无源正定 lifting / 全状态与部分可观测统一界）均未证明非平凡+可检验+prior-art delta。"
    "下一步：从三个 delta 中选定一个写出可证伪最小版本；若失败则 P1-only 也不成立，转入补采数据或缩小范围的 C 级决策。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t55-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t55-handoff")
print("doc_sha256:", sha)
print("revision:", revision())
