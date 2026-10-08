import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

SCRIPTS = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\scripts")

# file -> set of import lines to drop
PLAN = {
    "run_all.py": {"import subprocess", "import time"},
    "train_transformer.py": {"import subprocess", "import time"},
    "train_platform1.py": {"import subprocess", "import time"},
    "train_platform2.py": {"import subprocess", "import time"},
    "train_lstm_platforms.py": {"import subprocess"},
}

for name, drops in PLAN.items():
    p = SCRIPTS / name
    lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    kept, removed = [], []
    for ln in lines:
        if ln.strip() in drops:
            removed.append(ln.strip())
            continue
        kept.append(ln)
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.writelines(kept)
    print(f"{name}: removed {sorted(removed)}")
