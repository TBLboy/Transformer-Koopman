import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
DOC_REL = ".project-log/docs/business-logic/clarification.yaml"
DOC_SHA = hashlib.sha256(Path(ROOT, DOC_REL).read_bytes()).hexdigest()
print("doc sha256:", DOC_SHA)


def revision():
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def apply(action, payload, tag, label):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(),
           "action": action, "payload": payload}
    p = f"{TMP}/env_{tag}.json"
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(env, ensure_ascii=False, indent=2))
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", p], capture_output=True)
    ok = r.returncode == 0
    note = "" if ok else " -> " + r.stderr.decode("utf-8", "replace").strip()[:220]
    print(f"  {'OK  ' if ok else 'FAIL'} {label}{note}")
    return ok


SC = [
    "新项目是结构清晰、YAML 配置驱动的可安装 Python 包，覆盖 Data->Dataset->Train->Eval 主链路",
    "双平台统一使用论文 eq:pretraining_loss 定义的 5 项 Stage-1 损失（L_x, L_z, L_c, L_multi_x, L_multi_z），platform2 补齐缺失的多步损失",
    "双平台四类方法（PatchTST-Koopman 主方法、MLP-Koopman、LSTM-Koopman、Traditional EDMD）均可训练与评估并产出 RMSE/MAE，platform2 结果由新配置重训得到",
    "流水线不再调度配置中不存在的任务（消除 LSTM x platform2 KeyError 一类缺陷），且不再硬编码外部机器路径",
    "7 类消融变体（no_patch, no_attention, no_positional, window, patch_size, readout, pure_feature）在双平台可训练评估并产出 CSV/LaTeX/图表",
    "部署资产导出链路可用，部署包不依赖训练包",
    "回归测试套件存在且可重复运行，替代老项目的手工 CLI harness",
    "老项目 D:\\Project\\论文3老版本\\Transformer-Koopman 全程只读",
]
REQ = [
    "双平台四类方法的训练与评估命令及实际输出（含新的 RMSE/MAE 数字），并说明与老数字的差异来源",
    "platform2 补齐多步损失后的训练配置与结果，含 N_L 与 5 个 lambda 的实际取值",
    "缺陷修复清单及逐项验证证据（KeyError、配置漂移、硬编码路径、死接口）",
    "消融变体训练的完成证据与结果文件（CSV/LaTeX/图表）",
    "回归测试套件的运行命令、结果与环境信息",
    "独立复核（不复用实现者结论）对新项目主链路与论文方法定义一致性的 go 结论",
]

print("\n== 1. reshape GOAL-001 conditions into gate-valid objects ==")
apply("goal.update", {"id": "GOAL-001",
                      "success_conditions": [
                          {"id": f"SC-{i}", "statement": s, "status": "pending",
                           "limitation": "阶段一/二/三全部完成后才可能转为 passed"}
                          for i, s in enumerate(SC, 1)],
                      "required_evidence": [
                          {"id": f"RE-{i}", "subject": s, "evidence_refs": []}
                          for i, s in enumerate(REQ, 1)]},
      "t5-goal-shape", "goal.update GOAL-001")

print("\n== 2. resume TASK-001 (clears Q-MULTISTEP-UNIFY-001) ==")
apply("task.resume", {"task_id": "TASK-001",
                      "next_action": "澄清交付物已通过独立复核（go）；转入阶段① 按 scope A 拆分并执行第一批 D+A+B 清理任务（FIX-10 优先）"},
      "t5-resume", "task.resume TASK-001")

print("\n== 3. record evidence ==")
VB = {"git_commit": None, "diff_hash": DOC_SHA, "file_hashes": {DOC_REL: DOC_SHA}}
apply("evidence.record", {
    "id": "EV-CLARIFY-001", "kind": "analysis",
    "subject": "重构业务澄清交付物：12 条业务原子 + 18 条三方对齐记录 + 7 个开放问题（strict，结论级）",
    "status": "valid", "task_id": "TASK-001",
    "covers": {"tasks": ["TASK-001"], "requirements": ["REQ-001"], "files": [DOC_REL]},
    "version_binding": VB}, "t5-ev1", "evidence EV-CLARIFY-001")

apply("evidence.record", {
    "id": "EV-CLARIFY-REVIEW-001", "kind": "review",
    "subject": "独立复核（4 轮收敛至 go）：首轮 conditional 7 项发现全部核实，二三轮逐条修正，第四轮确认 ALN-015 引用三元组修正且无回归",
    "status": "valid", "task_id": "TASK-001",
    "covers": {"tasks": ["TASK-001"], "files": [DOC_REL]},
    "version_binding": VB}, "t5-ev2", "evidence EV-CLARIFY-REVIEW-001")

print("\n== 4. record the independent go review ==")
apply("review.record", {
    "id": "REV-CLARIFY-001", "task_id": "TASK-001", "reviewer": "verification-reviewer-4th-pass",
    "verdict": "go",
    "scope": {"artifact": DOC_REL, "sha256": DOC_SHA,
              "in_scope": "业务澄清交付物的功能/技术业务逻辑、双向对齐记录与引用准确性",
              "out_of_scope": "阶段② 理论方法决策、阶段③ 重训与论文数字（尚未开始）",
              "rounds": 4, "final_blocking_items": 0},
    "evidence_refs": ["EV-CLARIFY-REVIEW-001", "EV-CLARIFY-001"]},
    "t5-rev", "review REV-CLARIFY-001")

print("\n== 5. record DEC-005 (B level: goal shape + gate gaps) ==")
apply("record.create", {
    "kind": "decision", "id": "DEC-005", "title": "修正 GOAL-001 门禁载荷形状并记录两处门禁配置缺口", "status": "accepted",
    "payload": {
        "authority": "B",
        "decision": "将 GOAL-001 的 success_conditions/required_evidence 由字符串数组改为门禁期望的对象数组（{id,statement,status} / {id,subject,evidence_refs}），status 一律 pending。",
        "rationale": "state_store.py:1136-1138 与 1163-1166 要求每项为对象；字符串会产出 'not an object' 畸形错误而非真实未达成，属埋雷。",
        "gate_gaps": [
            "TASK-001 的 extensions.risk 不可通过 CLI 设置：task.update 仅允许 implementer/owner（state_store.py:1549-1553），因此任务级高风险独立复核门禁无法由 CLI 启用；本轮复核已如实记录，但不被门禁强制。",
            "GOAL-001 的 extensions 缺少 implementer/owner：_goal_completion_problems（state_store.py:1196-1213）在 implementer 非字符串时直接跳过复核人独立性校验，因此目标级复核独立性目前空转。",
        ],
        "mitigation": "本轮仍以 reviewer != 实现者 的方式真实执行并记录复核；建议后续由用户决定是否为工作流补一个可写 extensions 的受控入口。",
        "status_note": "以上两点不影响本轮 TASK-001 的完成判定，因为 TASK-001 的完成门禁只要求覆盖它的有效证据。"}},
    "t5-dec5", "decision DEC-005")

print("\n== 6. finish TASK-001 ==")
apply("task.finish", {"task_id": "TASK-001", "summary":
    "业务澄清交付物完成并通过独立复核（go）：clarification.yaml 含功能业务逻辑、技术业务逻辑、双向对齐 18 条记录、7 个开放问题；"
    "修正了 P2 lifting 误述、补入 INV1 稳定性分叉违反（6 份产物 rho>1，含主方法）、基线 L_c 漂移、论文谱系未收敛、多步损失归约不一致；"
    "三处 C 级决策已锁定（DEC-002 还原度、DEC-003 5 项损失统一、DEC-004 阶段顺序）；清理范围定 scope A；"
    "证据 EV-CLARIFY-001（valid，绑定 doc sha256）、复核 EV-CLARIFY-REVIEW-001（valid）+ REV-CLARIFY-001（go）。"},
    "t5-finish", "task.finish TASK-001")

print("\nfinal revision:", revision())
