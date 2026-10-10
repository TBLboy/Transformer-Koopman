import json, subprocess, sys, hashlib
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
        print(p.stdout.decode("utf-8", "replace")[:700]); print(p.stderr.decode("utf-8", "replace")[:1200])

audit = {
    "question": "P_final = 4 or 8? (GPT round-18, the only pre-manuscript technical item)",
    "rule_from_gpt": "final checkpoint metadata is the source of truth for the reported experiment configuration",
    "findings": {
        "configs/platform2.yaml": {"history_length": 8, "patch_length": 2, "latent_dim": 10, "d_model": 16, "n_layers": 1, "n_heads": 2, "d_ff": 64, "dropout": 0.1, "readout_method": "mean", "data_dir": "../数据备份/软体平台数据/处理后的数据"},
        "deploy/algorithms/tk_assets/model_assets/platform2_metadata.json": {"history_length": 4, "patch_length": 2, "latent_dim": 10, "d_model": 16, "n_layers": 3, "n_heads": 2, "source_checkpoint": "C:/Users/Windows/Desktop/论文4/code_project/results/models/ablation_platform2/20260514_084213/full_model/full_model_model.pth"},
        "deploy/algorithms/tk_assets/transformer_koopman_model.py": "OLD ROUTE: KoopmanDynamics has a single fixed nn.Parameter A (no context MLP, no low-rank A(c) modulation); PatchTSTKoopmanModel = encoder -> fixed-A koopman -> linear decoder.",
        "deploy/algorithms/configs/transformer_koopman_controller.json": "OLD ROUTE controller: LQR gains (Q_x1/Q_x2/alpha/R_control/ff_gain/u_limit), not RTI-MPC.",
        "deploy/export_assets.py": "exports by copying a checkpoint from results/models/... and reading its config; no results/ dir exists in the repo.",
        "repo checkpoints": "only ONE .pth in the repo: deploy/algorithms/tk_assets/model_assets/platform2_full_model.pth (the P=4 legacy one). No results/ or results/models/ directory exists; no P=8 checkpoint is checked in.",
    },
    "experiments_actually_run": "all Phase-2 gate experiments (A/B/AB ablation, rank sweep, rollout-aware, DirectNN, Gate-14C/14D RTI, matched oracle, theory diagnostics) trained their models from 处理后的数据 using configs/platform2.yaml -> P=8, n_layers=1.",
    "conclusion": "P_final for the PAPER = 8 (config + every executed experiment). The bundled deploy checkpoint (P=4, n_layers=3) is a STALE LEGACY artifact imported from the previous project (论文4/code_project, ablation_platform2/20260514_084213) and implements the OLD route (fixed A + LQR); it was not used in any current experiment and cannot reproduce any new-route result.",
    "required_actions": [
        "Train and save the final P=8 new-route model (history-conditioned low-rank A(c), rollout-aware scheduled training) as the paper's single model artifact; none currently exists in the repo.",
        "Regenerate deploy assets (deploy/algorithms/tk_assets/model_assets/) from that P=8 checkpoint via deploy/export_assets.py.",
        "Replace the old-route deploy stack (fixed-A KoopmanDynamics + LQR controller config) with the new-route model + RTI-SP controller before P2 hardware.",
        "Then unify P=8 across paper tables / algorithm box / experiment description.",
    ],
    "classified_as": "deployment-consistency defect (same family as ALN-010 residual / ALN-004): config vs artifact drift.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-CONFIG-AUDIT-001",
      "title": "Configuration audit: P_final=8 for the paper; deploy ckpt (P=4, old route) is a stale legacy artifact", "status": "complete",
      "payload": audit}, "tZ10-audit")

apply("record.create", {"kind": "decision", "id": "DEC-028",
      "title": "P_final = 8（论文）；部署栈需从当前 pipeline 重新生成（旧 ckpt P=4 作废）", "status": "active",
      "payload": {
        "level": "B", "basis": "GPT 第十八轮 §11/§12 configuration audit 要求 + 本机核查证据（PHASE2-CONFIG-AUDIT-001）",
        "decision": "论文报告 P=8（与 platform2.yaml 及全部已执行实验一致）。仓库内现有部署 checkpoint（P=4, n_layers=3, 旧路线固定 A + LQR）来自旧项目 论文4/code_project 的 ablation 运行，作废，不作为论文模型。",
        "consequence": "P2 真机前必须：(1) 训练并保存 P=8 新路线最终模型（当前仓库无该 checkpoint）；(2) 用 export_assets.py 重新导出部署资产；(3) 用新路线模型 + RTI-SP 控制器替换旧部署栈。理论章节中 P 为一般符号，不受影响。",
        "note": "该不一致属于 deployment-consistency defect（与 ALN-010 残余、ALN-004 同类）：config 与 artifact 漂移。",
      }}, "tZ11-dec028")

covers = {"files": ["Transformer-Koopman/训练代码/configs/platform2.yaml",
                    "Transformer-Koopman/训练代码/deploy/algorithms/tk_assets/model_assets/platform2_metadata.json",
                    "Transformer-Koopman/训练代码/deploy/algorithms/tk_assets/transformer_koopman_model.py",
                    "Transformer-Koopman/训练代码/deploy/algorithms/configs/transformer_koopman_controller.json"],
          "requirements": [], "tasks": ["TASK-006"]}
cpath = f"{TMP}/covers_audit.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-CONFIG-AUDIT-001", "--kind", "research",
                    "--subject", "P_final configuration audit",
                    "--status", "valid", "--task-id", "TASK-006", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tZ12-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:700]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "TASK-006（论文新版本，strict）进行中。**第十八轮裁定已接收**：理论章节 v2.1 = GO FOR MANUSCRIPT（REV-THEORY-002 = go）；理论路线 CLOSED；诊断数字以第十八轮 §21 清单为唯一有效版本。"
    "**配置核查（GPT §11/§12，本轮唯一技术项）已完成**：P_final = **8**（platform2.yaml history_length=8/n_layers=1，与全部已执行实验一致）；仓库内部署 ckpt（P=4/n_layers=3）来自旧项目 论文4/code_project 的 ablation 运行，属旧路线（固定 A + LQR），**作废**；当前仓库**不存在** P=8 的最终模型 checkpoint。记录 PHASE2-CONFIG-AUDIT-001 / DEC-028 / EV-PHASE2-CONFIG-AUDIT-001。"
    "**Main.tex 状态**：新路线改写完成（Def.1 HCLTK(r=2)、§Finite-Horizon Theory、§Real-Time Predictive Control、删除旧 LQR/UUB），结构检查通过（环境配对/悬空引用/括号/美元符），**未编译**（本机无 LaTeX）。"
    "**下一步**：(1) 机制图（‖∏A‖₂、d_M(H)、e_x(H) 随 H 的归一化曲线，GPT §9 优先于新理论）；(2) 实验章节（离线结果占位或真机 E1–E5）；(3) Related Work/Positioning 覆盖 history-conditioned transition 与 RTI；(4) 图 1–3 适配；(5) 参考文献；(6) 训练并导出 P=8 最终模型 + 更新部署栈（P2 真机前置）。"
)
apply("task.resume", {"task_id": "TASK-006", "next_action": next_action}, "tZ13-resume")
apply("task.handoff", {"task_id": "TASK-006", "next_action": next_action}, "tZ14-handoff")
print("revision:", revision())
