import json, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

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

dec = {
    "id": "DEC-023", "kind": "decision", "status": "active",
    "title": "阶段③ 启动：解冻代码、务实定位（二区/三区工程论文）、P2 真机由用户执行、一个学期",
    "payload": {
        "class": "C", "decided_by": "user",
        "reason": "第十/十一轮将路线 A 收窄强化为 A+（RSHC-TK），其核心假设（history 调制控制通道 B(c)）已在现有数据上强通过；用户决定推进到实现。",
        "decision": [
            "1) 解冻训练代码，进入阶段③：允许修改 src/patchtst_koopman 与 scripts，跑真实 latent pipeline 结构 gate（fixed/A-only/B-only/AB）。",
            "2) 论文目标：二区/三区工程型论文即可（接受务实 novelty 定位）。DEC-021 的严格读法（必须新控制器机制）据此放宽为『可解释的建模改进 + 控制器结构变化 + 真机 + 简易理论』。",
            "3) P2 真机硬件可用；真机闭环实验由用户执行，Agent 负责代码/模型/控制器/理论/数据分析。",
            "4) 时间线：一个学期（约 4 个月，16 周）。",
        ],
        "reversible": True,
        "signals": ["conclusion", "submission-format"],
        "notes": [
            "结构选择（B-only vs AB）待 full pipeline gate 结果定；倾向 B-only。",
            "DEC-018（稳定化 ρ(A)≤rho_max + 非平凡界）在阶段③仍需满足。",
            "A+ 论文主线与 §49 novelty 表述以 GPT v1.1 为准。",
        ],
    },
}
apply("record.create", dec, "tT0-dec023")

next_action = (
    "阶段③ 启动（DEC-023，用户 C 级裁定）：(1) 解冻代码，进入阶段③实现；(2) 目标二区/三区工程论文，DEC-021 严格读法放宽；(3) P2 真机可用、实验由用户执行，Agent 负责代码/模型/控制器/理论/分析；(4) 时间线一个学期（16 周）。"
    "依据：第十/十一轮将路线 A 收窄为 A+（RSHC-TK），核心假设（history 调制控制通道 B(c)）已在现有数据强通过（B-only H=20 −67% vs A-only −42%；matched-state 差异 3.24×）。"
    "已摸清训练代码：encoder(x_history)→z=[x_t;h](d=10)、koopman z'=Az+Bu、decoder=前2维；EDMD 三阶段训练；dataset 仅提供 x_history/u_t/x_next（无 u_history）。"
    "下一步：实现 low-rank context modulation（fixed/A-only/B-only/AB）到 latent Koopman（新增 context encoder 摄入 x/u history；低秩 A(c)/B(c)），在 P2 现有数据上跑 full pipeline 结构 gate（H=1/5/10/20 train/val/test RMSE）+ history-shuffle + modulation-nullification + CB(c) 谱/PD，定 B-only vs AB，产出 gate 报告交 GPT。"
    "GOAL-001 门禁仍拒绝；DEC-018 未满足；代码已解冻。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tT1-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tT2-handoff")
print("revision:", revision())
