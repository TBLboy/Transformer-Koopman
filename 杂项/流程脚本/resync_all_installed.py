import hashlib
from pathlib import Path

pairs = [
    (Path(r'D:\Project\vibe-coding\vibe-coding\runtime'), Path(r'C:\Users\12187\.config\opencode\vibe-workflow')),
    (Path(r'D:\Project\vibe-coding\vibe-coding\skills'), Path(r'C:\Users\12187\.config\opencode\skills')),
]
SKIP = {'__pycache__', '.git'}
CRLF = b'\r\n'

normalized = 0
checked = 0
mismatch = []
only_installed = []

for source_root, target_root in pairs:
    for path in sorted(target_root.rglob('*')):
        if path.is_dir():
            continue
        if set(path.relative_to(target_root).parts) & SKIP or path.suffix == '.pyc':
            continue
        data = path.read_bytes()
        if b'\x00' not in data and CRLF in data:
            data = data.replace(CRLF, b'\n')
            path.write_bytes(data)
            normalized += 1
        rel = path.relative_to(target_root)
        src = source_root / rel
        checked += 1
        if not src.is_file():
            only_installed.append(str(rel))
            continue
        if hashlib.sha256(src.read_bytes()).hexdigest() != hashlib.sha256(path.read_bytes()).hexdigest():
            mismatch.append(str(rel))

print('normalized to LF:', normalized)
print('checked:', checked)
print('mismatch vs source (content differs):', len(mismatch))
for m in mismatch:
    print('   MISMATCH', m)
print('installed-only (generated / not in source):', len(only_installed))
for m in only_installed:
    print('   ONLY', m)
