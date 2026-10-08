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
    f"{C}/src/patchtst_koopman/models/rollout.py",
    f"{C}/src/patchtst_koopman/models/full_model.py",
    f"{C}/src/patchtst_koopman/models/mlp_koopman_model.py",
    f"{C}/src/patchtst_koopman/models/lstm_koopman_model.py",
    f"{C}/src/patchtst_koopman/ablation/models.py",
    f"{C}/src/patchtst_koopman/utils/evaluation.py",
    f"{C}/tests/test_rollout_consistency.py",
]
VB = {"git_commit": None, "diff_hash": None,
      "file_hashes": {f: hashlib.sha256((Path(ROOT) / f).read_bytes()).hexdigest() for f in FILES}}

NEXT = ("ALN-010 四部分（EDMD 闭式解 / PositionalEncoding / subprocess pipeline / rollout）已完成，"
        "ALN-010 仍 partially-resolved（余部署侧模型栈副本一致性测试，属阶段②/后续）。"
        "下一步：FIX-05..07（ALN-005/007/012/014/015/016/017/018/019 中未处理者），批次二 FIX-08/09")

ALN010_PAYLOAD = {
    "class": "implementation-drift",
    "doc_ref": {
        "path": ".project-log/docs/business-logic/clarification.yaml",
        "sha256": "632aa4ffb82e6ceb254107524f4c733535719db92211a7db456be514ee3dac6e",
    },
    "residual": [
        "部署侧模型栈副本（PositionalEncoding 已对齐，但其余类缺一致性测试）",
    ],
    "residual_owner": "ALN-010 后续批次（阶段② 或后续）",
    "resolved_part": [
        "EDMD 闭式解：收敛为 utils/koopman_solve.solve_koopman_operator（EV-ALN010-SOLVE-001）",
        "PositionalEncoding：收敛为 utils/positional_encoding.PositionalEncoding，部署副本改为跟随 torch.get_default_dtype()，新增数值一致性测试（EV-ALN010-POSENC-001）",
        "subprocess pipeline：7 处（run_all / train_transformer / train_platform1 / train_platform2 / train_lstm_platforms / run_ablation_pipeline / run_experiment4_pipeline）收敛为 utils/subprocess_runner（run_streaming / run_capture），scripts/ 下无裸 subprocess.Popen/run，新增 tests/test_subprocess_centralisation.py（EV-ALN010-SUBPROC-001）",
        "rollout：模型侧 5 处重复（PatchTST/MLP/LSTM/Ablation 的 predict_multi_step + get_koopman_matrices，以及 full_model 私有 roll_out_latent）收敛为 models/rollout.KoopmanRolloutMixin；utils/evaluation.iterative_prediction 改为委托 predict_multi_step；新增 tests/test_rollout_consistency.py（EV-ALN010-ROLLOUT-001）",
    ],
    "status_note": "partially-resolved",
    "subject": "重复实现导致多处可独立漂移",
}


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
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:300]))


def rec_rev(rid):
    c = sqlite3.connect(DB)
    row = c.execute("SELECT revision FROM records WHERE id=?", (rid,)).fetchone()
    c.close()
    return row[0]


print("== evidence: ALN-010 rollout ==")
apply("evidence.record", {
    "id": "EV-ALN010-ROLLOUT-001", "kind": "test",
    "subject": (
        "ALN-010 第四部分：rollout 去重。模型侧 5 处重复收敛为 models/rollout.KoopmanRolloutMixin"
        "（predict_multi_step / roll_out_latent / get_koopman_matrices），PatchTSTKoopmanModel、"
        "MLPKoopmanModel、LSTMKoopmanModel、ablation.AblationModel 均改为继承该 mixin；"
        "utils/evaluation.iterative_prediction 原先自带一份 encode→koopman→decode→滑窗 循环，"
        "现改为委托 model.predict_multi_step（保留 AMP 与 numpy 返回语义）；"
        "顺带移除 4 个模型文件中不再使用的 import torch。新增 tests/test_rollout_consistency.py"
        "（16 项：4 个类共享同一函数对象、stub 上 predict_multi_step/roll_out_latent/get_koopman_matrices "
        "的解析行为、真实模型与 ablation 工厂的 rollout 形状、iterative_prediction 与 predict_multi_step 数值一致）。"
        "套件 216 passed / 2 skipped / 1 xfailed；smoke_train PASS；smoke_test 4/4。"
    ),
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES},
    "version_binding": VB}, "t29-ev-aln010rollout", "EV-ALN010-ROLLOUT-001")

print("\n== ALN-010 payload update ==")
apply("record.update", {"kind": "alignment", "id": "ALN-010",
                        "expected_record_revision": rec_rev("ALN-010"),
                        "status": "open", "payload": ALN010_PAYLOAD},
      "t29-aln010", "ALN-010 payload")

print("\n== refresh next_action ==")
apply("task.handoff", {"task_id": "TASK-002", "next_action": NEXT}, "t29-handoff", "task.handoff")
apply("task.resume", {"task_id": "TASK-002", "next_action": NEXT}, "t29-resume", "task.resume")

print("\nfinal revision:", revision())
