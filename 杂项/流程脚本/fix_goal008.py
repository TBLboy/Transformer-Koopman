import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r"C:\Users\12187\.config\opencode\vibe-workflow\scripts")
from state_context import apply_command, open_store  # noqa: E402
from state_store import SCHEMA_VERSION  # noqa: E402

ROOT = Path(r"D:\Project\辅料称重防错系统")
EVID = "EV-TASK-140-DEVENV-R1"


def apply(action, payload):
    store = open_store(ROOT, heal=True)
    env = {
        "schema_version": SCHEMA_VERSION,
        "command_id": uuid.uuid4().hex,
        "expected_revision": store.status()["revision"],
        "action": action,
        "payload": payload,
    }
    res = apply_command(ROOT, env)
    print(f"[ok] {action} -> {json.dumps(res, ensure_ascii=False)[:120]}")


apply(
    "goal.update",
    {
        "id": "GOAL-008",
        "success_conditions": [
            {
                "id": "SC-UV-REPRO",
                "status": "passed",
                "text": "PC 端开发环境可依据 docs/dev-environment.md 用 uv 完整复现",
                "evidence_refs": [EVID],
            },
            {
                "id": "SC-TESTS-GREEN",
                "status": "passed",
                "text": "后端 pytest 全量 150 项通过、0 失败",
                "evidence_refs": [EVID],
            },
            {
                "id": "SC-RESTORE-WIN",
                "status": "passed",
                "text": "备份恢复在 Windows 真实 uvicorn 进程可用且数据完好",
                "evidence_refs": [EVID],
            },
        ],
        "required_evidence": [
            {
                "kind": "test",
                "subject": "TASK-140 验证：pytest 全量 150 通过/0 失败；真实进程备份恢复成功",
                "evidence_refs": [EVID],
            }
        ],
    },
)

print("done")
