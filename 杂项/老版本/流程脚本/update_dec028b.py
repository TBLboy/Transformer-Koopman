import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')
store = open_store(root, heal=True)
rec = store.get_record('decision', 'DEC-028')
payload = dict(rec['payload'])

payload['root_cause_verified'] = {
    'writer': (
        'opencode 工具链内的 getProjectId()（kdco-primitives 型插件逻辑；本机在 '
        'C:\\Users\\12187\\AppData\\Local\\opencode\\opencode-cli.exe 中命中该逻辑，'
        'npm 版 opencode.exe 中未命中）。已读源码确认：'
        'projectId = `git rev-list --max-parents=0 --all` 排序后的第一个根提交（40 位），'
        '非 git 仓库时回退为 sha256(path)[:16]；结果缓存到 `$GIT_DIR/opencode`，'
        '下次读取时以 /^[a-f0-9]{40}$|^[a-f0-9]{16}$/ 校验后直接复用。'
    ),
    'why_it_shadows': (
        'git 的引用查找顺序第一顺位是 `$GIT_DIR/<name>`，先于 refs/heads/<name>；'
        '因此 `.git/opencode` 一旦存在，裸名 opencode 永远先命中它。'
    ),
    'measured_failures': (
        '裸名取版本号的命令失败：git log -1 opencode / git diff opencode … → fatal: bad object opencode；'
        'git worktree add <path> opencode → 误判为新建分支。'
        '以分支名驱动的命令不受影响：git switch opencode（会打印歧义警告但仍成功）、'
        'git push origin opencode 均实测正常。'
    ),
    'correction_of_earlier_wording': (
        '此前记为「客户端的运行时文件，删除会破坏客户端状态」——过重且不准确。'
        '实测与源码表明它是**纯缓存**，删除后下次调用会重新生成，不影响功能。'
        '但它同时是插件数据的**键**（projectId 用于跨 worktree 的委派存储/状态库），'
        '所以仍建议原地保留：本仓库缓存值 e0a1f460… 已过期（当前根提交为 7fac930 与 3eaff4d，'
        '仓库有两个不相连的根），删除会使 projectId 变更、可能让既有插件数据失联。'
    ),
    'options_verified': [
        'A（根治）改名分支：任何名为 opencode 的分支都会被该缓存遮蔽，改名后冲突永久消失。',
        'B（零改动）保留分支名，涉及该分支一律写全限定 ref refs/heads/opencode。',
        'C（不改名但结构修复）把 .git/opencode 换成同名【目录】：实测裸名立刻恢复解析到分支 '
        '（git log -1 opencode → 正确提交，git rev-parse opencode → 正确 sha）。'
        '代价：该插件写入失败会走 catch 打警告并退回每次重算，属降级而非崩溃——'
        '此结论只对已读源码的那套逻辑成立，未知写入方是否同样容错。',
    ],
    'switch_mechanism_verified': (
        '未提交改动是否阻断切换，取决于该文件在两个分支上内容是否相同：内容相同则原样跟随（不阻断），'
        '只存在于源分支则必须删除（git 拒绝）。实测：提交掉 3 个仅在 auto-research 上的 docs 改动后，'
        '`git switch opencode` 成功且 AI_INSTALL.md 的未提交改动自动跟随，无需 stash。'
    ),
}

payload['conditions'] = [
    c for c in payload.get('conditions', [])
    if '删除会破坏客户端状态' not in c
]

submit = {
    'schema_version': 1, 'command_id': uuid.uuid4().hex,
    'expected_revision': store.status()['revision'],
    'action': 'record.update',
    'payload': {'kind': 'decision', 'id': 'DEC-028',
                'expected_record_revision': rec['revision'], 'payload': payload},
}
apply_command(root, submit)
print('OK record.update DEC-028 (root cause verified)')
print('revision', refresh_views(root)['revision'])
