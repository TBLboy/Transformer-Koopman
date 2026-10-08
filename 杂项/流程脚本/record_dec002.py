import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

PAYLOAD = {
    "decision": "重构保真度契约 = C：结构重构 + 修已知缺陷 + 方法论升级",
    "decided_by": "user",
    "decided_at_session": "2026-09-28",
    "scope": [
        "允许修掉老代码真实缺陷（run_all 的 LSTM x platform2 KeyError、5 类配置漂移、3 处外部机器硬编码路径、死接口）",
        "允许纳入方法论升级（代价函数由 3 项扩为 5 项：新增多步物理 + 多步 latent）",
        "接受因此需要重新训练双平台，并修改论文 Section IV-B 与 Algorithm 1",
        "老项目 D:\\Project\\论文3老版本\\Transformer-Koopman 全程只读"
    ],
    "consequence": "重构总目标不再是逐位复现老结果；需要建立新的对照基线，并在完成时用独立复核确认新数字与配置自洽。",
    "evidence": [
        "用户对保真度契约问题的答复：选择选项 C",
        "老 .project-log/business-logic/open-questions.md 中 Q-20260605-004 为唯一待确认项"
    ],
    "newly_discovered_conflict": {
        "summary": "多步损失已实现但双平台不一致，且与论文正文、老提案三方冲突",
        "matrix": {
            "code_edmd_trainer": "5 项损失已实现（_pretrain_epoch docstring 与 328-330 行读取 multi_step 权重）",
            "configs_platform1": "multi_step.horizon=3, multi_step_physical=1.0, multi_step_latent=0.5 -> 5 项生效",
            "configs_platform2": "无 multi_step 键，loss_weights 仅 3 项 -> 3 项生效",
            "proposal_Q_20260605_004": "多步物理权重 10x（未验证）",
            "paper_body_per_old_log": "3 项（L_x, L_z, L_c）"
        },
        "impact": "已报告的 RMSE 0.157 (P1) 与 0.474 (P2) 可能来自不同的损失函数，属结论级 traceability gap，需用户确认权威定义",
        "status": "awaiting user decision"
    }
}

envelope = {
    "schema_version": 1,
    "command_id": "t007-dec002",
    "expected_revision": 6,
    "action": "record.create",
    "payload": {
        "kind": "decision",
        "id": "DEC-002",
        "title": "重构保真度契约定为 C（重构+修缺陷+方法论升级）",
        "status": "active",
        "payload": PAYLOAD,
    },
}

path = f"{TMP}/env_t007_dec002.json"
open(path, "w", encoding="utf-8", newline="\n").write(
    json.dumps(envelope, ensure_ascii=False, indent=2)
)

r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path],
                   capture_output=True)
out = r.stdout.decode("utf-8", "replace").strip()
print("rc:", r.returncode)
print(out or r.stderr.decode("utf-8", "replace"))
print("payload bytes:", len(json.dumps(PAYLOAD, ensure_ascii=False).encode("utf-8")))
