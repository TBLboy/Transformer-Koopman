import hashlib
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r"C:\Users\12187\.config\opencode\vibe-workflow\scripts")
from state_context import apply_command, open_store  # noqa: E402
from state_store import SCHEMA_VERSION  # noqa: E402

ROOT = Path(r"D:\Project\辅料称重防错系统")
REPO = ROOT / "milk-milk-go"
COMMIT = sys.argv[1]


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


REL = [
    "pc/server/app/api/operations.py",
    "pc/server/app/db/session.py",
    "pc/server/seed.py",
    "pc/server/tests/test_restore.py",
    "pc/server/tests/test_backup_retention.py",
    "pc/server/tests/test_auth.py",
    "pc/server/tests/test_operations.py",
    "pc/server/tests/test_demo_seed.py",
    "pc/server/requirements.lock",
    "pc/server/README.md",
    "docs/dev-environment.md",
]
FILES = [f"milk-milk-go/{path}" for path in REL]
FILE_HASHES = {
    f"milk-milk-go/{path}": hashlib.sha256((REPO / path).read_bytes()).hexdigest() for path in REL
}

EVIDENCE_ID = "EV-TASK-140-DEVENV-R1"

apply(
    "evidence.record",
    {
        "id": EVIDENCE_ID,
        "kind": "test",
        "subject": (
            "TASK-140 验证：pc/server pytest 全量 150 项通过、0 失败（原 143 通过/6 失败，"
            "新增 1 项种子默认路径测试）；对运行中的 uvicorn 8011 真实进程执行备份→恢复，"
            "POST /operations/restore 返回 status=success、restart_required=true，"
            "恢复后 /api/v1/health 为 database=ok，主数据完好（14 辅料/6 产品），"
            "pc/data 无 .restore-* 残留。提交 b61505c。"
        ),
        "status": "valid",
        "task_id": "TASK-140",
        "covers": {"files": FILES, "requirements": [], "tasks": ["TASK-140"]},
        "version_binding": {"git_commit": COMMIT, "file_hashes": FILE_HASHES},
    },
)

apply(
    "goal.update",
    {"id": "GOAL-008", "required_evidence": [EVIDENCE_ID]},
)

apply(
    "task.finish",
    {
        "task_id": "TASK-140",
        "summary": (
            "PC 开发环境 uv 复现与遗留缺陷修复：新增 docs/dev-environment.md 与 "
            "pc/server/requirements.lock；仓库内 .venv（CPython 3.11.15）；README 端口 8000→8011；"
            "seed.py 演示素材默认路径回退到 <data_dir>/uploads；test_select_directory 改为"
            "平台无关断言；修复备份恢复在 Windows 的 WinError 32（release_database_handles + "
            "closing 显式关闭连接）。pytest 全量 150 通过/0 失败，真实 uvicorn 进程恢复成功。提交 b61505c。"
        ),
    },
)

print("done")
