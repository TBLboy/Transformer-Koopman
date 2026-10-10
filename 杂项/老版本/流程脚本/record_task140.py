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
    print(f"[ok] {action} -> {json.dumps(res, ensure_ascii=False)[:140]}")


def sha(rel):
    return hashlib.sha256((REPO / rel).read_bytes()).hexdigest()


FILES = [
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

apply(
    "goal.create",
    {
        "id": "GOAL-008",
        "title": "在本机用 uv 复现 PC 端开发环境并修复遗留缺陷",
        "extensions": {
            "kind": "goal",
            "owner": "agent",
            "priority": "high",
            "success_conditions": [
                "PC 端开发环境可依据文档用 uv 完整复现（venv/依赖/种子/运行/测试）",
                "后端测试全量通过，0 失败",
                "备份恢复在 Windows 真实进程中可用且数据完好",
            ],
            "required_evidence": ["EV-TASK-140-DEVENV"],
        },
    },
)

apply(
    "task.create",
    {
        "id": "TASK-140",
        "title": "PC 开发环境 uv 复现文档与遗留缺陷修复",
        "goal_id": "GOAL-008",
        "extensions": {
            "kind": "task",
            "owner": "agent",
            "authority": "B",
            "phase": "implementation",
            "risk": "medium",
            "priority": "high",
            "goal": "在本机用 uv 复现 PC 端开发环境，并修复上一轮遗留的缺陷与测试失败。",
            "inputs": ["milk_preview 分支代码", "pc/data/uploads 演示素材", "pc/server/requirements.txt"],
            "outputs": [
                "docs/dev-environment.md",
                "pc/server/requirements.lock",
                "备份恢复 Windows 修复",
                "seed.py 默认素材路径修复",
            ],
            "plan": [
                "生成 requirements.lock 并新建仓库内 .venv",
                "编写 uv 复现文档并修正 README 端口",
                "修 seed.py 演示素材默认路径",
                "修 test_select_directory 平台断言",
                "排查并修复 5 个 test_restore Windows 失败",
                "全量回归测试与真实进程验证",
            ],
            "done_when": [
                "uv 复现文档存在且步骤可执行",
                "requirements.lock 存在且与实际环境一致",
                "pytest 全量 0 失败",
                "真实 uvicorn 进程执行备份恢复返回 success",
            ],
            "related_business_logic": ["BL-BACKUP-001"],
            "related_decisions": ["DEC-054"],
            "verification": {
                "commands": [
                    "pytest -q",
                    "uvicorn 8011 + POST /operations/restore",
                    "Invoke-RestMethod /api/v1/health",
                ],
                "status": "passed",
            },
        },
    },
)

apply(
    "task.begin",
    {
        "task_id": "TASK-140",
        "run_id": "RUN-140-devenv",
        "next_action": "记录验证证据与决策，随后完成任务",
    },
)

apply(
    "record.create",
    {
        "kind": "decision",
        "id": "DEC-054",
        "title": "Windows 下恢复备份前必须释放 SQLite 文件句柄",
        "status": "active",
        "payload": {
            "authority": "B",
            "date": "2026-10-06",
            "context": (
                "TASK-140 排查 5 个 test_restore 失败：Windows 上恢复备份报 WinError 32"
                "（文件被占用），恢复流程无法把 milk_weigh.sqlite3 移动到回滚目录。"
                "实测确认 with sqlite3.connect(...) 只提交事务、不关闭连接，句柄会因引用环"
                "延迟到 GC 才释放；同时应用自身的 SQLAlchemy 连接池也持续持有数据库文件。"
                "Windows 不允许替换仍被打开的文件，POSIX 无此限制。"
            ),
            "decision": (
                "恢复数据库文件前显式释放全部 SQLite 句柄：新增 app/db/session.py::"
                "release_database_handles() 关闭连接池，POST /operations/restore 先 db.close()"
                " 再调用它；测试与工具代码统一改用 contextlib.closing 显式关闭连接。"
            ),
            "rationale": (
                "最小且不改变恢复语义：仍按原设计原地替换数据库文件（接口本就返回"
                "restart_required=true），只是先归还句柄。替代方案（改用 SQLite backup API "
                "覆盖写入、或要求停服恢复）改动更大或降低可用性。"
            ),
            "alternatives": (
                "1) 用 SQLite backup API 把恢复数据写回现有文件——语义与回滚逻辑改动大；"
                "2) 要求先停服务再恢复——牺牲在线恢复能力；"
                "3) 仅改测试不修服务——生产环境仍会失败。"
            ),
            "consequences": (
                "恢复前连接池被清空，恢复后引擎按需重建到替换后的数据库文件；"
                "恢复接口在 Windows 真实进程验证通过。同类隐患（测试中 10 处 sqlite3 连接）"
                "一并消除。"
            ),
        },
    },
)

apply(
    "evidence.record",
    {
        "id": "EV-TASK-140-DEVENV",
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
        "covers": {
            "files": FILES,
            "requirements": [],
            "tasks": ["TASK-140"],
        },
        "version_binding": {
            "git_commit": COMMIT,
            "file_hashes": {path: sha(path) for path in FILES},
        },
    },
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
