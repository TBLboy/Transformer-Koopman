import hashlib
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')

GUARDED = [
    'vibe-coding/runtime/scripts/validate_project.py',
    'vibe-coding/runtime/scripts/init_project.py',
    'vibe-coding/runtime/scripts/render_subagent_prompt.py',
    'vibe-coding/scripts/global_installer.py',
    'vibe-coding/scripts/opencode_installer.py',
    'vibe-coding/scripts/bootstrap_vibe_python.py',
    'vibe-coding/scripts/generate_cc_switch_config.py',
    'vibe-coding/build_release.py',
    'vibe-coding/skills/a-project-init/scripts/init_project_agents.py',
    'vibe-coding/skills/a-project-log-align/scripts/align.py',
    'vibe-coding/skills/a-project-log-archive/scripts/archive.py',
    'vibe-coding/runtime/hooks/post_tool_use.py',
    'vibe-coding/runtime/hooks/pre_compact.py',
    'vibe-coding/runtime/hooks/session_start.py',
]
TESTS = ['vibe-coding/tests/test_archive_skill.py', 'vibe-coding/tests/test_align_skill.py']
DOCS = ['vibe-coding/README.md', 'vibe-coding/.github/workflows/tests.yml']
COVERS = GUARDED + TESTS + DOCS
HASHES = {rel: hashlib.sha256((root / rel).read_bytes()).hexdigest() for rel in COVERS}


def apply(action, payload):
    store = open_store(root, heal=True)
    receipt = apply_command(root, {
        'schema_version': 1, 'command_id': uuid.uuid4().hex,
        'expected_revision': store.status()['revision'],
        'action': action, 'payload': payload,
    })
    print('OK', action, payload.get('id') or payload.get('task_id'), '->', receipt.get('result'))
    return receipt


apply('task.begin', {'task_id': 'TASK-103', 'run_id': 'RUN-114',
                     'next_action': '记录证据并提交独立复核结论'})

apply('evidence.record', {
    'id': 'EV-WIN-AUDIT-007',
    'kind': 'delivery',
    'subject': (
        'CLI 控制台编码修复：14 个入口在启动时把 stdout/stderr 固定为 UTF-8，'
        '不再依赖平台代码页；CI（windows-latest cp1252 + ubuntu-latest）双双转绿。'
        '本证据同时覆盖 TASK-100/101/102 的当前字节（其原证据因后续守卫改动而 stale）。'
    ),
    'status': 'valid',
    'task_id': 'TASK-103',
    'covers': {'files': COVERS, 'requirements': [],
               'tasks': ['TASK-100', 'TASK-101', 'TASK-102', 'TASK-103']},
    'version_binding': {
        'git_commit': 'dc9db42',
        'diff_hash': None,
        'file_hashes': HASHES,
    },
})

apply('review.record', {
    'id': 'REVIEW-WIN-AUDIT-006',
    'task_id': 'TASK-103',
    'reviewer': 'verification-reviewer (subagent ses_f19405c1affekoscM3Qxe12pW7)',
    'verdict': 'go',
    'scope': {
        'reviewed_evidence': 'EV-WIN-AUDIT-007',
        'method': '读全部 14 个文件确认守卫位置；在 scratch 副本中回滚守卫做反证；核对 GitHub API 的 CI 结论；双环境复跑全量套件',
        'confirmed': [
            '14 个入口的守卫均为 main() 的第一条可执行语句，早于任何 print/json.dumps；模块级无提前输出',
            '反证成立：移除守卫后 archive/align/init_project/generate_cc_switch_config/session_start 均以 cp1252 UnicodeEncodeError 失败，带守卫则成功',
            '无可观测行为变化（仅编码 + 5 个文件补 import sys：pre_compact、session_start、init_project、render_subagent_prompt、generate_cc_switch_config）',
            '两个新回归测试非恒真：子环境确实剔除 PYTHONUTF8（大小写不敏感），移除守卫即失败',
            'CI run 36387388399 conclusion=success，head_sha=01cec84，与 README 实测值一致',
            'archive() 改用 encoding="utf-8" 属正当契约修正（该测试断言 stderr 中的中文子串），非遮蔽',
        ],
        'nuances': [
            'hooks 的 stdout 早已被既有 hook_common 固定为 UTF-8，故新守卫对 hooks 的增量价值是 stderr 与抗重构鲁棒性',
            '守卫未包 try/except（hook_common 包裹了 AttributeError/ValueError）；实际风险低',
            'tests/test_align_skill.py 的 align() 辅助仍按 locale 解码（既有问题，非本次引入）',
            'reviewer 本地复现 skipped=5，未能复现 README 中 skipped=8 一行（其 bash 可用）',
        ],
        'corrections_applied_to_record': [
            'import sys 实为 5 个文件而非 2 个',
            'README 曾漏提交，已补为 dc9db42',
        ],
        'not_verified': ['真实交互式 Windows 控制台（命令均为管道）', 'hooks 的 stderr 中文路径'],
    },
    'evidence_refs': ['EV-WIN-AUDIT-007'],
})

apply('task.finish', {'task_id': 'TASK-103', 'summary': (
    '修复 CI 暴露的控制台编码缺陷（审计 5 类之外的新发现）：CLI 在传统代码页（cp1252/cp936）控制台下'
    '打印非 ASCII 数据即抛 UnicodeEncodeError（CI run 36384167750 windows-latest failures=21）。'
    '在 14 个入口脚本（含用户批准后追加的 init_project、render_subagent_prompt、bootstrap_vibe_python、'
    'build_release、generate_cc_switch_config）的 main() 首条语句统一把 sys.stdout/sys.stderr reconfigure 为 UTF-8，'
    '并用 getattr 容忍被替换的流；5 个文件补 import sys。'
    '新增 2 个可移植回归测试（PYTHONIOENCODING=cp1252 且子环境剔除 PYTHONUTF8 复现旧控制台、断言输出为 UTF-8），'
    '并修正 archive() 辅助为按 UTF-8 解码。反证：移除守卫后 archive/align/init_project/generate_cc_switch_config/'
    'session_start 均复现同一 cp1252 崩溃。'
    '验证：本地不设 PYTHONUTF8（cp936 控制台）与设 PYTHONUTF8 两种环境均 Ran 252 / OK(skipped=8)；'
    'CI run 36387388399 双 job 转绿（windows-latest Ran 252 in 148.5s OK(skipped=2)、ubuntu-latest Ran 252 in 27.5s OK(skipped=2)）；'
    'validate_package 通过。独立复核 REVIEW-WIN-AUDIT-006 = go。'
    '提交：01cec84（14 入口 + 2 测试）、dc9db42（README 平台矩阵与控制台契约）。'
    '证据 EV-WIN-AUDIT-007 同时重覆盖 TASK-100/101/102（其原证据 EV-004 因 01cec84 改动安装器而 stale）。'
    '残余：真实交互式控制台路径未测（均为管道）；hooks 新守卫对 stdout 冗余（既有 hook_common 已固定），增量价值在 stderr 与鲁棒性；'
    'align() 辅助仍按 locale 解码（既有）；守卫未包 try/except。'
)})

print('revision', refresh_views(root)['revision'])
