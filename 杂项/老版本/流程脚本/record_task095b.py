import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')
repo = root / 'vibe-coding'


def apply(action, payload):
    store = open_store(root, heal=True)
    revision = store.status()['revision']
    envelope = {
        'schema_version': 1,
        'command_id': uuid.uuid4().hex,
        'expected_revision': revision,
        'action': action,
        'payload': payload,
    }
    result = apply_command(root, envelope)
    print('OK', action)
    return result


def digest(rel):
    return hashlib.sha256((root / rel).read_bytes()).hexdigest()


head = subprocess.run(
    ['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True
).stdout.strip()

FILES = [
    'vibe-coding/skills/a-project-log-archive/scripts/archive.py',
    'vibe-coding/skills/a-project-log-align/scripts/align.py',
    'vibe-coding/runtime/scripts/state_context.py',
    'vibe-coding/runtime/scripts/init_project.py',
    'vibe-coding/runtime/scripts/state_ledger.py',
    'vibe-coding/runtime/scripts/workflow_state.py',
    'vibe-coding/runtime/scripts/state_views.py',
    'vibe-coding/.gitattributes',
    '.project-log/.gitattributes',
    '.project-log/ledger/v1/ledger.jsonl',
]

apply('evidence.record', {
    'id': 'EV-WINDOWS-EOL-001',
    'kind': 'acceptance',
    'subject': 'Windows/Ubuntu 行尾一致性修复：LF 账本、逐字节可比、归档远端可核验',
    'status': 'valid',
    'task_id': 'TASK-095',
    'covers': {'files': FILES, 'requirements': [], 'tasks': ['TASK-095']},
    'version_binding': {
        'git_commit': head,
        'diff_hash': None,
        'file_hashes': {f: digest(f) for f in FILES},
    },
})

apply('record.create', {
    'kind': 'decision',
    'id': 'DEC-006',
    'title': 'Project Log 与框架源码在所有平台一律以 LF 为唯一规范行尾',
    'status': 'active',
    'payload': {
        'authority': 'B',
        'decision': (
            'Project Log 账本是逐字节归档的权威对象；Windows 默认文本模式写入会把 LF 变成 CRLF，'
            '导致 Windows 与 Ubuntu 产出的账本字节不同，并使按原始字节比对的证据指纹全部失配。'
            '因此账本/视图/初始化种子/align 标记一律显式以 newline="\\n" 写入；'
            '初始化在 .project-log/.gitattributes 落 * -text；框架仓库以 .gitattributes 固定 * text=auto eol=lf。'
        ),
        'rationale': 'LF 是账本逐字节可比与证据指纹跨平台一致的唯一前提。',
        'consequences': [
            'Windows 检出/写出的 Project Log 与 Ubuntu 完全一致',
            '既有 CRLF 工作树与本地 .project-log 已一次性归一化为 LF（内容无损：git hash-object == 索引 blob）',
            'evidence 指纹仍按原始字节比对，故跨平台仓库应以 .gitattributes 而非 core.autocrlf 控制行尾',
        ],
        'evidence': ['EV-WINDOWS-EOL-001'],
    },
})

apply('task.finish', {
    'task_id': 'TASK-095',
    'summary': (
        '归档通过并推送：KB work_record=ab62f02ca54e0693deadc0c979036d735572aafb，'
        '提交账本 683 行全 LF、0 CRLF，KB 工作区干净，远端 ref 可核验。'
        '根因修复：state_ledger.append_event 加 os.O_BINARY（Windows 文本模式把 LF 写成 CRLF 的真正源头）、'
        '_ensure_ledger_ignore/workflow_state.save_state/state_views 发布锁/align.MARKER 一律 newline="\\n"、'
        'state_context 新增 .project-log/.gitattributes(* -text)、init_project 种子改 LF 写入并纳入 .gitattributes、'
        'archive.py 改 as_posix 路径、git_environment 代理大小写、Windows 盘符/file://~ 展开与自指守卫、'
        '仓库 .gitattributes 改 * text=auto eol=lf。安装副本 7 文件同步一致。'
        '回归 245 tests（仅 test_opencode_* 因 Windows 权限 os.symlink/POSIX 假脚本失败，属既有环境限制）；validate_package 通过。'
        '本地 .project-log 223 文件与仓库 148 文件归一化为 LF（内容无损）。'
        '未验证：evidence 表 166 条 stale 属历史累积与项目根迁移（多数覆盖路径仍以旧根 runtime/... 记录），本次未处理；'
        'CONTRACT-014 覆盖文件真实缺失。'
    ),
})

print(json.dumps(refresh_views(root))[:300])
