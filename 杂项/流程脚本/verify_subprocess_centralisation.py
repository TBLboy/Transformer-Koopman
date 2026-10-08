import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码")
SCRIPTS = ROOT / "scripts"

TARGETS = [
    "run_all.py",
    "train_transformer.py",
    "train_platform1.py",
    "train_platform2.py",
    "train_lstm_platforms.py",
    "ablation/run_ablation_pipeline.py",
    "experiment4/run_experiment4_pipeline.py",
]

# 1) shared module importable + API present
sys.path.insert(0, str(ROOT / "src"))
from patchtst_koopman.utils import subprocess_runner as sr  # noqa: E402

print("shared module:", sr.__file__)
for fn in ("run_streaming", "run_capture"):
    print(f"  has {fn}: {callable(getattr(sr, fn, None))}")

# 2) per-file static audit
print()
print(f"{'file':<42} {'imports shared':<15} {'raw Popen':<10} {'raw run':<8}")
print("-" * 78)
ok = True
for rel in TARGETS:
    p = SCRIPTS / rel
    src = p.read_text(encoding="utf-8-sig")
    tree = ast.parse(src)

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "patchtst_koopman.utils.subprocess_runner":
            imported |= {a.name for a in node.names}

    raw_popen = sum(
        1
        for n in ast.walk(tree)
        if isinstance(n, ast.Attribute)
        and n.attr == "Popen"
        and isinstance(n.value, ast.Name)
        and n.value.id == "subprocess"
    )
    raw_run = sum(
        1
        for n in ast.walk(tree)
        if isinstance(n, ast.Attribute)
        and n.attr == "run"
        and isinstance(n.value, ast.Name)
        and n.value.id == "subprocess"
    )

    good = bool(imported) and raw_popen == 0 and raw_run == 0
    ok = ok and good
    print(f"{rel:<42} {str(sorted(imported)):<15} {raw_popen:<10} {raw_run:<8}")

print()
print("ALL CENTRALISED" if ok else "PROBLEM FOUND")
sys.exit(0 if ok else 1)
