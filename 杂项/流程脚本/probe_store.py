import json
import sys
from pathlib import Path

sys.path.insert(0, r'C:\Users\12187\.config\opencode\vibe-workflow\scripts')
from state_context import open_store  # noqa: E402

store = open_store(Path(r'D:\Project\vibe-coding'), heal=True)
recs = store.list_records('decision')
print('total decisions:', len(recs))
for r in recs[-2:]:
    print(json.dumps(r, ensure_ascii=False, indent=2)[:900])
    print('---')
