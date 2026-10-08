import hashlib
import json
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

DB = (r'D:\Project\vibe-coding\.project-log\.state\c15166f6f14948aa85604021638f0b1a'
      r'\2428c28d612809201bbb0fec8029f394b8ca9a64ea9618cfc5ecc99617f72274\state.sqlite3')
root = Path(r'D:\Project\vibe-coding')
repo = root / 'vibe-coding'

REBIND = [
    'ARCHIVE-EXPORT-LEGACY1', 'DESIGN-012', 'EV-OPENCODE-009', 'EV-OPENCODE-025',
    'EV-OPENCODE-026', 'OPENCODE-BRANCH-AUDIT', 'OPENCODE-MIGRATION-FINAL-REVIEW-V2',
    'OPENCODE-MIGRATION-FINAL-REVIEW-V3', 'SC-TERM-CONTRACT-V2',
]
# AUDIT-007 is deliberately excluded: it covers the deprecated codex install.

conn = sqlite3.connect('file:' + DB + '?mode=ro', uri=True)
cols = [r[1] for r in conn.execute('pragma table_info(evidence)')]
source = {}
for r in conn.execute('select * from evidence'):
    e = dict(zip(cols, r))
    source[e['id']] = e

head = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                      capture_output=True, text=True).stdout.strip()


def apply(action, payload):
    store = open_store(root, heal=True)
    envelope = {
        'schema_version': 1,
        'command_id': uuid.uuid4().hex,
        'expected_revision': store.status()['revision'],
        'action': action,
        'payload': payload,
    }
    apply_command(root, envelope)
    print('OK', action, payload.get('id') or payload.get('task_id'))


def digest(rel):
    return hashlib.sha256((root / rel).read_bytes()).hexdigest()


for eid in REBIND:
    e = source[eid]
    covers = json.loads(e['covers'])
    files = covers.get('files') or []
    apply('evidence.record', {
        'id': eid + '-EOL-REBIND',
        'kind': e['kind'],
        'subject': (e['subject'] or eid) + ' [EOL rebind: covered bytes provably unchanged]',
        'status': 'valid',
        'task_id': e['task_id'],
        'covers': covers,
        'version_binding': {
            'git_commit': head,
            'diff_hash': None,
            'file_hashes': {f: digest(f) for f in files},
        },
    })

apply('record.create', {
    'kind': 'decision',
    'id': 'DEC-022',
    'title': '存量 stale 证据的处理策略：只能重绑可证明未变的产物，不得伪造新鲜度',
    'status': 'active',
    'payload': {
        'authority': 'B',
        'statement': (
            'evidence 指纹按原始字节比对，故框架演进与项目根迁移会让历史证据自然 stale。'
            'stale 是这类记录的合法终态：不重写历史、不伪造新鲜度。'
            '只有当一个记录的覆盖产物可证明逐字节未变时（含仅行尾差异），才以 <原id>-EOL-REBIND 形式重绑为有效。'
        ),
        'inventory': '.project-log/docs/evidence-inventory.md',
        'classification': {
            'applicable_stale_rebound': len(REBIND),
            'changed_input': 59,
            'missing_input': 97,
            'legacy_external_dead': 1,
        },
        'actions': [
            'INVALIDATE-REASONS 保持原样，仅新增重绑记录，不删除历史',
            'AUDIT-007 覆盖已弃用的 codex 安装，保持 stale 不重绑',
            'changed-input / missing-input 记录不复活：框架确已演进，且无活跃 Goal 声明其为必需证据',
        ],
        'rationale': '保持证据账本可审计：历史结果与当前适用性分离，重绑必须可证明。',
    },
})

print(json.dumps(refresh_views(root))[:200])
