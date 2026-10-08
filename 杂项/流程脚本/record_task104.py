import hashlib
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')
repo = root / 'vibe-coding'
NEW_COMMIT = '7f102fc'


def apply(action, payload):
    store = open_store(root, heal=True)
    receipt = apply_command(root, {
        'schema_version': 1, 'command_id': uuid.uuid4().hex,
        'expected_revision': store.status()['revision'],
        'action': action, 'payload': payload,
    })
    print('OK', action, payload.get('id') or payload.get('task_id'), '->', receipt.get('result'))
    return receipt


files = subprocess.run(
    ['git', '-C', str(repo), 'diff', '--name-only', '13b9d4c', NEW_COMMIT],
    capture_output=True, text=True, check=True,
).stdout.split()
covers_files = ['vibe-coding/' + p for p in files]
hashes = {rel: hashlib.sha256((root / rel).read_bytes()).hexdigest() for rel in covers_files}
print('touched files:', len(covers_files))

apply('task.create', {
    'id': 'TASK-104',
    'title': '把 Windows 平台修复的三个提交合入主分支 opencode 并验证',
    'goal_id': None,
    'extensions': {
        'authority': 'B',
        'kind': 'task',
        'phase': 'alignment',
        'risk': 'standard',
        'implementer': 'vibe-main (opencode main agent)',
        'inputs': ['用户指令：把这三个提交合到 opencode 分支（主分支）',
                   '0fb57a0 / 01cec84 / dc9db42'],
        'done_when': [
            '三个提交 cherry-pick 到 opencode，无冲突',
            '被触及路径与已通过 CI 的 dc9db42 逐字节一致',
            'validate_package 在合并后的树中通过',
            'opencode 已推送且 CI（windows-latest + ubuntu-latest）转绿',
            '不触碰另一会话的未提交文件（AI_INSTALL.md、docs/auto-research/*）',
        ],
        'related_business_logic': [],
        'plan': ['建独立 worktree 避免干扰另一会话', 'cherry-pick 三提交',
                 '字节级比对 dc9db42', '快进 opencode 并推送', '观察 CI'],
        'outputs': ['EV-WIN-AUDIT-008'],
    },
})

apply('task.begin', {'task_id': 'TASK-104', 'run_id': 'RUN-115',
                     'next_action': '记录集成证据并收口'})

apply('evidence.record', {
    'id': 'EV-WIN-AUDIT-008',
    'kind': 'integration',
    'subject': (
        'Windows 平台修复三个提交（0fb57a0/01cec84/dc9db42）已 cherry-pick 合入主分支 opencode：'
        '13b9d4c..7f102fc 快进推送；23 个被触及文件与已通过 CI 的 dc9db42 逐字节一致；'
        'opencode 上的 CI run 36390303777 conclusion=success（ubuntu 34s / windows 3m16s）。'
    ),
    'status': 'valid',
    'task_id': 'TASK-104',
    'covers': {'files': covers_files, 'requirements': [],
               'tasks': ['TASK-100', 'TASK-101', 'TASK-102', 'TASK-103', 'TASK-104']},
    'version_binding': {'git_commit': NEW_COMMIT, 'diff_hash': None, 'file_hashes': hashes},
})

apply('task.finish', {'task_id': 'TASK-104', 'summary': (
    '把 Windows 平台修复的三个提交合入主分支 opencode。'
    '做法：`git worktree add` 建独立工作树（避免切换分支时被另一会话在 opencode-auto-research 上的未提交文件阻断），'
    '在其中 cherry-pick 0fb57a0/01cec84/dc9db42（无冲突），再用 `switch --force-create opencode` 把 opencode 从 13b9d4c 快进到 7f102fc，'
    '推送 13b9d4c..7f102fc（快进，无 merge commit，历史线性），随后删除临时工作树。'
    '验证：23 个被触及文件与已通过 CI 的 dc9db42 逐字节一致（逐文件 sha 比对 23/23）；合并后树 validate_package 通过；'
    'opencode 分支 CI run 36390303777 = success（ubuntu-latest 34s、windows-latest 3m16s，经 GitHub API 复核 conclusion/head_sha/head_branch）。'
    '约束遵守：未触碰另一会话的 4 个未提交文件；opencode-auto-research 保留（含其 TASK-097 提交与未提交改动）。'
    '未做：未合并/未删除 opencode-auto-research；未创建 PR（用户未要求）。'
)}) 

print('revision', refresh_views(root)['revision'])
