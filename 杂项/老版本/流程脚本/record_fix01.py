import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
CODE = Path(ROOT) / "Transformer-Koopman" / "训练代码"

FILES = [
    "Transformer-Koopman/训练代码/configs/platform2.yaml",
    "Transformer-Koopman/训练代码/scripts/run_all.py",
    "Transformer-Koopman/训练代码/tests/test_pipeline_jobs.py",
    "Transformer-Koopman/训练代码/tests/test_config_contract.py",
]
VB = {"git_commit": None, "diff_hash": None,
      "file_hashes": {f: hashlib.sha256((Path(ROOT) / f).read_bytes()).hexdigest() for f in FILES}}


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
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:180]))


print("== evidence: FIX-01 ==")
apply("evidence.record", {
    "id": "EV-FIX01-001", "kind": "test",
    "subject": "FIX-01 修复：platform2.yaml 补齐 lstm_koopman 段；run_all.py 增加启动前配置预检；新增 tests/test_pipeline_jobs.py 守卫。复现 KeyError: 'lstm_koopman'（lstm_koopman_model.py:31）后修复，8 个任务全部通过预检，套件 137 passed / 2 skipped / 1 xfailed",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES},
    "version_binding": VB}, "t15-ev-fix01", "EV-FIX01-001")

print("\n== alignment ALN-003 -> resolved ==")
import sqlite3
DB = next(Path(ROOT, ".project-log", ".state").rglob("state.sqlite3"))
conn = sqlite3.connect(DB)
row = conn.execute("SELECT revision FROM records WHERE kind='alignment' AND id='ALN-003'").fetchone()
apply("record.update", {"kind": "alignment", "id": "ALN-003",
                        "expected_record_revision": row[0], "status": "resolved"},
      "t15-aln003", "alignment/ALN-003 -> resolved")

print("\nfinal revision:", revision())
