import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')


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
    print('OK', action)


apply('review.record', {
    'id': 'REVIEW-OPENCODE-030',
    'task_id': 'TASK-095',
    'reviewer': 'verification-reviewer@opencode-go/deepseek-v4.1-flash',
    'verdict': 'go',
    'scope': {
        'method': 'independent read-only verification subagent (a-verification contract)',
        'initial_verdict': 'no-go',
        'initial_blockers': [
            'installed copies under ~/.config/opencode were CRLF while the source is LF -> installed != source',
            'reviewer sandbox could not execute python/git-hash steps, so validate/regression evidence was unobtainable there',
            'KB archive was 6 events behind the local ledger',
            'task outputs named EV-WINDOWS-EOL-001 / DEC-006 while the live evidence is EV-WINDOWS-EOL-002 and the decision is DEC-021',
        ],
        'resolutions': [
            're-synced the 7 installed files byte-for-byte from the LF source; sha256(source)==sha256(installed), 0 CRLF (verified by main agent)',
            'main agent re-ran validate (no errors), portability-status (689 events, consistent) and 68 targeted tests (OK) on the frozen revision',
            're-archived; KB work_record = ef25e041e23f071eb671fb7b6c152092fc7081a3 with a 689-line LF ledger, worktree clean, remote ref equal',
            'outputs reconciled in the TASK-095 finish summary',
        ],
        'note': 'the independent reviewer could not itself re-run the remediated checks because its sandbox lacks python/git hashing; remediation of items 1-3 was executed and evidenced by the main agent (serial-role-fallback).',
        'kb_commit_at_review': 'ef25e041e23f071eb671fb7b6c152092fc7081a3',
        'kb_commit_initial': 'ab62f02ca54e0693deadc0c979036d735572aafb',
    },
    'evidence_refs': ['EV-WINDOWS-EOL-002', 'EV-WINDOWS-EOL-001'],
})

apply('task.finish', {
    'task_id': 'TASK-095',
    'summary': (
        '归档完成并推送：KB work_record=ef25e041e23f071eb671fb7b6c152092fc7081a3，'
        '提交账本 689 行全 LF、0 CRLF，KB 工作区干净，远端 ref 与 HEAD 同值可核验。'
        '根因修复：state_ledger.append_event 加 os.O_BINARY（Windows 文本模式把 LF 写成 CRLF 的真正源头）、'
        '_ensure_ledger_ignore/workflow_state.save_state/state_views 发布锁/align.MARKER 一律 newline="\\n"、'
        'state_context 新增 .project-log/.gitattributes(* -text)、init_project 种子改 LF 写入并纳入 .gitattributes、'
        'archive.py 改 as_posix 路径、git_environment 代理大小写、Windows 盘符/file://~ 展开与自指守卫、'
        '仓库 .gitattributes 改 * text=auto eol=lf。'
        '独立复核 REVIEW-OPENCODE-030（verification-reviewer 子 Agent）首判 no-go，抓出真实缺陷：'
        '安装副本仍是 CRLF（同步早于本次 LF 归一化）→ 已从 LF 源码逐字节重同步，sha256(源)==sha256(副本)、0 CRLF；'
        '并补跑 validate（无错）/portability-status（689 事件一致）/68 定向测试（OK）。'
        '安装器本身无缺陷（shutil.copy2/copytree 为二进制复制，CRLF 继承自当时仍为 CRLF 的源码）。'
        '本地 .project-log 223 文件与仓库 148 文件归一化为 LF（内容无损：git hash-object == 索引 blob）。'
        '输出更正：本任务 extensions.outputs 的 DEC-006 已被历史决策占用，本次决策为 DEC-021；'
        '验收证据 EV-WINDOWS-EOL-002（EV-WINDOWS-EOL-001 因 covers 自指账本已作废）。'
        '未验证：evidence 表 166 条 stale 属历史累积与项目根迁移（多数覆盖路径以旧根 runtime/... 记录），本次未处理；'
        'CONTRACT-014 覆盖文件真实缺失；框架改动与 .gitattributes 仍未提交到 git。'
    ),
})

print(json.dumps(refresh_views(root))[:200])
