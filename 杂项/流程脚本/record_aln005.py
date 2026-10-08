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
    f"{C}/configs/platform1.yaml",
    f"{C}/configs/platform2.yaml",
    f"{C}/tests/test_config_contract.py",
]
VB = {"git_commit": None, "diff_hash": None,
      "file_hashes": {f: hashlib.sha256((Path(ROOT) / f).read_bytes()).hexdigest() for f in FILES}}

NEXT = ("ALN-005 已 resolved（删除两平台配置中的死键，KNOWN_UNREAD 清空）。"
        "下一步：FIX-05..07（ALN-007/012/014/015/016/017/018/019 中未处理者），批次二 FIX-08/09")

DEC_PAYLOAD = {
    "decision": "删除两平台 YAML 中声明但从不被读取的死键（而非保留/注释/接线）",
    "rationale": (
        "ALN-005 记录 17 组死键（controller/evaluation/logging 整段 + data/encoder/koopman/decoder/"
        "training 若干），仓库级扫描另发现 mlp_koopman/lstm_koopman 的 optimizer 键，共 35 个死叶/平台。"
        "用户明确选择'删除死键'。接线（让键生效）属阶段② 理论方法讨论范围，本阶段不引入行为变更。"
    ),
    "alternatives": [
        "保留并注释为'未接线'——保留误导性配置，否决",
        "接线使其生效——改变训练行为，属阶段②，本阶段否决",
    ],
    "consequences": [
        "platform1.yaml / platform2.yaml 顶层仅剩 experiment/data/encoder/koopman/training/mlp_koopman/lstm_koopman",
        "tests/test_config_contract.py 的 KNOWN_UNREAD 清空为空集，任何新死键将直接使套件失败",
        "REQUIRED_PATHS 移除 koopman.enforce_stability；源码扫描范围扩展到 src/+scripts/+deploy/，避免误报脚本读取的键",
        "保留 experiment.log_dir（scripts/train_patchtst.py 读取）、experiment.name（experiment4 写入）、koopman.rho_max（koopman_dynamics/edmd_trainer 读取）",
    ],
    "level": "B",
    "decided_by": "user",
}

ALN005_PAYLOAD = {
    "class": "implementation-drift",
    "doc_ref": {
        "path": ".project-log/docs/business-logic/clarification.yaml",
        "sha256": hashlib.sha256(
            Path(ROOT, ".project-log/docs/business-logic/clarification.yaml").read_bytes()
        ).hexdigest(),
    },
    "status_note": "resolved",
    "resolution": (
        "用户选择删除死键（DEC-012）。两平台 YAML 共删除 35 个死叶/平台：controller/evaluation/logging "
        "整段，data.add_noise/noise_level/noise_type/normalization_method，encoder.positional_encoding，"
        "koopman.enforce_stability/model_type，decoder.decoder_type，training.val_every_n_epochs/"
        "save_every_n_epochs/save_best_only，training.edmd.pretrain.optimizer，"
        "training.edmd.compute.batch_encode，training.end_to_end.optimizer，以及 mlp_koopman/lstm_koopman "
        "的 edmd.pretrain.optimizer 与 end_to_end.optimizer。"
        "tests/test_config_contract.py 的 KNOWN_UNREAD 清空为空集（新死键将直接失败），"
        "REQUIRED_PATHS 移除 koopman.enforce_stability，源码扫描扩展到 src/+scripts/+deploy/。"
        "保留 experiment.log_dir / experiment.name / koopman.rho_max（均被读取或写入）。"
        "证据 EV-ALN005-001。"
    ),
    "subject": "YAML 声明但从不被读取的键（controller/evaluation/logging 整段）",
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
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:400]))


def rec_rev(rid):
    c = sqlite3.connect(DB)
    row = c.execute("SELECT revision FROM records WHERE id=?", (rid,)).fetchone()
    c.close()
    return row[0]


print("== decision DEC-012 ==")
apply("record.create", {"kind": "decision", "id": "DEC-012",
                        "title": "ALN-005：删除两平台配置中的死键（用户决策 B）",
                        "status": "active", "payload": DEC_PAYLOAD},
      "t30-dec012", "DEC-012")

print("\n== evidence EV-ALN005-001 ==")
apply("evidence.record", {
    "id": "EV-ALN005-001", "kind": "test",
    "subject": (
        "ALN-005 修复：删除两平台 YAML 中声明但从不被读取的死键。platform1.yaml / platform2.yaml "
        "各删除 35 个死叶（controller/evaluation/logging 整段；data.add_noise/noise_level/noise_type/"
        "normalization_method；encoder.positional_encoding；koopman.enforce_stability/model_type；"
        "decoder.decoder_type；training.val_every_n_epochs/save_every_n_epochs/save_best_only；"
        "training.edmd.pretrain.optimizer；training.edmd.compute.batch_encode；training.end_to_end.optimizer；"
        "mlp_koopman/lstm_koopman 的 edmd.pretrain.optimizer 与 end_to_end.optimizer）。"
        "tests/test_config_contract.py：KNOWN_UNREAD 清空为空集、REQUIRED_PATHS 移除 koopman.enforce_stability、"
        "源码扫描范围扩展到 src/+scripts/+deploy/。验证：两平台 YAML 解析后死键残留 0；"
        "test_config_contract.py 67 passed / 1 xfailed；完整套件 214 passed / 2 skipped / 1 xfailed"
        "（较 216 少 2 项 = 移除的 koopman.enforce_stability × 2 平台参数化）；"
        "smoke_train.py PASS（rho=0.999753）；smoke_test.py 4/4。"
    ),
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES},
    "version_binding": VB}, "t30-ev-aln005", "EV-ALN005-001")

print("\n== ALN-005 -> resolved ==")
apply("record.update", {"kind": "alignment", "id": "ALN-005",
                        "expected_record_revision": rec_rev("ALN-005"),
                        "status": "resolved", "payload": ALN005_PAYLOAD},
      "t30-aln005", "ALN-005")

print("\n== refresh next_action ==")
apply("task.handoff", {"task_id": "TASK-002", "next_action": NEXT}, "t30-handoff", "task.handoff")
apply("task.resume", {"task_id": "TASK-002", "next_action": NEXT}, "t30-resume", "task.resume")

print("\nfinal revision:", revision())
