import hashlib
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')
REPO = root / 'vibe-coding'


def apply(action, payload):
    store = open_store(root, heal=True)
    apply_command(root, {
        'schema_version': 1, 'command_id': uuid.uuid4().hex,
        'expected_revision': store.status()['revision'],
        'action': action, 'payload': payload,
    })
    print('OK', action, payload.get('id') or payload.get('task_id') or '')


# 1) 新增 C 级决策：分支改名（用户已批准）
apply('record.create', {
    'kind': 'decision', 'id': 'DEC-029', 'status': 'active',
    'title': '把主线分支 opencode 改名为 opencode-main，消除 .git/opencode 缓存遮蔽',
    'payload': {
        'authority': 'C', 'user_approval': 'approved', 'category': 'tooling',
        'context': (
            'DEC-028 查明：opencode 工具链把项目 id 缓存到 $GIT_DIR/opencode（固定文件名），'
            '而 git 解析引用名时优先命中 $GIT_DIR/<name>，导致任何名为 opencode 的分支被永久遮蔽：'
            '裸名取版本号的命令失败（git log/diff opencode → fatal: bad object opencode）。'
            '用户在三个方案中选择了改名（A），接受其破坏 main/opencode/codex 按宿主命名约定的代价。'
        ),
        'decision': (
            '把主线分支 opencode 改名为 opencode-main；缓存文件 .git/opencode 保持原样不动'
            '（保持插件 project id 不变，避免既有插件数据失联）。'
        ),
        'action': (
            'git branch -m opencode opencode-main → push -u origin opencode-main → '
            'push origin --delete opencode。旧名末端 7f102fc 以 archive/opencode-before-rename 标签保留'
            '（沿用仓库既有 archive/main-before-branch-split 约定），必要时可 push 该标签重建分支。'
        ),
        'expected_result': '裸名与任意形式引用该分支均可正常解析；CI 在新的分支名上转绿。',
        'conditions': [
            'opencode-auto-research 分支名不含精确的 opencode，不受遮蔽影响，故不改名',
            '今后不要新建名为 opencode 的分支（会被同一缓存再次遮蔽）',
        ],
        'verified_result': (
            'git log -1 opencode-main → 78d8445、git rev-parse opencode-main → 78d8445e…（不再有歧义）；'
            '远端分支 codex/main/opencode-auto-research/opencode-main，opencode 已删除；'
            'opencode-main 的 CI run 36394046812 = success（ubuntu 38s / windows 3m16s）。'
        ),
    },
})

# 2) 更新 DEC-028：工作绕过法已不需要，保留为知识
store = open_store(root, heal=True)
rec28 = store.get_record('decision', 'DEC-028')
p28 = dict(rec28['payload'])
p28['status_note'] = (
    '已被 DEC-029 取代：分支改名后本仓库不再有名为 opencode 的分支，'
    '“一律写 refs/heads/opencode”的绕行法在本仓库不再需要。'
    '本条保留为知识：任何仓库只要存在名为 opencode 的分支，就会与该缓存同名冲突。'
)
apply('record.update', {
    'kind': 'decision', 'id': 'DEC-028', 'expected_record_revision': rec28['revision'],
    'status': 'superseded', 'payload': p28,
})

# 3) 任务与证据
apply('task.create', {
    'id': 'TASK-105', 'title': '归档他人未提交内容并把主线分支改名为 opencode-main',
    'goal_id': None,
    'extensions': {
        'authority': 'B', 'kind': 'task', 'phase': 'alignment', 'risk': 'standard',
        'implementer': 'vibe-main (opencode main agent)',
        'inputs': [
            '用户决定：问题1 按推荐方案提交并切换；问题2 选择 A（分支改名）',
            'git 状态：opencode-auto-research 上 4 个未提交文件（另一会话产物）',
        ],
        'done_when': [
            '3 个 docs 改动提交在 opencode-auto-research，AI_INSTALL.md 提交在主线',
            '主工作树切回主线分支且工作区干净',
            '主线分支改名为 opencode-main，远端旧名已退役并有归档标签',
            'opencode-main 上 CI（windows-latest + ubuntu-latest）转绿',
        ],
        'related_business_logic': [],
        'plan': ['按归属提交未提交内容', '切换主工作树', '改名并推送', '退役旧分支名', '观察 CI'],
        'outputs': ['EV-WIN-AUDIT-009'],
    },
})
apply('task.begin', {'task_id': 'TASK-105', 'run_id': 'RUN-116', 'next_action': '记录证据并收口'})

files = ['vibe-coding/AI_INSTALL.md']
hashes = {rel: hashlib.sha256((root / rel).read_bytes()).hexdigest() for rel in files}
apply('evidence.record', {
    'id': 'EV-WIN-AUDIT-009', 'kind': 'integration', 'status': 'valid', 'task_id': 'TASK-105',
    'subject': (
        '主线分支由 opencode 改名为 opencode-main 并验证：旧名末端以 archive/opencode-before-rename 标签保留；'
        'AI_INSTALL.md 的未提交内容已按归属提交到主线（78d8445）；'
        'opencode-auto-research 上的 3 个 docs 改动提交为 97cdf52；'
        'opencode-main 的 CI run 36394046812 = success；改名后裸名歧义消失。'
    ),
    'covers': {'files': files, 'requirements': [], 'tasks': ['TASK-105']},
    'version_binding': {'git_commit': '78d8445', 'diff_hash': None, 'file_hashes': hashes},
})

apply('task.finish', {'task_id': 'TASK-105', 'summary': (
    '按用户决定收口两件事。'
    '①未提交内容按归属归档：docs/auto-research/{00_vision,06_experiment_engine,OPEN_QUESTIONS}.md 三个一行改动'
    '（另一会话执行其 DEC-027 的产物）提交为 97cdf52 于 opencode-auto-research；'
    'AI_INSTALL.md 的 18 行通用安装文档（全局 model 必配、否则后台委派静默失败）随切换带入主线并提交为 78d8445。'
    '实测切换不需要 stash：两分支该文件内容相同，未提交改动自动跟随。'
    '②主线分支改名：opencode → opencode-main（用户选 A），git branch -m + push -u + 删除远端旧名；'
    '旧名末端 7f102fc 以 archive/opencode-before-rename 标签保留（沿用 archive/main-before-branch-split 约定）。'
    '.git/opencode 缓存保持不动以保持插件 project id 不变。'
    '验证：改名后 git log -1 opencode-main / git rev-parse opencode-main 均正常（歧义消失）；'
    'CI run 36394046812 = success（ubuntu-latest 38s、windows-latest 3m16s，API 复核 conclusion/head_sha/head_branch）；'
    '主工作树现位于 opencode-main 且工作区干净；main 分支未触碰。'
    '遗留：docs/auto-research/README.md 第 3 行仍写“从 `opencode` 播种”（历史陈述，属另一会话文档，未擅自改动）。'
)}) 

print('revision', refresh_views(root)['revision'])
