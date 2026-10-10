import hashlib
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import apply_command, open_store, refresh_views  # noqa: E402

root = Path(r'D:\Project\vibe-coding')
repo = root / 'vibe-coding'
installed = [Path(r'C:\Users\12187\.config\opencode\vibe-workflow'),
             Path(r'C:\Users\12187\.config\opencode\skills')]
SKIP = {'__pycache__', '.git'}


def apply(action, payload):
    store = open_store(root, heal=True)
    envelope = {
        'schema_version': 1, 'command_id': uuid.uuid4().hex,
        'expected_revision': store.status()['revision'],
        'action': action, 'payload': payload,
    }
    apply_command(root, envelope)
    print('OK', action, payload.get('id') or payload.get('task_id'))


head = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                      capture_output=True, text=True).stdout.strip()

# every installed runtime/skill file, bound by absolute path
bound = {}
for tree in installed:
    for path in sorted(tree.rglob('*')):
        if path.is_dir() or path.suffix == '.pyc':
            continue
        if set(path.relative_to(tree).parts) & SKIP:
            continue
        bound[path.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()

apply('evidence.record', {
    'id': 'EV-WINDOWS-EOL-003',
    'kind': 'verification',
    'subject': 'Installed OpenCode runtime and skills are LF and content-identical to the framework source',
    'status': 'valid',
    'task_id': 'TASK-095',
    'covers': {'files': sorted(bound), 'requirements': [], 'tasks': ['TASK-095']},
    'version_binding': {
        'git_commit': head, 'diff_hash': None, 'file_hashes': bound,
    },
})

apply('record.create', {
    'kind': 'decision',
    'id': 'DEC-023',
    'title': '证据指纹保持原始字节语义；跨平台行尾一致性在结构层保证，不做单侧行尾归一化',
    'status': 'active',
    'payload': {
        'authority': 'B',
        'statement': (
            '已评估"让 evidence 指纹行尾无关"（让 _covered_digest / doc_ref 比较 CRLF→LF 归一化）。'
            '若只改比较侧，会与记录侧（state-fingerprint 默认 raw-file、调用方自算 sha256）在 Windows 上不同步；'
            '实测该改法使 test_changed_covered_file_makes_evidence_stale 与 '
            'test_changed_doc_ref_propagates_into_task_and_goal_gates 失败：记录侧按 CRLF 存哈希、比较侧按 LF 归一化 → 立刻判 stale。'
            '要让两侧一致，须同时改提供侧默认选择器、doc_ref 生成侧、全量测试的确定性行尾写入与文档，属于会放宽 raw-file'
            '“精确字节可见”契约的语义变更，需单独立项。'
        ),
        'decision': (
            '保持指纹的原始字节语义不变；跨平台一致性改由结构层保证：'
            '仓库 .gitattributes(* text=auto eol=lf) + .project-log/.gitattributes(* -text) + 安装器二进制复制 + 现有 LF 归一化。'
        ),
        'rationale': (
            '结构层已消除"框架文件以 CRLF 检出"的可能（仓库 148 文件 0 CRLF；已安装 85 文件与源码逐字节一致），'
            '故 raw-file 的行尾敏感在本项目内不再产生误判；而放宽比较侧会削弱逐字节归档所依赖的精确字节可见性。'
        ),
        'evidence': ['EV-WINDOWS-EOL-002', 'EV-WINDOWS-EOL-003'],
    },
})

apply('task.create', {
    'id': 'TASK-096',
    'title': '统一证据指纹在记录侧与比较侧的行尾语义（待用户决策）',
    'goal_id': None,
    'extensions': {
        'authority': 'C',
        'kind': 'task',
        'phase': 'solution-research',
        'risk': 'high',
        'depends_on': ['TASK-095'],
        'done_when': [
            '明确 evidence 指纹是否应行尾无关（C 级语义选择，需用户批准）',
            '若采用：提供侧默认选择器、doc_ref 生成侧、比较侧与全套件测试的行尾写入一并改为同一 helper',
            '若采用：更新 docs/USAGE.md 与 state_evidence 的选择器契约说明',
            '全量回归通过且无新的跨平台脆弱点',
        ],
        'related_business_logic': [],
        'inputs': [],
        'plan': [
            '分析：单侧归一化会在 Windows 上使记录侧与比较侧不同步（已由 2 个失败测试证明）',
            '方案 A（保持现状）：结构层 .gitattributes/LF 归一化保证一致，raw-file 语义不变',
            '方案 B（C 级）：引入 artifact_digest 单一 helper，两侧与测试同步改为行尾无关，放宽 raw-file 行尾可见性',
        ],
        'outputs': [],
    },
})

apply('task.wait', {
    'task_id': 'TASK-096',
    'kind': 'user-decision',
    'reason': '证据指纹是否改为行尾无关属于语义选择；单侧改动已被证明会破坏记录侧/比较侧一致性',
    'resume_when': '用户就其选择方案 A（保持原始字节语义）或方案 B（统一改为行尾无关）给出决定',
})

print(refresh_views(root)['revision'])
