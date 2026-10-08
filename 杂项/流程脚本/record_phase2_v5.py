import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"


def rev():
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def apply(action, payload, tag):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": rev(), "action": action, "payload": payload}
    p = f"{TMP}/env_{tag}.json"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", p], capture_output=True)
    print(("OK   " if r.returncode == 0 else "FAIL ") + tag)
    if r.returncode:
        print(r.stderr.decode("utf-8", "replace")[:1200])
    return r.returncode


next_action = (
    "阶段② A 池完成 prior-art 淘汰：A1/A3/A4/A5 通用形式已被覆盖（input transformation / delay / switched / hierarchical Koopman）；"
    "A6/A8 暂缓。存续候选仅 A2（relative-degree-preserving）、A7（control-relevant subspace）、A9（actuation-redundancy kernel gating），"
    "并统一到一个修复 Schur 缺陷的闭环 task-tracking 界骨架（含编码器误差/有限数据误差/history 截断/输入映射秩缺陷）。"
    "下一步需用户 C 级确认论文核心创新主张的取向（严谨性路线 / 软体物理结构路线 / 组合），随后进入 S6 Theory Construction。代码继续冻结。"
)

payload = {
    "status": "complete",
    "documents": [".project-log/docs/phase2_branch_status_v0.5.md"],
    "new_prior_art": [
        "10.1109/tro.2026.3654384 T-RO 2026 Koopman Operators in Robot Learning (survey)",
        "10.1109/icra55743.2025.11127925 ICRA 2025 Multi-Segment Soft Robot Deep Koopman MPC",
        "10.23919/sice56594.2022.9905758 SICE 2022 Deep Koopman with Control soft robot spectral analysis",
        "10.29057/icbi.v14iespecial.15510 soft robot Koopman identification (vision light point)",
        "10.3390/biomimetics9110666 worm robot DMD-Koopman control",
        "10.1109/cdc49753.2023.10384106 Blischke & Hespanha switched Koopman learning",
        "10.1016/j.automatica.2019.05.016 Peitz & Klus switched-system Koopman model reduction",
        "10.1007/s11424-025-4546-0 Ning et al. switched nonlinear Koopman predictive control",
        "10.1016/j.sysconle.2025.106340 Ju et al. Koopman MPC nonlinear switched systems",
        "10.1115/1.4056703 Boyle & Stockar hierarchical Koopman MPC",
        "10.1109/lra.2024.3349966 Koopman-ZNN redundant manipulator constrained tracking",
        "10.1109/tac.2026.3693027 Bevanda et al. Nonparametric Control Koopman Operators",
        "10.1109/tii.2026.3705896 Hancooglu & Efe Koopman inverse dynamics / explicit model following",
        "10.1016/j.engappai.2025.111349 Wang et al. Koopman-based predictive tracking control",
    ],
    "branch_status": {
        "A1": "killed generic: input transformation prior art (Cibulka/Korda/Hanis 2025 SIADS)",
        "A2": "kept: relative-degree-preserving lifting, needs concrete rank/relative-degree theorem; verifiability on visual soft platform doubtful",
        "A3": "downgraded: standard sampled-data/delay/quantized control",
        "A4": "killed generic: switched Koopman learning/MPC prior art",
        "A5": "killed generic: hierarchical Koopman MPC prior art",
        "A6": "deferred: adjacent to adaptive Koopman / unknown input gain",
        "A7": "kept: control-relevant subspace, needs data-checkable discarded-subspace-to-task-error bound",
        "A8": "deferred: risks becoming multi-task learning",
        "A9": "kept (most physical): actuation-redundancy kernel gating (2D virtual input -> 4 ropes, nullspace = tension/common-mode mode gating dynamics); neighbor prior art: nullspace control allocation, Koopman-ZNN RA-L 2024",
    },
    "theory_backbone": "Closed-loop task-tracking bound unifying encoder prediction error + finite-data estimation error + history truncation under partial observation (G4) + input-map rank defect (G2); fixes the verified Schur/norm defect at Main34.tex L719-737.",
    "research_result": "All generic operator directions are prior-art occupied; no final route passed all gates. Shortlist = A2/A7/A9. Paper core contribution orientation is a C-level decision requiring user confirmation.",
}

rc = apply("record.create", {"kind": "research", "id": "PHASE2-SCREEN-004", "title": "阶段② A 池 prior-art 淘汰与存续候选", "status": "complete", "payload": payload}, "t45-screen")
if rc == 0:
    apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t45-resume")
    apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t45-handoff")
print("revision:", rev())
