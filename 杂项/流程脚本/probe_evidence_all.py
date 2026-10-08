import sqlite3, json, hashlib
from pathlib import Path

p = r'D:\Project\vibe-coding\.project-log\.state\c15166f6f14948aa85604021638f0b1a\2428c28d612809201bbb0fec8029f394b8ca9a64ea9618cfc5ecc99617f72274\state.sqlite3'
root = Path(r'D:\Project\vibe-coding')
c = sqlite3.connect('file:' + p + '?mode=ro', uri=True)
cols = [r[1] for r in c.execute('pragma table_info(evidence)')]

rows = [dict(zip(cols, r)) for r in c.execute('select * from evidence')]
print('total evidence:', len(rows))
from collections import Counter
print('status counts:', Counter(r['status'] for r in rows))

now_match = 0
now_changed = []
now_missing = []
for r in rows:
    vb = r.get('version_binding') or '{}'
    try:
        vb = json.loads(vb)
    except Exception:
        continue
    fh = vb.get('file_hashes') or {}
    if not fh:
        continue
    verdicts = []
    for f, recorded in fh.items():
        fp = root / f
        if not fp.exists():
            verdicts.append(('missing', f))
            continue
        b = fp.read_bytes()
        cur = hashlib.sha256(b).hexdigest()
        cur_lf = hashlib.sha256(b.replace(b'\r\n', b'\n')).hexdigest()
        if cur == recorded:
            verdicts.append(('match', f))
        elif cur_lf == recorded:
            verdicts.append(('eol-only', f))
        else:
            verdicts.append(('changed', f))
    kinds = {v[0] for v in verdicts}
    if kinds == {'match'} or kinds == {'match', 'eol-only'}:
        now_match += 1
    else:
        detail = [v for v in verdicts if v[0] in ('changed', 'missing')]
        if any(v[0] == 'missing' for v in detail):
            now_missing.append((r['id'], detail))
        else:
            now_changed.append((r['id'], detail))

print('evidence whose covered files are now hash-equal (match or EOL-only):', now_match)
print('evidence with genuinely changed covered file(s):', len(now_changed))
for eid, d in now_changed:
    print('   CHANGED', eid, d)
print('evidence with missing covered file(s):', len(now_missing))
for eid, d in now_missing:
    print('   MISSING', eid, d)
