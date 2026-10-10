import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')

store = open_store(root, heal=True)
apply_command(root, {
    'schema_version': 1, 'command_id': uuid.uuid4().hex,
    'expected_revision': store.status()['revision'],
    'action': 'record.create',
    'payload': {
        'kind': 'decision',
        'id': 'DEC-028',
        'title': '分支名 opencode 与 .git/opencode 冲突，git 操作一律用全限定 ref',
        'status': 'active',
        'payload': {
            'authority': 'B',
            'category': 'tooling',
            'context': (
                'vibe-coding 仓库的顶层存在 .git/opencode 文件（由 opencode 客户端自身写入，非 git 对象）。'
                '它与分支 opencode 同名，导致 `git rev-parse opencode` 报 '
                '"warning: refname \'opencode\' is ambiguous"，并使 '
                '`git worktree add <path> opencode` 误判为新建分支而失败（fatal: a branch named \'opencode\' already exists），'
                '`git log opencode..<branch>` 亦直接报 fatal: Invalid revision range。'
                '本项在 TASK-104 合入主分支时实际发生并中断了第一次执行。'
            ),
            'decision': (
                '涉及该分支的 git 命令一律使用全限定 ref：`refs/heads/opencode`（远程为 `origin/opencode`）。'
                '不要使用裸名 `opencode`，也不要删除 .git/opencode（它是客户端的运行时文件，删除会破坏客户端状态）。'
            ),
            'conditions': [
                '仅在需要解析该分支的引用时适用；`git push origin opencode` 这类以 refspec 形式给出的写法仍正常',
                '若未来把该分支改名或客户端不再写 .git/opencode，本条可作废',
            ],
            'expected_result': (
                '后续会话不再因裸名 opencode 的歧义而中断：worktree 创建、范围比较、rev-parse 均可直接工作。'
            ),
            'action': (
                '新建 worktree：`git -C <repo> worktree add <path> refs/heads/opencode`（注意会以 detached HEAD 建立，'
                'cherry-pick 后再 `git switch --force-create opencode` 快进该分支）；'
                '范围比较：`git log refs/heads/opencode..refs/heads/<other>`。'
            ),
        },
    },
})
print('OK record.create DEC-025')
print('revision', refresh_views(root)['revision'])

