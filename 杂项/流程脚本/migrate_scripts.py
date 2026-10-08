import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman")
CODE = Path(ROOT) / "Transformer-Koopman" / "训练代码"

pairs = []
# top-level runner scripts and docs of the code project
for name in ("run_all_training.bat", "run_all_training.ps1", "README.md"):
    src = OLD / name
    if src.exists():
        pairs.append((src, CODE / name))
# every remaining script (incl. ablation/, experiment4/, debug/) and their yaml
for p in sorted((OLD / "scripts").rglob("*")):
    if p.is_file() and p.suffix in {".py", ".yaml", ".yml"}:
        pairs.append((p, CODE / "scripts" / p.relative_to(OLD / "scripts")))

copied, skipped = 0, []
for src, dst in pairs:
    if dst.exists():
        skipped.append(dst.name)
        continue
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    copied += 1

print(f"copied {copied} files, skipped {len(skipped)} already present: {sorted(set(skipped))[:8]}")

bad = []
for src, dst in pairs:
    if not dst.exists():
        continue
    if hashlib.sha256(src.read_bytes()).hexdigest() != hashlib.sha256(dst.read_bytes()).hexdigest():
        bad.append(str(dst.relative_to(CODE)))
print(f"byte-identity check over {len(pairs)} pairs -> mismatches: {bad if bad else 'NONE'}")

print("\n=== 训练代码 tree (depth 3, code only) ===")
for p in sorted(CODE.rglob("*")):
    rel = p.relative_to(CODE)
    if len(rel.parts) > 3 or "__pycache__" in rel.parts:
        continue
    if p.is_dir():
        print(f"  D {rel}/")
    elif p.suffix in {".py", ".yaml", ".toml", ".txt", ".bat", ".ps1", ".md"}:
        print(f"    {p.stat().st_size:>7} {rel}")


def revision():
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def apply(action, payload, tag, label):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(),
           "action": action, "payload": payload}
    p = f"{TMP}/env_{tag}.json"
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(env, ensure_ascii=False, indent=2))
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", p], capture_output=True)
    ok = r.returncode == 0
    print(f"    {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else r.stderr.decode('utf-8', 'replace')[:150]))


print("\n== refresh TASK-002 next_action (handoff -> resume) ==")
apply("task.handoff", {"task_id": "TASK-002",
                       "next_action": "复现并修复 FIX-01（run_all.py 调度 LSTM x platform2 导致 KeyError），随后 FIX-03/04/05/06/07，批次二 FIX-08/09"},
      "t14-handoff", "task.handoff")
apply("task.resume", {"task_id": "TASK-002",
                      "next_action": "复现并修复 FIX-01（run_all.py 调度 LSTM x platform2 导致 KeyError），随后 FIX-03/04/05/06/07，批次二 FIX-08/09"},
      "t14-resume", "task.resume")

print("\nfinal revision:", revision())
