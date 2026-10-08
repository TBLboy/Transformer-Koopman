import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

GATE = Path(ROOT) / ".project-log" / "docs" / "phase2_gate_update_v0.2.md"
HO5 = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v5.md"
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

dec_payload = {
    "id": "DEC-020", "kind": "decision", "status": "active",
    "title": "阶段② 方向改为 D：更换建模范式（放宽 DEC-015 的 Koopman 约束）",
    "payload": {
        "class": "C",
        "decided_by": "user",
        "reason": "跨四轮 R18/N6/M12/Q7 在“必须保留有限维 Koopman 线性闭合”前提下无候选存活；P2 闭合误差小且不可后验反馈重塑、动态全阶，P1 残差恒在 im(B)。用户裁定更换建模范式。",
        "decision": "阶段② 不再要求建模范式为有限维 Koopman 线性闭合；允许 contraction/LPV/低维非线性核混合/耗散-无源/可解释残差等范式。继续由外部 GPT 提出路线，本地验证。",
        "supersedes_partial": "DEC-015 的“必须保留 Koopman 连接”一项",
        "revised_gate_doc": ".project-log/docs/phase2_gate_update_v0.2.md",
        "reversible": True,
        "signals": ["conclusion"],
        "notes": [
            "放宽的是范式约束，不降低证据要求：新路线须显式论证范式必要性并回应 T4 四个经验事实。",
            "禁止伪创新清单不变；DEC-018（阶段③ 镇定前提）不变；代码/配置/论文仍冻结。",
            "外部构思方在 fan 2401.08153 等边界外的非 Koopman 范式空间重新出题。",
        ],
    },
}
apply("record.create", dec_payload, "tA0-dec020")

covers = {"files": [".project-log/docs/phase2_gate_update_v0.2.md",
                    ".project-log/docs/phase2_gpt_handoff_v5.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_gatev2.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-GATE-V02-001", "--kind", "decision",
                    "--subject", "Phase-2 gate v0.2 (paradigm change under DEC-020)",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tA1-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "用户 C 级决策 D（DEC-020）：阶段② 更换建模范式，放宽 DEC-015“必须保留有限维 Koopman 闭合”约束，继续由外部 GPT 出路线。"
    "依据：第四轮 Q0–Q6 验证后，P2 闭合误差小(归一化 RMSE 0.008)且不可后验反馈重塑（连 rank-10 全秩非线性漂移仅降 0.25%、残差秩不变）、obstruction 动态全阶（Hankel 秩 99%=97/100），P1 残差恒在 im(B)。"
    "产出：phase2_gate_update_v0.2.md（修订门禁：范式实质改变 + 显式论证必要性 + 回应 T4 四个经验事实 + 控制器结构改 + P1/P2 锚点 + 可证定理 + prior-art 双划线 + 数据可实现/最小传感集）与独立交接稿 phase2_gpt_handoff_v5.md（请求第五轮：≤6 条范式级路线）。"
    "下一步：等待 GPT 依据交接稿 v5 返回第五轮范式级路线；返回后按同法（prior-art + 廉价实验 + 门禁 v0.2 对拍）验证。GOAL-001 门禁仍拒绝；DEC-018 未满足；代码/配置/论文冻结。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tA2-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tA3-handoff")
print("gate_sha:", sha(GATE))
print("ho5_sha:", sha(HO5))
print("revision:", revision())
