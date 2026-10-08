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


apply('record.create', {
    'kind': 'decision',
    'id': 'DEC-024',
    'title': '证据指纹保持原始字节语义（方案 A）：行尾一致性由结构层保证',
    'status': 'active',
    'payload': {
        'authority': 'C',
        'user_approval': 'approved',
        'statement': (
            '用户批准方案 A：evidence 指纹维持 raw-file 的原始字节语义，不做行尾归一化；'
            '跨平台一致性由 .gitattributes(eol=lf)、.project-log/.gitattributes(-text) 与 LF 归一化在结构层保证。'
        ),
        'rejected_option': '方案 B：记录侧与比较侧统一改为行尾无关',
        'rationale': (
            '单侧归一化会让记录侧与比较侧在 Windows 上不同步（DEC-023 已实测 2 个测试失败）；'
            '结构层已消除框架文件以 CRLF 检出的可能，故无需放宽 raw-file 的精确字节可见性。'
        ),
        'evidence': ['EV-WINDOWS-EOL-002', 'EV-WINDOWS-EOL-003'],
        'related': ['DEC-021', 'DEC-023'],
    },
})

apply('task.begin', {
    'task_id': 'TASK-096',
    'run_id': 'RUN-107',
    'next_action': '方案 A 已批准：无需代码改动，记录决策并关闭任务',
})

apply('task.finish', {
    'task_id': 'TASK-096',
    'summary': (
        '用户在方案 A / 方案 B 之间选择方案 A：保持 evidence 指纹的原始字节语义，不做行尾归一化。'
        '依据 DEC-023 的实测结论（单侧归一化会让记录侧与比较侧在 Windows 上不同步，2 个测试失败），'
        '以及 TASK-095 已在结构层消除 CRLF 检出的可能（仓库 .gitattributes eol=lf、'
        '.project-log/.gitattributes -text、安装器二进制复制、本地与已安装树均已 LF 归一化）。'
        '本次无代码改动，故无实现证据；决策见 DEC-024。'
    ),
})

print('revision', refresh_views(root)['revision'])
