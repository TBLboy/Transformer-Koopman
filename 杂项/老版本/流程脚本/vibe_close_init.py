#!/usr/bin/env python3
"""Close out the init task: implementer, legacy evidence, review, alignment finding, gate, finish."""
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


TASK = "T-20260926-init-log"
LEGACY_RELS = [
    "architecture/software-architecture.md",
    "business-logic/constraints.md",
    "business-logic/decision-records.md",
    "business-logic/edges.md",
    "business-logic/graph.md",
    "business-logic/main.md",
    "business-logic/nodes.md",
    "business-logic/open-questions.md",
    "config/config-schema.md",
    "current-session.md",
    "debugging/known-issues.md",
    "hardware/hardware-list.md",
    "progress.md",
    "requirements.md",
]

# 1. Record the implementer so reviewer independence can be established.
apply("task.update", {"task_id": TASK, "implementer": "vibe-main"})

# 2. Bind the 14 archived legacy files to evidence.
legacy_files = [".project-log/legacy/" + rel for rel in LEGACY_RELS] + [
    ".project-log/legacy/PROVENANCE.md"
]
apply("evidence.record", {
    "id": "E-20260926-legacy-archive",
    "kind": "verification",
    "subject": "14 个 format-1 旧日志文件无损归档到 .project-log/legacy/（EOL 归一后与 git HEAD 一致）",
    "status": "valid",
    "task_id": TASK,
    "covers": {"files": legacy_files, "requirements": [], "tasks": [TASK]},
    "version_binding": {
        "git_commit": None, "diff_hash": None,
        "file_hashes": {rel: sha256(ROOT / rel) for rel in legacy_files},
    },
})

# 3. Independent review record (verdict: go).
apply("review.record", {
    "id": "RV-20260926-init-log",
    "task_id": TASK,
    "reviewer": "verification-reviewer",
    "verdict": "go",
    "scope": {
        "artifacts": ["AGENTS.md", ".project-log/**", ".project-log/legacy/**"],
        "method": "read-only independent verification (git blobs vs archive, markers, ledger chain) + raw CLI/EOL evidence supplied by main agent",
        "residual": [
            "reviewer's own shell could not execute the Vibe CLI or a hashing tool; CLI outputs were supplied by the main agent",
            "any formerly-untracked files in the removed nested .project-log are undiscoverable",
        ],
    },
    "evidence_refs": ["E-20260926-init-log", "E-20260926-legacy-archive"],
})

# 4. Record the pre-existing rule drift found by the reviewer (not caused by init).
apply("record.create", {
    "kind": "alignment", "id": "AL-20260926-inv-drift", "status": "open",
    "title": "既有代码与“禁止 np.linalg.inv”规则不一致（消解后遗留）",
    "payload": {
        "classification": "implementation-drift",
        "source": "independent review of init task",
        "finding": "规则要求 EDMD 闭式解使用 np.linalg.solve（禁止 np.linalg.inv），但 np.linalg.inv 仍出现在 training/traditional_edmd_trainer.py:155 和 training/mlp_koopman_trainer.py:187；仅 edmd_trainer.py 已迁移。",
        "impact": "数值稳定性风险仅在被声明的规则层面存在；非本次初始化引入。",
        "recommended_action": "后续任务中按需将这两处改为 np.linalg.solve 并补 NaN/Inf 守卫；需用户确认是否纳入当前基线。",
        "affected_paths": [
            "Transformer-Koopman/src/patchtst_koopman/training/traditional_edmd_trainer.py",
            "Transformer-Koopman/src/patchtst_koopman/training/mlp_koopman_trainer.py",
        ],
    },
})

print(json.dumps({"status": "recorded"}, ensure_ascii=False))
