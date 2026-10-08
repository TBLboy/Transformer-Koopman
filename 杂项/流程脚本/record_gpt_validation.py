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

DOC = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_route_validation_v1.md"
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
    "document": ".project-log/docs/phase2_gpt_route_validation_v1.md",
    "document_sha256": sha,
    "scope": "validate GPT routes R1-R18 + combos; verification and feedback only",
    "verdicts": {
        "R1": "partially feasible; narrow real delta = unreachable residual as representation-learning loss + multi-step reachable alignment; precedents cover only feedforward/certificate use",
        "R2": "not feasible as main theorem (high risk); LQR covariant similarity-invariance known since 1984; fixing Q = choosing a gauge",
        "R3": "partially feasible; needs control-oriented theorem; overlaps DEKC arXiv:2506.08319 and discrepancy modeling arXiv:2203.05164",
        "R4": "renaming (SPC/DeePC; arXiv:2601.11901 condensed multi-step EDMD)",
        "R5": "partial renaming (actuated/transverse; P2 kernel not excited -> A9 dead)",
        "R6": "renaming (Koopman Gramian balanced truncation arXiv:1709.08712)",
        "R7": "partial renaming (LQG balanced truncation Jonckheere-Silverman 1983)",
        "R9": "partial renaming; residual = coordinate-invariant control-relevant metric",
        "R10": "auxiliary only",
        "R13": "renaming (Markov realization Ho-Kalman; arXiv:2602.14537 N-step predictability <-> CAP)",
        "R14": "partial renaming; residual = new computable Koopman-specific control-relevant error metric",
        "R15": "renaming (reference governor; project I2 already killed)",
        "R16": "partial renaming (BCPO arXiv:2507.19437 observation vs control sufficiency)",
        "R17": "narrative layer only",
        "R18": "renaming as independent contribution (invariance proximity arXiv:2311.13033; SafEDMD Cor 3.2)",
    },
    "combo_verdicts": {
        "Combo A (R1+R15+R18)": "mixed; only R1 has a real delta",
        "Combo B (R2+R9+R4)": "not recommended (R2 high risk + R4 renaming)",
        "Combo C (R3+R12+R18)": "P1-fit but needs R3 control theorem",
        "Combo D (R4+R13+R2)": "not recommended",
    },
    "best_remaining_space": [
        "R1 delta: unreachable residual as representation-learning loss + multi-step reachable-subspace alignment",
        "coordinate-invariant control-relevant closed-loop bound (intersection of R7/R9/R14/R18)",
    ],
    "evidence_level": "L2 (abstract + fragments); L3 full-text comparison NOT done",
    "next": "L3 full-text prior-art comparison prioritized at arXiv:2601.11901, 2602.14537, 2311.13033, 2307.15368, 1709.08712, 2209.08637, 2402.03145, 2507.19437; then decide route vs C-level direction",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-ROUTE-VALIDATION-001", "title": "GPT R1-R18 逐条验证：R1 部分可行、R2 高危、R3 需补理论、R4-R18 多为换名", "status": "complete", "payload": payload}, "t59-val")

next_action = (
    "已完成 GPT 18 条路线 + 4 组合的逐条验证（只验证不构思）。三项便宜测试：R2 前提 gauge 病理成立但属 1984 已知 LQR 协变不变性；R1 前提参考不可达缺陷 ~16~21%（一阶）；R3 前提残差可预测 17~25%。"
    "prior-art（L2）：R1 delta 窄但实在（不可达残差作训练损失+多步可达）；R2 高危（已知事实重述）；R3 需补控制定理（与 DEKC/discrepancy 重叠）；R4/R6/R13/R15/R18 基本换名；R5/R7/R9/R14/R16 部分换名。"
    "残余空间集中在两处：R1 的“训练目标化不可达残差+多步可达”，以及“坐标不变的控制相关闭环界”（R7/R9/R14/R18 交集）。"
    "下一步：做 L3 全文对拍（arXiv:2601.11901/2602.14537/2311.13033/2307.15368/1709.08712/2209.08637/2402.03145/2507.19437），据此判定 R1/R3 是否成立或转入 C 级决策。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t59-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t59-handoff")
print("doc_sha256:", sha)
print("revision:", revision())
