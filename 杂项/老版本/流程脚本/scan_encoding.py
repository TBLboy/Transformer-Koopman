import re
from pathlib import Path

repo = Path(r'D:\Project\vibe-coding\vibe-coding')
rows = []
for base in ('runtime/scripts', 'scripts', 'skills', 'runtime/hooks', 'plugins'):
    d = repo / base
    if not d.is_dir():
        continue
    for f in sorted(d.rglob('*.py')):
        text = f.read_text(encoding='utf-8')
        nonascii_literal = any(ord(c) > 127 for c in text)
        prints = 'print(' in text
        ensure_false = 'ensure_ascii=False' in text
        guard = 'reconfigure' in text or 'PYTHONIOENCODING' in text
        entry = '__main__' in text or 'def main(' in text
        if entry and prints and (nonascii_literal or ensure_false):
            rows.append({
                'file': str(f.relative_to(repo)).replace('\\', '/'),
                'nonascii': nonascii_literal,
                'ensure_false': ensure_false,
                'guard': guard,
            })

print('CLI scripts that print and can emit non-ASCII:')
for r in rows:
    tags = []
    if r['nonascii']:
        tags.append('zh-literal')
    if r['ensure_false']:
        tags.append('ensure_ascii=False')
    tags.append('GUARDED' if r['guard'] else 'NO-GUARD')
    print('  %-62s %s' % (r['file'], ','.join(tags)))
print()
print('total:', len(rows), '| without guard:', sum(1 for r in rows if not r['guard']))
