import json
import os
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

PY = r'D:\conda\envs\vibe-coding\python.exe'
REPO = Path(r'D:\Project\vibe-coding\vibe-coding')

FILES = [
    'runtime/scripts/validate_project.py',
    'scripts/global_installer.py',
    'scripts/opencode_installer.py',
    'skills/a-project-init/scripts/init_project_agents.py',
    'skills/a-project-log-align/scripts/align.py',
    'skills/a-project-log-archive/scripts/archive.py',
    'runtime/hooks/post_tool_use.py',
    'runtime/hooks/pre_compact.py',
    'runtime/hooks/session_start.py',
    'runtime/scripts/init_project.py',
    'runtime/scripts/render_subagent_prompt.py',
    'scripts/bootstrap_vibe_python.py',
    'build_release.py',
    'scripts/generate_cc_switch_config.py',
]

print('=== 1. compile all 14 ===')
bad = []
for rel in FILES:
    try:
        py_compile.compile(str(REPO / rel), doraise=True)
    except py_compile.PyCompileError as exc:
        bad.append((rel, str(exc).splitlines()[0]))
print('compiled OK:', len(FILES) - len(bad), '/', len(FILES))
for rel, err in bad:
    print('  FAILED', rel, err)

# A child environment that reproduces a legacy Windows console on any platform.
child_env = {k: v for k, v in os.environ.items() if k.upper() != 'PYTHONUTF8'}
child_env['PYTHONIOENCODING'] = 'cp1252'


def run(label, argv, expect_zero=True):
    result = subprocess.run([PY, *argv], cwd=str(REPO), env=child_env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = result.stdout + result.stderr
    crashed = b'UnicodeEncodeError' in out
    try:
        out.decode('utf-8')
        utf8 = True
    except UnicodeDecodeError:
        utf8 = False
    flag = 'OK ' if (not crashed and (not expect_zero or result.returncode == 0)) else 'BAD'
    print(f'  [{flag}] {label}: rc={result.returncode} unicode_crash={crashed} utf8_decodable={utf8}')
    return result


with tempfile.TemporaryDirectory() as tmp:
    cjk = Path(tmp) / '工程记录测试'
    cjk.mkdir()
    print()
    print('=== 2. new entry points under PYTHONIOENCODING=cp1252 (no PYTHONUTF8) ===')
    run('init_project.py --dry-run (CJK target)', ['runtime/scripts/init_project.py', '--target', str(cjk), '--dry-run'])
    run('render_subagent_prompt.py (CJK context)',
        ['runtime/scripts/render_subagent_prompt.py', '--role', 'business-analyst',
         '--project-root', str(cjk), '--task', '中文任务描述', '--scope', '只读'])
    run('generate_cc_switch_config.py', ['scripts/generate_cc_switch_config.py', '--root', '.'])
    run('bootstrap_vibe_python.py --help', ['scripts/bootstrap_vibe_python.py', '--help'])

    print()
    print('=== 3. guards reachable in all 14 ===')
    missing = []
    for rel in FILES:
        if 'reconfigure(encoding="utf-8")' not in (REPO / rel).read_text(encoding='utf-8'):
            missing.append(rel)
    print('files with the guard:', len(FILES) - len(missing), '/', len(FILES))
    for rel in missing:
        print('  MISSING', rel)
