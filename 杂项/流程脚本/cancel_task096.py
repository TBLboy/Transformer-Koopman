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
    'action': 'task.cancel',
    'payload': {
        'task_id': 'TASK-096',
        'reason': (
            '方案 A 已由用户批准（DEC-024）：保持 evidence 指纹原始字节语义，无需代码改动。'
            '本任务无实现产出，故按无操作取消而非按已实现收口；'
            '其分析结论保留在 DEC-023，若将来选方案 B 可重开。'
        ),
    },
})
print('cancelled; revision', refresh_views(root)['revision'])
