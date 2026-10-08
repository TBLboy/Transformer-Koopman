import hashlib
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')
repo = Path(r'D:\Project\vibe-coding\vibe-coding')

AUDITED = [
    ('vibe-coding/scripts/opencode_installer.py', repo / 'scripts/opencode_installer.py'),
    ('vibe-coding/tests/test_opencode_installer.py', repo / 'tests/test_opencode_installer.py'),
    ('vibe-coding/tests/test_opencode_plugin.py', repo / 'tests/test_opencode_plugin.py'),
    ('vibe-coding/tests/test_opencode_surface.py', repo / 'tests/test_opencode_surface.py'),
    ('.project-log/docs/windows-test-failure-audit.md', root / '.project-log/docs/windows-test-failure-audit.md'),
]

file_hashes = {rel: hashlib.sha256(p.read_bytes()).hexdigest() for rel, p in AUDITED}


def apply(action, payload):
    store = open_store(root, heal=True)
    apply_command(root, {
        'schema_version': 1,
        'command_id': uuid.uuid4().hex,
        'expected_revision': store.status()['revision'],
        'action': action,
        'payload': payload,
    })
    print('OK', action, payload.get('id') or payload.get('task_id'))


apply('evidence.record', {
    'id': 'EV-WIN-AUDIT-001',
    'kind': 'audit',
    'subject': 'Windows 平台测试失败报告（5 类 21 项）逐条核查：1 类真实产品缺陷 + 4 类测试平台不兼容',
    'status': 'valid',
    'task_id': 'TASK-098',
    'covers': {
        'files': [rel for rel, _ in AUDITED],
        'requirements': [],
        'tasks': ['TASK-098'],
    },
    'version_binding': {
        'git_commit': 'db7ed85260652292b6b46caade1197ab735b5ee3',
        'diff_hash': None,
        'file_hashes': file_hashes,
    },
})

apply('task.finish', {
    'task_id': 'TASK-098',
    'summary': (
        '核查外部 Windows 测试失败报告：5 类根因全部成立，21 项（8 failures / 13 errors / 3 skipped，Ran 246 tests）逐项复现，'
        '报告引用的行号全部命中。类别 1 确认为真实产品缺陷——installer 用 str(relative_to()) 造键，'
        'plan_sync 原样写入安装状态文件，实盘 103 键中 100 键含反斜杠、39 键混合分隔符；'
        '加重情节：状态文件因此不可跨 OS 迁移，且与 Codex 侧 global_installer.py 的 as_posix() 做法构成实现漂移。'
        '类别 2-5（symlink 特权 12、subprocess 缺 encoding 1、假 shim 无扩展名 4、可执行位断言 1）均为测试未做平台适配；'
        '类别 3 的 gbk/0xff/47 依赖非 PYTHONUTF8 环境（设 PYTHONUTF8=1 时签名为 utf-8/0xc0/10），根因一致。'
        '报告唯一偏差：漏列 test_opencode_surface.py:300 的 symlink 调用点（不影响计数）。'
        '证据 EV-WIN-AUDIT-001 + .project-log/docs/windows-test-failure-audit.md。'
        '未验证项：多 Windows locale 交叉、Linux/macOS 对照、既有状态文件迁移策略、Windows CI 覆盖。'
    ),
})

print('revision', refresh_views(root)['revision'])
