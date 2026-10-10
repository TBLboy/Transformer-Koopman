import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')


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


COMMON = {
    'authority': 'B',
    'kind': 'task',
    'phase': 'implementation',
    'risk': 'strict',
    'implementer': 'vibe-main + implementation-builder (delegated)',
    'inputs': [
        'EV-WIN-AUDIT-003',
        '.project-log/docs/windows-test-failure-audit.md',
        '用户 C 级决策：修类别 1 + 类别 2-5 测试适配 + Windows CI 与平台矩阵声明',
    ],
    'related_business_logic': [],
}

apply('task.create', {
    'id': 'TASK-100',
    'title': '修复安装器状态文件键归一化（类别 1 产品缺陷）并补写入强校验与旧状态迁移',
    'goal_id': None,
    'extensions': dict(COMMON, done_when=[
        'surface_assets/runtime_assets 造键统一为 POSIX（.as_posix()），不再依赖 os.sep',
        'plan_sync 入口对 previous 键规范化，使含反斜杠键的既有状态文件可无损迁移且不产生伪冲突',
        '写入状态文件前强制校验所有键为 POSIX 规范形式（回归时响亮失败）',
        '读取旧状态时接受并归一化历史反斜杠键（healing），validate 不再因旧键而拒绝',
        '三个失败用例在 Windows 上转为通过：test_fresh_install_verify_and_uninstall / test_local_skill_modification_is_preserved / test_runtime_local_modification_is_preserved_on_update',
        '实装后新状态文件 managed_files 中反斜杠键数为 0',
        '定向测试 + 相邻行为回归通过，且 Linux 语义未被破坏（键在 POSIX 上本就合法）',
    ], plan=[
        '新增 canonical_relative() 统一“分隔符归一化 + 安全校验”',
        '造键处改用 .as_posix()',
        'plan_sync 归一化 previous 键',
        'read_state 归一化旧键；写前断言规范形式',
        '定向测试 + 全量套件回归',
    ], outputs=['EV-WIN-AUDIT-004']),
})

apply('task.create', {
    'id': 'TASK-101',
    'title': 'Windows 平台测试适配：引入 tests/_platform.py 修复类别 2-5',
    'goal_id': None,
    'extensions': dict(COMMON, done_when=[
        '新增 tests/_platform.py：can_symlink()、posix_only/skip_unless_symlink 装饰器、make_package_manager_shim()、usable_posix_bash()',
        '类别 2：无 symlink 特权时相关用例跳过（skip）而非 error',
        '类别 3：用例复用 usable_posix_bash() 探测 bash 并显式 encoding="utf-8"；WSL 存根环境下跳过而非解码失败',
        '类别 4：假 npm/bun shim 在 Windows 上以 .cmd 构造，且“失败回滚”用例必须真正走到失败路径（不得静默成功）',
        '类别 5：可执行位断言改为平台条件断言（Windows 不断言 POSIX 权限位）',
        'test_cross_platform_surface.py 改为复用 _platform.usable_posix_bash() 且仍然通过',
        'Windows 全量套件 failures=0 errors=0（skip 允许）',
        '临时目录不在仓库内、用例不依赖本机全局 ~/.config/opencode 路径',
    ], plan=[
        '引入 tests/_platform.py 平台工具',
        '逐类改造被指认的调用点',
        '消除对本机全局路径的强耦合（test_opencode_plugin/test_opencode_surface 的 symlink 目标）',
        'Windows 全量套件复跑至 0 failures / 0 errors',
    ], outputs=['EV-WIN-AUDIT-005']),
})

apply('task.create', {
    'id': 'TASK-102',
    'title': '新增 CI（windows-latest + ubuntu-latest）并声明平台支持矩阵',
    'goal_id': None,
    'extensions': dict(COMMON, done_when=[
        '新增 .github/workflows/tests.yml，在 windows-latest 与 ubuntu-latest 上运行全量 unittest',
        '工作流不使用未固定的大版本号之外的隐式假设；解释器版本显式声明（3.11+）',
        '平台支持矩阵与已知限制（symlink 特权、bash/WSL 存根、可执行位）写入仓库文档',
        '本地按工作流同款命令复跑通过，命令与结果留痕',
    ], plan=[
        '编写 workflow（矩阵 ubuntu/windows，Python 3.11）',
        '文档补平台矩阵与限制说明',
        '本地同款命令复跑验证',
    ], outputs=['EV-WIN-AUDIT-006']),
})

print('revision', refresh_views(root)['revision'])
