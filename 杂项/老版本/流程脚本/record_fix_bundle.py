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


def hashes(relatives):
    out = {}
    for rel in relatives:
        p = root / rel
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


BASE_COMMIT = 'db7ed85260652292b6b46caade1197ab735b5ee3'
REVIEWER = 'verification-reviewer (subagent ses_f197a5cf2ffe3vRITlp3oLkF92)'
BUNDLE = [
    'vibe-coding/scripts/opencode_installer.py',
    'vibe-coding/tests/test_opencode_installer.py',
    'vibe-coding/tests/test_opencode_plugin.py',
    'vibe-coding/tests/test_opencode_surface.py',
    'vibe-coding/tests/test_cross_platform_surface.py',
    'vibe-coding/tests/_platform.py',
    'vibe-coding/.github/workflows/tests.yml',
    'vibe-coding/README.md',
    '.project-log/docs/windows-test-failure-audit.md',
]
BUNDLE_HASHES = hashes(BUNDLE)

PLAN = [
    # (task, evidence id, evidence files, subject, review id, review scope extras, summary)
    ('TASK-100', 'EV-WIN-AUDIT-004',
     ['vibe-coding/scripts/opencode_installer.py', 'vibe-coding/tests/test_opencode_installer.py'],
     '类别 1 产品缺陷修复：安装状态文件键统一 POSIX + 读时归一化迁移 + 写入强校验（4 个新回归测试）',
     'REVIEW-WIN-AUDIT-003',
     '复核以“把 scripts/opencode_installer.py 回滚到 HEAD 后新测试即 FAIL/ERROR”证明 4 个新测试是真实回归测试；'
     '确认无残留 str(relative_to()) 造键、新装状态文件 0 反斜杠键、迁移无伪冲突、写前守卫会拒绝反斜杠//空键。',
     '修复安装器状态文件键归一化（类别 1 产品缺陷）。'
     'surface_assets/runtime_assets 造键改用 .as_posix()；新增 canonical_relative() 统一“分隔符归一化 + 安全校验”，'
     'destination_for/validate_state_shape 改走它；read_state 经 heal_state 归一化历史反斜杠键（旧状态可无损迁移，不报伪冲突），'
     '并在升级时打印 “Normalized N legacy path key(s)”；写盘前加 assert_canonical_state() 强校验（反斜杠、a//b、空键一律响亮失败）。'
     '回归：新增 test_installation_state_keys_are_posix / test_legacy_backslash_state_keys_are_migrated / '
     'test_non_posix_state_key_is_refused_before_write / test_heal_state_normalizes_legacy_keys。'
     '原 3 个失败用例（test_fresh_install_verify_and_uninstall、test_local_skill_modification_is_preserved、'
     'test_runtime_local_modification_is_preserved_on_update）已通过；全量 failures 8→5，无新增回归。'
     '残余：canonical_relative 在所有平台替换反斜杠，理论上会误解析“文件名里真的含反斜杠”的 POSIX 路径（契约已声明键为 POSIX 相对路径，故可接受）。'),
    ('TASK-101', 'EV-WIN-AUDIT-005',
     ['vibe-coding/tests/_platform.py', 'vibe-coding/tests/test_opencode_installer.py',
      'vibe-coding/tests/test_opencode_plugin.py', 'vibe-coding/tests/test_opencode_surface.py',
      'vibe-coding/tests/test_cross_platform_surface.py'],
     '类别 2-5 测试平台适配：新增 tests/_platform.py，Windows 全量套件 failures=0/errors=0',
     'REVIEW-WIN-AUDIT-004',
     '逐条判定 8 个 skip 均为真实能力缺口（4 symlink 特权 + 1 bash + 2 cross-platform bash + 1 既存 0.3.0 归档件）；'
     '确认“无断言被削弱”：plugin 侧的 @skipUnless(PLUGIN_PACKAGE.is_file()) 被移除（覆盖反而增强），'
     'file:// 断言改用 url2pathname（Windows 下更严格），可执行位断言在 POSIX 上仍执行；'
     '确认移除对宿主全局 ~/.config/opencode/node_modules 的 symlink 属正当解耦，替代的仓库内 @opencode-ai/plugin 垫片行为等价。',
     '按报告建议引入 tests/_platform.py（can_symlink / skip_unless_symlink / posix_only / make_package_manager_shim / '
     'usable_posix_bash / make_opencode_ai_node_modules），逐类改造被指认调用点：'
     '类别 2 四个 symlink 用例加 @skip_unless_symlink；'
     '类别 3 该用例改用 usable_posix_bash() 探测（WSL 存根下跳过）并补 encoding="utf-8"；'
     '类别 4 全部 8 处假包管理器改用 make_package_manager_shim（Windows 用 .cmd 启动器），使“失败回滚”用例真正走到非零退出路径'
     '（此前在本机被真 npm 抢先解析，assertNotEqual 看到 0）；'
     '类别 5 可执行位断言改为 POSIX 条件，文件存在性断言全平台保留。'
     '同时移除对宿主全局 node_modules 的强耦合，并暴露/修复两个此前在 Windows 从未执行到的测试缺陷'
     '（node:os homedir() 忽略 HOME 需补 USERPROFILE；裸 "opencode" 需经 shutil.which 解析为 opencode.CMD）。'
     '实测：Windows 全量 Ran 250 tests / OK（0 failures, 0 errors；skipped 随宿主 5-8）。'
     '残余：POSIX 分支（垫片 shebang、chmod、可执行位断言）本机无法执行，仅靠代码审读与 ubuntu-latest CI 配置保证；'
     'Windows 具备符号链接特权时的 pass 路径未实测；posix_only 已提供但当前未被使用（类别 5 只需单条断言条件化）。'),
    ('TASK-102', 'EV-WIN-AUDIT-006',
     ['vibe-coding/.github/workflows/tests.yml', 'vibe-coding/README.md'],
     '新增 Windows/Ubuntu CI 工作流并把平台支持矩阵与已知限制写入 README',
     'REVIEW-WIN-AUDIT-005',
     '确认工作流在 ubuntu-latest 与 windows-latest 上运行与本地实测完全相同的两条命令、解释器版本显式声明为 3.11；'
     '按复核意见修正 README 中“skipped=8”的宿主相关性（明确 5-8 范围及原因）；'
     '确认平台矩阵三条限制（symlink 特权 / WSL bash 存根 / POSIX 权限位）与实测一致；'
     '本地复跑 validate_package 通过、YAML 解析正确。CI 本身尚未在 GitHub 上真实执行。',
     '新增 .github/workflows/tests.yml：矩阵 ubuntu-latest + windows-latest、Python 3.11，'
     '步骤 = 安装 runtime/scripts/requirements.txt → validate_package.py --root . → '
     'python -m unittest discover -s tests -p "test_*.py"（与 README“回归套件”命令逐字一致）。'
     'README「平台范围」由“Windows 延期”改为实测矩阵（Windows Ran 250 / OK，skipped 随宿主 5-8），'
     '并列出三条已知平台限制与安装状态文件的 POSIX 键契约。'
     '本地留痕：validate_package = “Package validation passed.”(exit 0)；全量套件 Ran 250 / OK。'
     '残余：CI 从未在 GitHub 上真实触发（未推送），仅本地复跑同款命令。'),
]

for task, ev_id, ev_files, subject, rev_id, rev_scope, summary in PLAN:
    apply('task.begin', {'task_id': task, 'run_id': f'RUN-{111 + ["TASK-100","TASK-101","TASK-102"].index(task)}',
                         'next_action': '记录证据并提交独立复核结论'})
    apply('evidence.record', {
        'id': ev_id, 'kind': 'audit', 'subject': subject, 'status': 'valid', 'task_id': task,
        'covers': {'files': ev_files, 'requirements': [], 'tasks': [task]},
        'version_binding': {'git_commit': BASE_COMMIT, 'diff_hash': None,
                            'file_hashes': {rel: BUNDLE_HASHES[rel] for rel in ev_files}},
    })
    apply('review.record', {
        'id': rev_id, 'task_id': task, 'reviewer': REVIEWER, 'verdict': 'go',
        'scope': {
            'reviewed_evidence': ev_id,
            'review_pass': '同一次综合独立复核（覆盖 TASK-100/101/102）',
            'method': '审读完整 git diff、自行复跑全量套件与工作流同款命令、在临时副本中回滚安装器以检验回归测试真伪',
            'verdict_basis': rev_scope,
            'reviewer_full_suite': 'Ran 250 tests in 143.512s / OK (skipped=5) — 与实现方 skipped=8 的差异源于 bash 解析（git-bash 可用则该 3 例执行）',
            'not_verified': ['POSIX 侧执行（本机无第二个平台）', 'Windows 具备符号链接特权时的 pass 路径',
                             'CI 在 GitHub 上真实触发'],
        },
        'evidence_refs': [ev_id],
    })
    apply('task.finish', {'task_id': task, 'summary': summary})

print('revision', refresh_views(root)['revision'])
