import hashlib
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')


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
    print('OK', action, '->', json.dumps(result)[:160] if not isinstance(result, dict) else 'dict')
    return result


def digest(rel):
    data = (root / rel).read_bytes()
    return hashlib.sha256(data).hexdigest()


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

apply('task.create', {
    'id': 'TASK-095',
    'title': '修复 Windows/Ubuntu 行尾一致性缺陷并完成真实归档',
    'goal_id': None,
    'extensions': {
        'authority': 'B',
        'kind': 'task',
        'phase': 'implementation',
        'risk': 'high',
        'implementer': 'vibe-main (opencode main agent, serial-role-fallback)',
        'done_when': [
            '定位并修复 Windows 下 Project Log 行尾（CRLF）缺陷，含账本写入路径',
            'Windows 产出的账本字节 == render_ledger 字节（LF），归档字节比对通过',
            '仓库与工作树以 .gitattributes 固定 eol=lf',
            '真实归档成功且远端可核验',
            '安装副本与源码逐文件一致',
            '回归测试与 validate_package 通过',
        ],
        'related_business_logic': [],
        'inputs': ['REQ-TERM-LAYOUT-001'],
        'plan': [],
        'depends_on': [],
        'outputs': ['EV-WINDOWS-EOL-001', 'DEC-006'],
    },
})

apply('task.begin', {
    'task_id': 'TASK-095',
    'run_id': 'RUN-106',
    'next_action': '绑定证据并完成任务，然后重新归档',
})

apply('evidence.record', {
    'id': 'EV-WINDOWS-EOL-001',
    'kind': 'acceptance',
    'subject': 'Windows/Ubuntu 行尾一致性修复与真实归档（LF 账本、逐字节可比、远端可核验）',
    'status': 'valid',
    'task_id': 'TASK-095',
    'covers': {
        'files': FILES,
        'requirements': [],
        'tasks': ['TASK-095'],
    },
    'version_binding': {
        'file_hashes': {f: digest(f) for f in FILES},
        'ledger_events': 683,
        'kb_commit': 'ab62f02ca54e0693deadc0c979036d735572aafb',
        'kb_ref': 'refs/heads/work_record',
        'tests': 'test_archive_skill 38/38, test_state_ledger 19/19, validate_package pass',
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
            'Project Log 的账本是逐字节归档的权威对象；Windows 默认文本模式会在写入时把 LF 变成 CRLF，'
            '使 Windows 与 Ubuntu 产出的账本字节不同、并让按原始字节比对的证据指纹全部失配。'
            '因此：账本、视图、初始化种子、align 标记一律显式以 newline="\\n" 写入；'
            '初始化在 .project-log/.gitattributes 落 * -text；'
            '框架仓库以 .gitattributes 固定 * text=auto eol=lf。'
        ),
        'rationale': 'LF 是账本逐字节可比的唯一前提，也是证据指纹跨平台一致的前提。',
        'consequences': [
            'Windows 检出/写出的 Project Log 与 Ubuntu 完全一致',
            '既有 CRLF 工作树与本地 .project-log 已一次性归一化为 LF（内容无损：git hash-object 与索引 blob 相同）',
            'evidence 指纹仍按原始字节比对，故依赖工作树保持 LF；跨平台仓库应以 .gitattributes 而非 core.autocrlf 控制',
        ],
        'evidence': ['EV-WINDOWS-EOL-001'],
    },
})

apply('task.finish', {
    'task_id': 'TASK-095',
    'summary': (
        '归档通过并推送（KB work_record=ab62f02，提交账本 683 行全 LF、0 CRLF，工作区干净）。'
        '根因修复：state_ledger.append_event 加 os.O_BINARY（Windows 文本模式把 LF 写成 CRLF 的真正源头）、'
        '_ensure_ledger_ignore 与 workflow_state.save_state 与 state_views 锁与 align.MARKER 一律 newline="\\n"、'
        'state_context 新增 .project-log/.gitattributes(* -text)、init_project 种子改 LF 写入并纳入 .gitattributes、'
        'archive.py 改 as_posix 路径 + git_environment 代理大小写 + Windows 盘符/file://~ 展开与自指守卫、'
        '仓库 .gitattributes 改 * text=auto eol=lf。安装副本 7 文件同步一致。'
        '回归 245 tests（仅 test_opencode_* 因 Windows 权限/POSIX 假脚本失败，属既有环境限制）；validate_package 通过。'
        '本地 .project-log 223 文件与仓库 148 文件归一化为 LF（内容无损，git hash-object == 索引 blob）。'
        '未验证：evidence 表 166 条 stale 属历史累积与项目根迁移（多数覆盖路径以旧根 runtime/... 记录），未在本次处理；'
        'CONTRACT-014 覆盖文件真实缺失。'
    ),
})

print('=== render ===')
print(json.dumps(refresh_views(root))[:300])
