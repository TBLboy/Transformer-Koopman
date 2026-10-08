import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')
store = open_store(root, heal=True)
rec = store.get_record('decision', 'DEC-028')
print('current revision:', rec.get('revision'))
payload = dict(rec['payload'])

# 精确化：把“哪些未提交文件真正阻断切换”从推断改为已实测事实，
# 并补上另一个经实测确认的现象（裸名解析到不存在的对象）。
payload['verified_addendum'] = {
    'verified_at': '2026-09-28',
    'method': '在临时克隆（--branch opencode-auto-research）中重放同一工作树状态，'
              '对 3 个 docs/auto-research/*.md 与 AI_INSTALL.md 各追加一行后执行 `git switch opencode`；'
              '克隆用完即删，真实工作树未受影响。',
    'switch_refusal': (
        '实测被拒，且工作树保持原状（Aborting）：'
        '`error: Your local changes to the following files would be overwritten by checkout:` '
        '仅列出 docs/auto-research/00_vision.md、06_experiment_engine.md、OPEN_QUESTIONS.md 三个文件。'
        'AI_INSTALL.md 虽也被修改但不构成阻断——它在两个分支上内容相同，切换时原样跟随。'
        '（更正：此前“4 个未提交文件都会阻断”的说法不准确。）'
    ),
    'bare_name_resolution': (
        '实测 `git rev-parse opencode` 返回 e0a1f460e521a5864460935431787e5628c6b57a，'
        '而 `git cat-file -t` 对该串报 `bad object`（不在本仓库任何 pack 中），'
        '即裸名解析到的是一个不存在的对象，而非 refs/heads/opencode(7f102fc)。'
        '故裸名不仅“有歧义警告”，而是会解析失败或解析到错误目标。'
    ),
    'worktree_rationale': (
        '选用独立 worktree 而非 stash：worktree 让两个分支同时在不同目录检出，'
        '主工作树与另一会话的未提交改动零接触；stash 需要改动他人未提交内容，pop 冲突会打乱其工作。'
    ),
}
payload['conditions'] = list(payload.get('conditions', [])) + [
    'refs/heads/opencode 的全限定写法同样适用于检出与范围比较；worktree 用全限定 ref 建立时为 detached HEAD，'
    'cherry-pick 后需 switch --force-create opencode 才能把该分支快进过去。',
]

submit = {
    'schema_version': 1,
    'command_id': uuid.uuid4().hex,
    'expected_revision': store.status()['revision'],
    'action': 'record.update',
    'payload': {
        'kind': 'decision', 'id': 'DEC-028',
        'expected_record_revision': rec['revision'],
        'payload': payload,
    },
}
apply_command(root, submit)
print('OK record.update DEC-028')
print('revision', refresh_views(root)['revision'])
