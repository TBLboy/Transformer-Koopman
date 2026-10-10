import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

GATE = Path(ROOT) / ".project-log" / "docs" / "phase2_gate_update_v0.3.md"
HO = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v8.md"
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
    "id": "DEC-021", "kind": "decision", "status": "active",
    "title": "阶段② 目标轴切换：控制器设计创新为首要，建模创新可选",
    "payload": {
        "class": "C",
        "decided_by": "user",
        "reason": "用户澄清：真正想做的创新在控制器设计上，建模创新可有可无。过去七轮 R/N/M/Q/V/W 全部优化模型/表示，控制器始终是 B†+LQR 或简单逆控制，控制器设计空间从未被系统搜索。",
        "decision": "阶段② 首要贡献改为控制器设计实质新颖（新架构/律/算法 + 可证定理）；建模可用标准件（现有 Transformer-Koopman 或已刻画响应算子），不要求建模新颖。据此发布门禁 v0.3（控制器中心）。",
        "revised_gate_doc": ".project-log/docs/phase2_gate_update_v0.3.md",
        "reversible": True,
        "signals": ["conclusion"],
        "notes": [
            "保留既有约束事实：Koopman 闭合不可塑、P2 响应几何为经典（单调[固定输出反射]/近可积/局部可逆/低歧义）、约束不激活、无输出零空间。",
            "两条数据分支：①现有数据；②最小新增观测（C1 中段 marker / C2 差分绳长 / C3 张力-电流 proxy）。",
            "禁止伪创新清单不变；DEC-018/019/020 保持；代码/配置/论文冻结。",
        ],
    },
}
apply("record.create", dec_payload, "tD0-dec021")

covers = {"files": [".project-log/docs/phase2_gate_update_v0.3.md",
                    ".project-log/docs/phase2_gpt_handoff_v8.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_gatev3.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-GATE-V03-001", "--kind", "decision",
                    "--subject", "Phase-2 gate v0.3 (controller-centric under DEC-021)",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tD1-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "用户 C 级澄清（DEC-021）：阶段② 首要贡献改为『控制器设计创新』，建模创新可有可无；发布门禁 v0.3（控制器中心）。"
    "依据：过去七轮 R/N/M/Q/V/W 全部在优化模型/表示，控制器始终是 B†+LQR 或简单逆控制，控制器设计空间从未被系统搜索；GPT 第七轮『停止搜索』结论是在旧目标（新建模+新控制器）下给出，需按新目标重估。"
    "产出：phase2_gate_update_v0.3.md（控制器中心门禁：控制器设计实质新颖 + P1/P2 双锚点 + 可证定理 + 控制器级 prior-art 划界 + 建模可用标准件 + 现有数据或声明最小观测）与独立交接稿 phase2_gpt_handoff_v8.md（请求第八轮：≤6 条控制器设计路线；含两条数据分支：①现有数据 ②最小新增观测 C1/C2/C3）。"
    "启用性基质：P2 响应近可积/局部可逆/固定输出反射后单调(99.67%)/低歧义；P1 强单调；约束不激活；现有 Koopman 模型不稳定(ρ=2.0878)；无输出零空间。"
    "下一步：等待用户就『现有数据 vs 最小新增观测』拍板，并等待 GPT 依据交接稿 v8 返回第八轮控制器路线；返回后按同法验证。GOAL-001 门禁仍拒绝；DEC-018 未满足；代码/配置/论文冻结。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tD2-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tD3-handoff")
print("gate_sha:", sha(GATE))
print("ho_sha:", sha(HO))
print("revision:", revision())
