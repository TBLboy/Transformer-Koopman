import hashlib
import sqlite3
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')
repo = Path(r'D:\Project\vibe-coding\vibe-coding')

store = open_store(root, heal=True)
print('revision before:', store.status()['revision'])

audited = [
    ('vibe-coding/scripts/opencode_installer.py', repo / 'scripts/opencode_installer.py'),
    ('vibe-coding/tests/test_opencode_installer.py', repo / 'tests/test_opencode_installer.py'),
    ('vibe-coding/tests/test_opencode_plugin.py', repo / 'tests/test_opencode_plugin.py'),
    ('vibe-coding/tests/test_opencode_surface.py', repo / 'tests/test_opencode_surface.py'),
    ('vibe-coding/tests/test_cross_platform_surface.py', repo / 'tests/test_cross_platform_surface.py'),
    ('.project-log/docs/windows-test-failure-audit.md', root / '.project-log/docs/windows-test-failure-audit.md'),
]
file_hashes = {rel: hashlib.sha256(p.read_bytes()).hexdigest() for rel, p in audited}

apply_command(root, {
    'schema_version': 1,
    'command_id': uuid.uuid4().hex,
    'expected_revision': store.status()['revision'],
    'action': 'evidence.record',
    'payload': {
        'id': 'EV-WIN-AUDIT-002',
        'kind': 'audit',
        'subject': (
            'Windows 平台测试失败报告核查（修订版，取代已 stale 的 EV-WIN-AUDIT-001）：'
            '5 类根因全部成立；类别 1 = 真实产品缺陷（安装状态文件写反斜杠键：103 键中 100 含反斜杠、37 混合分隔符）；'
            '类别 2-5 = 测试平台不兼容；类别 3 首要触发因素为 bash 解析到 WSL 存根，补 encoding= 不足以修复；'
            '13 errors / 3 skipped 依赖 WSL bash 存根在 PATH 上（否则 12 / 1）。'
        ),
        'status': 'valid',
        'task_id': 'TASK-099',
        'covers': {
            'files': [rel for rel, _ in audited],
            'requirements': [],
            'tasks': ['TASK-098', 'TASK-099'],
        },
        'version_binding': {
            'git_commit': 'db7ed85260652292b6b46caade1197ab735b5ee3',
            'diff_hash': None,
            'file_hashes': file_hashes,
        },
    },
})
print('OK evidence.record EV-WIN-AUDIT-002')
print('revision after:', refresh_views(root)['revision'])

db = None
for base, _dirs, files in __import__('os').walk(str(root / '.project-log' / '.state')):
    for name in files:
        if name.endswith('.sqlite3'):
            db = Path(base) / name
conn = sqlite3.connect('file:' + db.as_posix() + '?mode=ro', uri=True)
conn.row_factory = sqlite3.Row

print()
print('=== reviews ===')
for r in conn.execute('SELECT * FROM reviews ORDER BY rowid DESC LIMIT 3'):
    d = dict(r)
    print({k: d[k] for k in ('id', 'task_id', 'reviewer', 'verdict') if k in d})

print()
print('=== tasks (latest 3) ===')
for r in conn.execute('SELECT id, title, status, run_id FROM tasks ORDER BY created_sequence DESC LIMIT 3'):
    print(dict(r))

print()
print('=== evidence (latest 3) ===')
for r in conn.execute('SELECT id, task_id, status FROM evidence ORDER BY rowid DESC LIMIT 3'):
    print(dict(r))
