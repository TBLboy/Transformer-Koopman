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

FILES = [
    "Transformer-Koopman/训练代码/src/patchtst_koopman/models/mlp_koopman_model.py",
    "Transformer-Koopman/训练代码/src/patchtst_koopman/models/lstm_koopman_model.py",
    "Transformer-Koopman/训练代码/src/patchtst_koopman/training/performance.py",
    "Transformer-Koopman/训练代码/scripts/ablation/train_ablation.py",
    "Transformer-Koopman/训练代码/scripts/experiment4/train_experiment4.py",
    "Transformer-Koopman/训练代码/tests/test_config_immutability.py",
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
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:300]))


print("== re-record ALN-011 evidence (supersedes EV-ALN011-001) ==")
apply("evidence.record", {
    "id": "EV-ALN011-002", "kind": "test",
    "subject": (
        "ALN-011 修复复核（重录，取代 EV-ALN011-001）：MLPKoopmanModel/LSTMKoopmanModel 的 _patch_config "
        "改为 _patched_config（deepcopy 后打补丁）；apply_gpu_training_defaults 返回副本并同步两个调用方。"
        "本次 ALN-010 rollout 去重改动了 mlp/lstm 两个模型文件（移除重复的 predict_multi_step/get_koopman_matrices、"
        "改继承 KoopmanRolloutMixin），使 EV-ALN011-001 因绑定文件哈希变化而 stale；_patched_config 逻辑未变，"
        "tests/test_config_immutability.py 仍全绿（套件 216 passed / 2 skipped / 1 xfailed）。"
    ),
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES},
    "version_binding": VB}, "t29-ev-aln011b", "EV-ALN011-002")

print("\nfinal revision:", revision())
