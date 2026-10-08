P = r'C:\Users\12187\AppData\Local\Temp\opencode\fullsuite_audit.log'
raw = open(P, 'rb').read()
try:
    text = raw.decode('utf-8')
except UnicodeDecodeError:
    text = raw.decode('utf-16', errors='replace')
lines = text.splitlines()

signatures = [
    'WinError 1314',
    'required privilege',
    'UnicodeDecodeError',
    'codec can',
    'st_mode',
    '0o111',
    'must be executable',
    'not found in',
    'AssertionError: 2 != 0',
    'AssertionError: 0 == 0',
]
print('=== signature counts ===')
for sig in signatures:
    print('  %-28s %d' % (sig, sum(1 for l in lines if sig in l)))

print()
print('=== class 1: relative-path assertions ===')
for i, l in enumerate(lines):
    if 'AssertionError' in l and 'not found in' in l:
        print('  ', l.strip()[:180])
        if i + 1 < len(lines):
            print('      next:', lines[i + 1].strip()[:180])

print()
print('=== class 3: GBK decode ===')
for i, l in enumerate(lines):
    if 'UnicodeDecodeError' in l:
        print('  ', l.strip()[:200])
        print('      at:', lines[i + 1].strip()[:160] if i + 1 < len(lines) else '')
        break

print()
print('=== class 5: executable bit ===')
for i, l in enumerate(lines):
    if 'st_mode' in l or 'must be executable' in l:
        print('  ', l.strip()[:200])
        print('      at:', lines[i + 1].strip()[:160] if i + 1 < len(lines) else '')
        break

print()
print('=== class 2: symlink errors (first 3) ===')
n = 0
for i, l in enumerate(lines):
    if 'WinError 1314' in l:
        print('  ', l.strip()[:160])
        n += 1
        if n >= 3:
            break

print()
print('=== class 4: rc assertions ===')
for l in lines:
    if 'AssertionError' in l and ('!= 0' in l or '== 0' in l):
        print('  ', l.strip()[:160])
