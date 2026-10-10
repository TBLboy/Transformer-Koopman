import hashlib
import shutil
from pathlib import Path

pairs = [
    (r'D:\Project\vibe-coding\vibe-coding\runtime\scripts\state_context.py',
     r'C:\Users\12187\.config\opencode\vibe-workflow\scripts\state_context.py'),
    (r'D:\Project\vibe-coding\vibe-coding\runtime\scripts\init_project.py',
     r'C:\Users\12187\.config\opencode\vibe-workflow\scripts\init_project.py'),
    (r'D:\Project\vibe-coding\vibe-coding\runtime\scripts\state_ledger.py',
     r'C:\Users\12187\.config\opencode\vibe-workflow\scripts\state_ledger.py'),
    (r'D:\Project\vibe-coding\vibe-coding\runtime\scripts\workflow_state.py',
     r'C:\Users\12187\.config\opencode\vibe-workflow\scripts\workflow_state.py'),
    (r'D:\Project\vibe-coding\vibe-coding\runtime\scripts\state_views.py',
     r'C:\Users\12187\.config\opencode\vibe-workflow\scripts\state_views.py'),
    (r'D:\Project\vibe-coding\vibe-coding\skills\a-project-log-archive\scripts\archive.py',
     r'C:\Users\12187\.config\opencode\skills\a-project-log-archive\scripts\archive.py'),
    (r'D:\Project\vibe-coding\vibe-coding\skills\a-project-log-align\scripts\align.py',
     r'C:\Users\12187\.config\opencode\skills\a-project-log-align\scripts\align.py'),
]

backup = Path(r'C:\Users\12187\AppData\Local\Temp\opencode\installed-backup2')
backup.mkdir(parents=True, exist_ok=True)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

for source, target in pairs:
    src, dst = Path(source), Path(target)
    (backup / dst.name).write_bytes(dst.read_bytes())   # pre-change backup
    shutil.copy2(src, dst)                              # byte-exact copy
    sb, db = src.read_bytes(), dst.read_bytes()
    print('%-16s src_crlf=%d dst_crlf=%d same=%s' % (
        dst.name, sb.count(b'\r\n'), db.count(b'\r\n'), sha(src) == sha(dst)))
