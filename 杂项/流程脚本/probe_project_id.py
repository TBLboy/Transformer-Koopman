"""检查 opencode 数据目录里是否存在以缓存 project id 命名的存储目录。"""
import os
from pathlib import Path

PROJECT_ID = 'e0a1f460e521a5864460935431787e5628c6b57a'
HOME = Path(os.path.expanduser('~'))
DIRS = [
    Path(os.environ.get('LOCALAPPDATA', '')) / 'opencode',
    Path(os.environ.get('APPDATA', '')) / 'opencode',
    HOME / '.local' / 'share' / 'opencode',
    HOME / '.opencode',
]

for d in DIRS:
    if not d.exists():
        print(f'(missing) {d}')
        continue
    print(f'--- {d}')
    for child in sorted(d.iterdir())[:10]:
        print(f'    {"DIR " if child.is_dir() else "FILE"} {child.name}')
    # 找以该 id 命名的目录
    try:
        for p in d.rglob('*'):
            if p.is_dir() and (p.name == PROJECT_ID or p.name.startswith(PROJECT_ID[:8])):
                print(f'    *** MATCH: {p}')
    except Exception as exc:
        print('    rglob error:', exc)
    proj = d / 'project'
    if proj.is_dir():
        print(f'    project/ entries: {[c.name for c in sorted(proj.iterdir())[:10]]}')

# 另找 opencode 的 storage 根
for base in [HOME / '.local' / 'share', Path(os.environ.get('LOCALAPPDATA', ''))]:
    for cand in ['opencode', 'opencode-cli']:
        p = base / cand
        if p.exists():
            print(f'EXISTS {p}')
