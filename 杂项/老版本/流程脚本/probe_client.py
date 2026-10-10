"""在 opencode 客户端二进制里搜索 .git/opencode 的用法，判断它是否会被读回。"""
import re
from pathlib import Path

EXES = [
    Path(r'C:\Users\12187\AppData\Roaming\npm\node_modules\opencode-ai\node_modules\opencode-windows-x64\bin\opencode.exe'),
    Path(r'C:\Users\12187\AppData\Roaming\npm\node_modules\opencode-ai\node_modules\opencode-windows-x64-baseline\bin\opencode.exe'),
]

PATTERNS = [b'.git/opencode', b'.git\\opencode', b'git", "opencode', b'shadow', b'Snapshot']

for exe in EXES:
    if not exe.exists():
        print('missing:', exe)
        continue
    data = exe.read_bytes()
    print('=' * 70)
    print(exe.name, f'({len(data):,} bytes)')
    for pat in PATTERNS:
        n = data.count(pat)
        print(f'  {pat!r}: {n} hit(s)')
    # 提取含 "opencode" 且前面 60 字节内含 "git" 的上下文片段
    hits = set()
    for m in re.finditer(re.escape(b'opencode'), data):
        s = max(0, m.start() - 90)
        ctx = data[s:m.end() + 60]
        if b'.git' in ctx or b'git ' in ctx or b'git"' in ctx:
            hits.add(ctx.decode('utf-8', 'replace'))
    print(f'  ---- {len(hits)} unique git-ish contexts mentioning "opencode" ----')
    for h in sorted(hits)[:14]:
        print('   |', h.replace('\n', ' ')[:170])
