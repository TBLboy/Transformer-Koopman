import sqlite3, json, hashlib
from pathlib import Path

p = r'D:\Project\vibe-coding\.project-log\.state\c15166f6f14948aa85604021638f0b1a\2428c28d612809201bbb0fec8029f394b8ca9a64ea9618cfc5ecc99617f72274\state.sqlite3'
root = Path(r'D:\Project\vibe-coding')
c = sqlite3.connect('file:' + p + '?mode=ro', uri=True)
cols = [r[1] for r in c.execute('pragma table_info(evidence)')]

CRLF = b'\r\n'
LF = b'\n'

for eid in ('CONTRACT-014', 'DESIGN-012', 'EV-OPENCODE-037'):
    d = dict(zip(cols, c.execute('select * from evidence where id=?', (eid,)).fetchone()))
    print('===', eid, 'status=', d['status'])
    print('  version_binding:', d['version_binding'])
    print('  invalidation_reason:', d.get('invalidation_reason'))
    covers = json.loads(d['covers'])
    for f in covers.get('files', []):
        fp = root / f
        if not fp.exists():
            print('   MISSING', f)
            continue
        b = fp.read_bytes()
        raw = hashlib.sha256(b).hexdigest()
        lf = hashlib.sha256(b.replace(CRLF, LF)).hexdigest()
        print('   file=%s crlf=%d raw=%s lf_normalized=%s' % (f, b.count(CRLF), raw[:20], lf[:20]))
