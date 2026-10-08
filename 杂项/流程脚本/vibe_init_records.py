#!/usr/bin/env python3
"""Record the initialization of the Vibe Project Log (format 2) for Transformer-Koopman."""
from __future__ import annotations

import hashlib
import json
import sys
import uuid
from pathlib import Path

RT = Path(r"C:\Users\12187\.config\opencode\vibe-workflow\scripts")
sys.path.insert(0, str(RT))
ROOT = Path(r"D:\Project\Transformer-Koopman")

from state_context import apply_command, open_store  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply(action: str, payload: dict) -> dict:
    store = open_store(ROOT, heal=True)
    envelope = {
        "schema_version": 1,
        "command_id": uuid.uuid4().hex,
        "expected_revision": store.status()["revision"],
        "action": action,
        "payload": payload,
    }
    result = apply_command(ROOT, envelope)
    print(f"OK  {action}: revision -> {result['receipt'].get('revision')}", file=sys.stderr)
    return result


GOAL = "G-patchtst-koopman"
TASK = "T-20260926-init-log"

apply("goal.create", {
    "id": GOAL,
    "title": "PatchTST-Koopman 非线性系统建模 + 分层 LQR 控制：噪声鲁棒建模可复现并产出学术论文",
})

apply("goal.update", {
    "id": GOAL,
    "success_conditions": [
        "Platform1 (6-state/3-control) 与 Platform2 (2-state/2-control) 的 PatchTST-Koopman 主方法可复现训练并产出 RMSE 结果",
        "对照基线（MLP-Koopman / LSTM-Koopman / Traditional EDMD）可复现",
        "消融变体全部可训练并在测试集 rollout 评估通过",
        "部署包独立于训练包，控制器可在上位机加载预训练资产",
        "论文材料（配图 / LaTeX 表格）可生成",
    ],
    "required_evidence": [
        "双平台主方法与基线的可复现训练结果（results/**/*.json）",
        "双平台消融评估结果（results/ablation/**/ablation_results.json）",
        "控制器资产校验通过记录",
        "smoke_test / validate 通过记录",
    ],
})

apply("record.create", {
    "kind": "decision", "id": "D-20260926-project-log-root", "status": "active",
    "title": "Project Log(格式2) 根目录迁至外层，子目录旧版日志归档",
    "payload": {
        "authority": "C",
        "user_approval": "approved",
        "decided_at": "2026-09-26",
        "decision": "Vibe format-2 .project-log 根目录 = D:/Project/Transformer-Koopman（外层，非 git）；子目录 Transformer-Koopman/.project-log 的 format-1 手写日志归档到 .project-log/legacy/。",
        "context": "真实代码与 git 仓库(origin github.com/TBLboy/Transformer-Koopman)位于子目录；外层为工作区根，非 git 仓库。",
        "alternatives": [
            "在子目录 git 仓库内建日志（保留 git 版本化 + 远端持久化）",
            "保留旧日志不初始化格式2",
        ],
        "rationale": "用户明确选择：日志放外层、不走 git。",
        "consequences": [
            "账本不受 git 追踪，portability-status 的远端持久化为 false",
            "子目录 git 仓库显示 14 个 .project-log 文件删除（未提交，未 commit）",
        ],
    },
})

apply("record.create", {
    "kind": "requirement", "id": "R-20260926-legacy-baseline", "status": "draft",
    "title": "从旧版 requirements.md 重新导入的需求基线（待用户确认）",
    "payload": {
        "approval": {"status": "pending", "note": "从 .project-log/legacy/requirements.md 重新导入，等待用户确认"},
        "source": ".project-log/legacy/requirements.md",
        "functional": [
            "PatchTST 编码器 + Koopman 动力学 + Linear 解码器（主方法）",
            "EDMD 两步法 与 End-to-End 两种训练方法",
            "MLP-Koopman / LSTM-Koopman / Traditional EDMD 对照基线",
            "7 种消融变体（no_patch/no_attention/no_positional/window/patch_size/readout/pure_feature）",
            "部署控制器包（上位机 FlexibleArmControl34）",
            "论文配图 / LaTeX 表格生成脚本",
        ],
        "non_functional": [
            "代码可重新训练出论文结果",
            "部署包不依赖训练包",
            "消融实验可复现",
        ],
        "scope": {
            "in": ["Platform1 6-DOF 柔性机械臂", "Platform2 2-DOF 软体机器人"],
            "out": ["硬件在环实时控制测试", "上位机 GUI 开发"],
        },
        "acceptance": [
            "scripts/smoke_test.py 全部通过",
            "所有模型可导入、训练 1 epoch 不报错",
            "部署控制器可加载预训练资产",
            "消融所有变体可训练",
        ],
    },
})

apply("record.create", {
    "kind": "architecture", "id": "A-20260926-module-layout", "status": "active",
    "title": "模块分层：算法包 / CLI 薄层 / 独立部署包",
    "payload": {
        "source": ".project-log/legacy/architecture/software-architecture.md",
        "layout": "src/patchtst_koopman（可 pip install 的算法包） + scripts（薄层 CLI 入口） + deploy（独立部署包） + configs（平台 YAML）",
        "boundaries": [
            "算法包与部署包严格分离；部署包使用独立模型副本，上位机不安装 patchtst_koopman",
            "所有训练/测试/消融通过 YAML 驱动；script 入口不使用硬编码路径",
            "GUI 仅存在于上位机，不在本项目范围内",
        ],
        "note": "代码位于子目录 Transformer-Koopman/；本根目录仅 .project-log/ 与 AGENTS.md",
    },
})

apply("task.create", {
    "id": TASK,
    "title": "初始化 Vibe Project Log（格式2）与根 AGENTS.md",
    "goal_id": GOAL,
    "extensions": {"risk": "high", "verification": {"level": 3}, "route": "strict"},
})

apply("task.begin", {
    "task_id": TASK,
    "run_id": "R-20260926-init-log-1",
    "next_action": "独立复核格式2日志、AGENTS.md 与旧版日志归档完整性",
})

files = [
    ".project-log/state-format.json",
    ".project-log/current-session.md",
    ".project-log/progress.md",
    ".project-log/docs/archive/README.md",
    ".project-log/legacy/PROVENANCE.md",
    "AGENTS.md",
]
hashes = {rel: sha256(ROOT / rel) for rel in files}

apply("evidence.record", {
    "id": "E-20260926-init-log",
    "kind": "verification",
    "subject": "格式2 .project-log 与根 AGENTS.md 初始化，旧版 format-1 日志归档至 legacy/",
    "status": "valid",
    "task_id": TASK,
    "covers": {"files": files, "requirements": [], "tasks": [TASK]},
    "version_binding": {"git_commit": None, "diff_hash": None, "file_hashes": hashes},
})

print(json.dumps({"status": "recorded"}, ensure_ascii=False))
