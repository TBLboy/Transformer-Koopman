import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"


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
    note = "" if ok else " -> " + r.stderr.decode("utf-8", "replace").strip()[:200]
    print(f"  {'OK  ' if ok else 'FAIL'} {label}{note}")


apply("record.create", {
    "kind": "decision", "id": "DEC-010",
    "title": "数据源 = 数据备份/（唯一来源），写适配层转换为 x,u,t,trajectory_id 契约格式", "status": "active",
    "payload": {
        "authority": "C", "user_approval": "approved",
        "decision": "保留 数据备份/ 作为唯一数据来源；不迁移老仓库的已处理 npz。改由适配层把 数据备份/ 中的原始/处理后数据转换为代码契约格式（x, u, t, trajectory_id）。转换产物放在对应硬件平台的 处理后的数据/ 目录下，例如机械臂 -> 数据备份/机械臂数据/处理后的数据/。",
        "safety_override": "为避免覆盖上游文件（软体平台 处理后的数据/ 已存在 train.npz、validation.npz、test.npz，且 schema 不同），契约格式产物写入该目录下的 koopman/ 子目录，文件名用 train.npz/val.npz/test.npz。此调整已生效并在交付说明中标注，用户可要求改为其它命名。",
        "open_question": "机械臂数据的轨迹切分字段与时间字段尚未确定：train_data.mat 字段为 x,y,u,q_dc,q_scaler,u_dc,u_scaler；val_data.mat 为 x_val,y_val,u_val；test_data.mat 为 x_test,u_test；三者均未见 t 或 trajectory_id。软体平台 npz 有 trajectory_id/step_index/time 但键名大写。",
        "rejected_alternative": "迁移老仓库 data/experiment_001 的已处理 npz（契约完全匹配、最快），因用户要求以 数据备份/ 为唯一来源而放弃。",
        "consequence": "适配层的字段语义（y 是否等于 next state、q_dc/q_scaler 的用途、轨迹如何切分）必须由数据本身证实，不得推断；在证实前不得用于产生论文结论数字。"}},
    "t12-dec10", "decision DEC-010")

print("\nfinal revision:", revision())
