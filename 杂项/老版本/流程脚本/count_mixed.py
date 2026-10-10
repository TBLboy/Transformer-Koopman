import json
from pathlib import Path

p = Path(r'C:\Users\12187\.config\opencode\.vibe-opencode-installation-state.json')
d = json.loads(p.read_text(encoding='utf-8'))
keys = list(d.get('managed_files', {}))

both = [k for k in keys if '\\' in k and '/' in k]
only_bs = [k for k in keys if '\\' in k and '/' not in k]
only_fs = [k for k in keys if '/' in k and '\\' not in k]
neither = [k for k in keys if '\\' not in k and '/' not in k]

print('total                :', len(keys))
print('has backslash        :', sum(1 for k in keys if '\\' in k))
print('has slash            :', sum(1 for k in keys if '/' in k))
print()
print('MIXED (both)         :', len(both))
print('backslash-only       :', len(only_bs))
print('forward-slash-only   :', len(only_fs))
print('neither separator    :', len(neither))
print('sum check            :', len(both) + len(only_bs) + len(only_fs) + len(neither))
print()
print('the forward-slash-only keys:', only_fs)
print('the no-separator keys      :', neither)
