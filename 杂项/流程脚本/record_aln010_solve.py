import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
DB = next(Path(ROOT, ".project-log", ".state").rglob("state.sqlite3"))
C = "Transformer-Koopman/训练代码"

FILES = [
    f"{C}/src/patchtst_koopman/utils/koopman_solve.py",
    f"{C}/src/patchtst_koopman/training/edmd_trainer.py",
    f"{C}/src/patchtst_koopman/training/mlp_koopman_trainer.py",
    f"{C}/src/patchtst_koopman/training/traditional_edmd_trainer.py",
    f"{C}/tests/test_koopman_solve.py",
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
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:240]))


def rec_rev(rid):
    c = sqlite3.connect(DB)
    row = c.execute("SELECT revision FROM records WHERE id=?", (rid,)).fetchone()
    c.close()
    return row[0]


print("== evidence: ALN-010 EDMD-solve part ==")
apply("evidence.record", {
    "id": "EV-ALN010-SOLVE-001", "kind": "test",
    "subject": "ALN-010（EDMD 求解部分）修复：新增 utils/koopman_solve.solve_koopman_operator 作为唯一闭式解实现（用 np.linalg.solve，较 np.linalg.inv 稳健），edmd_trainer / mlp_koopman_trainer / traditional_edmd_trainer 三处全部改为调用它；src/ 中 np.linalg.inv 已归零。新增 tests/test_koopman_solve.py（7 项：与 inv 闭式解数值一致、形状与恢复、病态矩阵下 solve 不劣于 inv、src 无 linalg.inv 守卫、三个 trainer 均导入共享实现）。套件 172 passed / 2 skipped / 1 xfailed；smoke_train PASS、smoke_test 4/4",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES},
    "version_binding": VB}, "t26-ev-aln010solve", "EV-ALN010-SOLVE-001")

print("\n== ALN-010: record partial resolution (stays open) ==")
apply("record.update", {
    "kind": "alignment", "id": "ALN-010",
    "expected_record_revision": rec_rev("ALN-010"),
    "status": "open",
    "payload": {
        "class": "implementation-drift",
        "doc_ref": {"path": ".project-log/docs/business-logic/clarification.yaml",
                    "sha256": "632aa4ffb82e6ceb254107524f4c733535719db92211a7db456be514ee3dac6e"},
        "status_note": "partially-resolved",
        "subject": "重复实现导致多处可独立漂移",
        "resolved_part": "EDMD 闭式解：三处（edmd_trainer / mlp_koopman_trainer / traditional_edmd_trainer）收敛为 utils/koopman_solve.solve_koopman_operator 单一实现，统一采用 np.linalg.solve；src/ 中 np.linalg.inv 归零。守卫 tests/test_koopman_solve.py（EV-ALN010-SOLVE-001）。",
        "residual": "subprocess pipeline 7 处（run_all.py / train_transformer.py / train_platform1.py / train_platform2.py / train_lstm_platforms.py / run_ablation_pipeline.py / run_experiment4_pipeline.py）；PositionalEncoding 3 处（models/patchtst_encoder.py、ablation/positional_encoding.py、deploy/algorithms/tk_assets/transformer_koopman_model.py）；rollout 循环 6+ 处；部署侧整份模型栈副本（需与训练侧数值一致性测试）。",
        "residual_owner": "ALN-010 后续批次（阶段① 继续）",
    }}, "t26-aln010", "ALN-010 payload updated")

print("\nfinal revision:", revision())
