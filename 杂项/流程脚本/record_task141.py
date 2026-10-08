import hashlib
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r"C:\Users\12187\.config\opencode\vibe-workflow\scripts")
from state_context import apply_command, open_store, refresh_evidence  # noqa: E402
from state_store import SCHEMA_VERSION  # noqa: E402

ROOT = Path(r"D:\Project\辅料称重防错系统")
REPO = ROOT / "milk-milk-go"
COMMIT = sys.argv[1]

DOC = "milk-milk-go/docs/dev-environment.md"
DOC_HASH = hashlib.sha256((REPO / "docs/dev-environment.md").read_bytes()).hexdigest()


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
    print(f"[ok] {action} -> {json.dumps(res, ensure_ascii=False)[:110]}")


apply(
    "task.create",
    {
        "id": "TASK-141",
        "title": "补充前端构建说明（pc/dist 未纳入版本控制）",
        "goal_id": None,
        "extensions": {
            "kind": "task",
            "owner": "agent",
            "authority": "A",
            "phase": "implementation",
            "risk": "low",
            "priority": "medium",
            "goal": "补全 docs/dev-environment.md 的前端构建说明：pc/dist 被 gitignore，新克隆需先构建。",
            "inputs": ["docs/dev-environment.md", "pc/package.json", "pc/vite.config.ts"],
            "outputs": ["docs/dev-environment.md 第 5 节与常见问题表"],
            "plan": ["确认 dist 被忽略且后端托管 dist", "拆分构建/热更新两种方式", "补常见问题条目"],
            "done_when": ["文档说明 npm run build 路径且解释 8011 返回 JSON 的原因"],
            "related_business_logic": [],
            "related_decisions": [],
            "verification": {"commands": ["回读文档 + 校验 8011 根路径返回 HTML"], "status": "passed"},
        },
    },
)

apply(
    "task.begin",
    {
        "task_id": "TASK-141",
        "run_id": "RUN-141-frontend-doc",
        "next_action": "记录证据并把受影响的原证据置为 stale",
    },
)

apply(
    "evidence.record",
    {
        "id": "EV-TASK-141-FRONTEND-DOC",
        "kind": "documentation",
        "subject": (
            "TASK-141：docs/dev-environment.md 第 5 节拆分为「npm run build 后由后端 8011 托管」"
            "与「npm run dev 热更新（5173）」两种方式，并说明 pc/dist 被 gitignore、"
            "未构建时 8011 根路径只返回 JSON；常见问题表补对应条目。提交 a47080b。"
        ),
        "status": "valid",
        "task_id": "TASK-141",
        "covers": {"files": [DOC], "requirements": [], "tasks": ["TASK-141"]},
        "version_binding": {"git_commit": COMMIT, "file_hashes": {DOC: DOC_HASH}},
    },
)

result = refresh_evidence(
    ROOT,
    "docs/dev-environment.md 补充前端构建说明后内容变化，原证据对新版本失效",
)
print("refresh ->", json.dumps(result, ensure_ascii=False)[:300])

apply(
    "task.finish",
    {
        "task_id": "TASK-141",
        "summary": (
            "补充前端构建说明：docs/dev-environment.md 第 5 节拆分构建（npm run build，由 8011 托管）"
            "与开发热更新（npm run dev，5173）两种方式，说明 pc/dist 被 gitignore、未构建时 8011 "
            "根路径只返回 JSON，常见问题表补条目。提交 a47080b。"
        ),
    },
)

print("done")
