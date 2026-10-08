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
DOC = ".project-log/docs/business-logic/clarification.yaml"
DOC_SHA = "39de4ac263088864d65c75f27a2df036767bbc9905c3c8da68579d6ffad95349"

NEXT = ("ALN-007（MATLAB 死接口）与 ALN-012（孤儿数据目录）已 resolved。"
        "下一步：ALN-014（中文路径，需用户决策 OQ-001 是否改 ASCII）；"
        "ALN-001/002/015/016/017/018 与 ALN-010 残余属阶段②")

FILES_007 = [
    f"{C}/scripts/encoder_inference_matlab.py",
    f"{C}/tests/test_matlab_adapter.py",
]
VB_007 = {"git_commit": None, "diff_hash": None,
          "file_hashes": {f: hashlib.sha256((Path(ROOT) / f).read_bytes()).hexdigest() for f in FILES_007}}

ALN007_PAYLOAD = {
    "class": "implementation-drift",
    "doc_ref": {"path": DOC, "sha256": DOC_SHA},
    "status_note": "resolved",
    "resolution": (
        "重写 scripts/encoder_inference_matlab.py 的 EncoderInference.__init__，使其读取真实 checkpoint 格式："
        "从 model_state_dict 抽取 encoder.* 前缀键作为编码器权重，从 model_info/config 取 history_length/"
        "state_dim/latent_dim，从 normalization 取 norm_stats；同时保留对旧式 encoder_state_dict 独立 checkpoint 的"
        "兼容分支（显式 if 守卫）。编码器架构优先用 checkpoint 内保存的 config 构建，保证与权重匹配。"
        "新增 tests/test_matlab_adapter.py（4 项：真实 save_model 输出往返、旧式独立 checkpoint 兼容、"
        "缺编码器权重时 KeyError、旧键读取有守卫）。套件 218 passed / 2 skipped / 1 xfailed。证据 EV-ALN007-001。"
    ),
    "subject": "死接口：MATLAB 适配器期望的 checkpoint 格式无人写入",
}

ALN012_PAYLOAD = {
    "class": "unknown",
    "doc_ref": {"path": DOC, "sha256": DOC_SHA},
    "status_note": "resolved",
    "resolution": (
        "逐目录确认用途：experiment_001 = 机械臂平台（x 6 维 / u 3 维），与新仓库 数据备份/机械臂数据/处理后的数据 "
        "逐元素一致（74655/19909/4976）；experiment_002..006 均为软体平台变体（x 2 维 / u 2 维），train 规模分别 "
        "10806/15749/15749/6090/24150，均与新仓库 数据备份/软体平台数据/处理后的数据（21000/6000/3000）不同，"
        "属被取代的软体平台数据迭代。新仓库不含 data/ 目录，experiment_002..005 未迁移（DEC-010：数据源仅 数据备份/），"
        "且新仓库全仓无任何引用。结论：孤儿目录为历史软体平台数据迭代，已由 数据备份/ 取代，不迁移。"
    ),
    "subject": "data/experiment_002..005 四个孤儿数据目录用途不明",
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


print("== evidence EV-ALN007-001 ==")
apply("evidence.record", {
    "id": "EV-ALN007-001", "kind": "test",
    "subject": (
        "ALN-007 修复：MATLAB 适配器改为读取真实 checkpoint 格式。scripts/encoder_inference_matlab.py 原先无条件读 "
        "checkpoint['encoder_state_dict']/['history_length']/['input_dim']/['output_dim']/['norm_stats']，"
        "而 utils/checkpoint.py:save_model 写的是 model_state_dict/config/koopman_A/koopman_B/spectral_radius/"
        "timestamp/model_info/normalization，键集不相交，适配器永远无法加载训练产物。现改为：从 model_state_dict "
        "抽取 encoder.* 前缀键、从 model_info/config 取维度、从 normalization 取 norm_stats，并保留旧式独立 "
        "checkpoint 的显式兼容分支。新增 tests/test_matlab_adapter.py（4 项：真实 save_model 输出往返并逐元素比对 "
        "lift 与 encoder 前向、旧式独立 checkpoint 兼容、缺编码器权重时 KeyError、旧键读取有守卫）。"
        "套件 218 passed / 2 skipped / 1 xfailed。"
    ),
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES_007},
    "version_binding": VB_007}, "t33-ev-aln007", "EV-ALN007-001")

print("\n== evidence EV-ALN012-001 ==")
apply("evidence.record", {
    "id": "EV-ALN012-001", "kind": "analysis",
    "subject": (
        "ALN-012 调查：data/experiment_002..005 孤儿目录用途。逐目录读取 npz 形状：experiment_001 = 机械臂平台"
        "（x 6 维 / u 3 维，74655/19909/4976），与新仓库 数据备份/机械臂数据/处理后的数据 逐元素一致；"
        "experiment_002..006 均为软体平台变体（x 2 维 / u 2 维，train 10806/15749/15749/6090/24150），"
        "均与新仓库 数据备份/软体平台数据/处理后的数据（21000/6000/3000）不同。新仓库无 data/ 目录，"
        "experiment_002..005 未迁移（DEC-010），且新仓库全仓 grep 无引用。结论：历史软体平台数据迭代，已被取代。"
    ),
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": []},
    "version_binding": {"git_commit": None, "diff_hash": None, "file_hashes": {}}},
    "t33-ev-aln012", "EV-ALN012-001")

print("\n== ALN-007 -> resolved ==")
apply("record.update", {"kind": "alignment", "id": "ALN-007",
                        "expected_record_revision": rec_rev("ALN-007"),
                        "status": "resolved", "payload": ALN007_PAYLOAD},
      "t33-aln007", "ALN-007")

print("\n== ALN-012 -> resolved ==")
apply("record.update", {"kind": "alignment", "id": "ALN-012",
                        "expected_record_revision": rec_rev("ALN-012"),
                        "status": "resolved", "payload": ALN012_PAYLOAD},
      "t33-aln012", "ALN-012")

print("\n== refresh next_action ==")
apply("task.handoff", {"task_id": "TASK-002", "next_action": NEXT}, "t33-handoff", "task.handoff")
apply("task.resume", {"task_id": "TASK-002", "next_action": NEXT}, "t33-resume", "task.resume")

print("\nfinal revision:", revision())
