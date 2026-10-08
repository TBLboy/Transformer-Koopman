import hashlib
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')
repo = Path(r'D:\Project\vibe-coding\vibe-coding')


def apply(action, payload):
    store = open_store(root, heal=True)
    receipt = apply_command(root, {
        'schema_version': 1,
        'command_id': uuid.uuid4().hex,
        'expected_revision': store.status()['revision'],
        'action': action,
        'payload': payload,
    })
    print('OK', action, payload.get('id') or payload.get('task_id'), '->', receipt.get('result'))
    return receipt


# --- 1. review record while EV-WIN-AUDIT-001 is still valid (refs must be valid + non-stale)
apply('review.record', {
    'id': 'REVIEW-WIN-AUDIT-001',
    'task_id': 'TASK-098',
    'reviewer': 'verification-reviewer (subagent ses_f19cb11c2ffeQx66P1Bg7WFFp5)',
    'verdict': 'conditional',
    'scope': {
        'reviewed_evidence': 'EV-WIN-AUDIT-001',
        'method': '自行读代码、读取实盘状态文件、双环境复跑全量套件（不采信被审方描述）',
        'confirmed': [
            '类别 1 为真实产品缺陷（installer str(relative_to()) 造键 → 状态文件反斜杠键）',
            '类别 2/4/5 为测试平台不兼容',
            '全量套件总数 246、failures 8',
        ],
        'corrections_required': [
            '混合分隔符键数：39 应为 37（39 是“含正斜杠”的键数）',
            '类别 3 根因：首要为 bash 解析到 WSL 存根；单独补 encoding= 不能修复（只会转为 returncode 断言失败）',
            '13 errors / 3 skipped 依赖 WSL bash 存根在 PATH 上（否则 12 errors / 1 skipped），文档未披露',
        ],
        'exit_condition': '修正上述 3 处后可判 go',
    },
    'evidence_refs': ['EV-WIN-AUDIT-001'],
})

# --- 2. amendment round as its own task (a finished task cannot be reopened)
apply('task.create', {
    'id': 'TASK-099',
    'title': '按独立复核意见修正 Windows 审计结论（3 处）并重绑证据',
    'goal_id': None,
    'extensions': {
        'authority': 'B',
        'kind': 'task',
        'phase': 'verification',
        'risk': 'standard',
        'implementer': 'vibe-main (opencode main agent, serial-role-fallback)',
        'inputs': ['REVIEW-WIN-AUDIT-001 (verdict=conditional)', 'EV-WIN-AUDIT-001'],
        'done_when': [
            '更正混合分隔符计数（39 -> 37）并给出精确分解',
            '重写类别 3 根因归属：首要因素 = bash 解析到 WSL 存根；次要 = 缺 encoding=（且单独修复无效）',
            '披露 13 errors / 3 skipped 的环境依赖（WSL bash 存根在 PATH 上；否则 12 / 1）',
            '修正 test_opencode_surface.py:300 的推理表述',
            '旧证据 EV-WIN-AUDIT-001 标记 stale（不删除），新证据绑定修订后文档哈希',
            '独立复核判定 go',
        ],
        'related_business_logic': [],
        'plan': [
            '逐条自行复验复核意见（不直接采信子 Agent 结论）',
            '修订 .project-log/docs/windows-test-failure-audit.md',
            '标记旧证据 stale 并记录新证据',
            '提交独立复核确认修订到位',
        ],
        'outputs': ['EV-WIN-AUDIT-002', 'REVIEW-WIN-AUDIT-002'],
    },
})

apply('task.begin', {
    'task_id': 'TASK-099',
    'run_id': 'RUN-110',
    'next_action': '修订审计文档并重绑证据，然后提交独立复核',
})

# --- 3. old evidence goes stale (artifact corrected); never delete it
apply('evidence.invalidate', {
    'id': 'EV-WIN-AUDIT-001',
    'reason': (
        'Covered artifact .project-log/docs/windows-test-failure-audit.md was corrected after '
        'REVIEW-WIN-AUDIT-001 (mixed-separator count 39->37; class-3 root cause re-attributed to the '
        'WSL bash stub; environment contingency of 13/3 counts disclosed). '
        'Recorded file_hashes no longer match the corrected bytes; superseded by EV-WIN-AUDIT-002.'
    ),
})

# --- 4. new evidence bound to the corrected document
audited = [
    ('vibe-coding/scripts/opencode_installer.py', repo / 'scripts/opencode_installer.py'),
    ('vibe-coding/tests/test_opencode_installer.py', repo / 'tests/test_opencode_installer.py'),
    ('vibe-coding/tests/test_opencode_plugin.py', repo / 'tests/test_opencode_plugin.py'),
    ('vibe-coding/tests/test_opencode_surface.py', repo / 'tests/test_opencode_surface.py'),
    ('vibe-coding/tests/test_cross_platform_surface.py', repo / 'tests/test_cross_platform_surface.py'),
    ('.project-log/docs/windows-test-failure-audit.md', root / '.project-log/docs/windows-test-failure-audit.md'),
]
file_hashes = {rel: hashlib.sha256(p.read_bytes()).hexdigest() for rel, p in audited}

apply('evidence.record', {
    'id': 'EV-WIN-AUDIT-002',
    'kind': 'audit',
    'subject': (
        'Windows 平台测试失败报告核查（修订版，取代 EV-WIN-AUDIT-001）：5 类根因全部成立；'
        '类别 1 = 真实产品缺陷（安装状态文件写反斜杠键，103 键中 100 含反斜杠、37 混合）；'
        '类别 2-5 = 测试平台不兼容；类别 3 首要触发因素为 bash 解析到 WSL 存根。'
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
})

print('revision', refresh_views(root)['revision'])
