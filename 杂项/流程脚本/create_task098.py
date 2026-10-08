import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')


def apply(action, payload):
    store = open_store(root, heal=True)
    apply_command(root, {
        'schema_version': 1, 'command_id': uuid.uuid4().hex,
        'expected_revision': store.status()['revision'],
        'action': action, 'payload': payload,
    })
    print('OK', action, payload.get('id') or payload.get('task_id'))


apply('task.create', {
    'id': 'TASK-098',
    'title': '核查 Windows 平台测试失败报告（5 类 21 项）并记录结论',
    'goal_id': None,
    'extensions': {
        'authority': 'B',
        'kind': 'task',
        'phase': 'verification',
        'risk': 'standard',
        'implementer': 'vibe-main (opencode main agent, serial-role-fallback)',
        'inputs': ['外部 agent 提交的 Windows 平台测试失败报告（5 类根因、21 项失败）'],
        'done_when': [
            '逐条判定报告 5 类根因的真实性：产品代码 bug / 测试不兼容 / 不成立',
            '每条结论附代码位置或实跑输出作为证据',
            '复现总数与报告一致（246 tests / 8 failures / 13 errors / 3 skipped）或说明差异',
            '核实“产品 bug”这一类是否真的存在于对外契约（安装状态文件）',
            '记录未验证项与建议的后续动作',
        ],
        'related_business_logic': [],
        'plan': [
            '读取被指认的代码位置（installer 相对路径、symlink 调用点、subprocess encoding、shim、可执行位断言）',
            '实跑目标测试抓住原始报错，与报告描述逐条比对',
            '实跑全量套件确认计数与分类分布',
            '输出核查结论并归档',
        ],
        'outputs': ['EV-WIN-AUDIT-001'],
    },
})

apply('task.begin', {
    'task_id': 'TASK-098',
    'run_id': 'RUN-109',
    'next_action': '逐条核查报告结论并抓取代码/实跑证据',
})

print('revision', refresh_views(root)['revision'])
