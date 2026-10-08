import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

CODE = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码")

TARGETS = [
    "scripts/run_all.py",
    "scripts/train_transformer.py",
    "scripts/train_platform1.py",
    "scripts/train_platform2.py",
    "scripts/train_lstm_platforms.py",
    "scripts/ablation/run_ablation_pipeline.py",
    "scripts/experiment4/run_experiment4_pipeline.py",
]

print("=== existence / size ===")
for rel in TARGETS:
    p = CODE / rel
    print(f"  {'OK     ' if p.is_file() else 'MISSING'} {rel}" + (f"  ({p.stat().st_size} B)" if p.is_file() else ""))

print()
print("=== subprocess / Popen / run / check_call usage ===")
PAT = re.compile(r"subprocess\.|Popen|check_call|check_output|\.run\(|sys\.executable|PYTHON_EXE|python_exe")
for rel in TARGETS:
    p = CODE / rel
    if not p.is_file():
        continue
    hits = []
    for lineno, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if PAT.search(line):
            hits.append((lineno, line.strip()))
    print(f"  --- {rel}  ({len(hits)} hits)")
    for lineno, line in hits[:14]:
        print(f"      {lineno}: {line[:120]}")
    if len(hits) > 14:
        print(f"      ... (+{len(hits) - 14} more)")
