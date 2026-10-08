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
    f"{C}/src/patchtst_koopman/utils/positional_encoding.py",
    f"{C}/src/patchtst_koopman/models/patchtst_encoder.py",
    f"{C}/src/patchtst_koopman/ablation/positional_encoding.py",
    f"{C}/deploy/algorithms/tk_assets/transformer_koopman_model.py",
    f"{C}/tests/test_positional_encoding_consistency.py",
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


print("== evidence: ALN-010 PositionalEncoding part ==")
apply("evidence.record", {
    "id": "EV-ALN010-POSENC-001", "kind": "test",
    "subject": "ALN-010（PositionalEncoding 部分）修复：新增 utils/positional_encoding.PositionalEncoding 为唯一权威实现；models/patchtst_encoder.py 删除自带副本改为导入；ablation/positional_encoding.py 改为向后兼容重导出（6 个消融编码器无需改动）；部署副本 deploy/.../transformer_koopman_model.py 的 dtype 处理由硬编码 torch.float 改为 torch.get_default_dtype()，消除与训练侧的数值分歧。新增 tests/test_positional_encoding_consistency.py（6 项：三处同一类对象、src 仅一处类定义、部署副本与权威实现逐元素相等、float64 默认 dtype 下仍一致）。套件 178 passed / 2 skipped / 1 xfailed；smoke_train PASS、smoke_test 4/4、ablation 重导出为同一对象",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES},
    "version_binding": VB}, "t27-ev-aln010posenc", "EV-ALN010-POSENC-001")

print("\n== ALN-010: update partial resolution ==")
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
        "resolved_part": [
            "EDMD 闭式解：三处收敛为 utils/koopman_solve.solve_koopman_operator（EV-ALN010-SOLVE-001）。",
            "PositionalEncoding：三处收敛为 utils/positional_encoding.PositionalEncoding；部署副本改为跟随 torch.get_default_dtype() 并有数值一致性测试（EV-ALN010-POSENC-001）。",
        ],
        "residual": [
            "subprocess pipeline 7 处（run_all.py / train_transformer.py / train_platform1.py / train_platform2.py / train_lstm_platforms.py / run_ablation_pipeline.py / run_experiment4_pipeline.py）。",
            "rollout 循环 6+ 处。",
            "部署侧整份模型栈副本（PositionalEncoding 已对齐，其余类仍需一致性测试）。",
        ],
        "residual_owner": "ALN-010 后续批次（阶段① 继续）",
    }}, "t27-aln010", "ALN-010 payload updated")

print("\nfinal revision:", revision())
