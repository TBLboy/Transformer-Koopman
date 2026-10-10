import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

PAYLOAD = {
    "decision": "阶段顺序：① 整理代码（当前阶段）→ ② 理论方法讨论 → ③ 重训与结果更新",
    "decided_by": "user",
    "user_statement": "重训是肯定的，但是不是现在。我们先整理好代码，之后会做理论方法的讨论，之后才正式开始重训。",
    "implications": [
        "本阶段目标 = 把代码整理成干净、可验证、可重训的结构；不产出论文数字",
        "多步损失的 lambda 取值（含 multi_step_physical=10.0）与 N_L 属阶段② 理论方法讨论议题，现在不得视为已冻结或已验证的超参",
        "成功条件中涉及重训结果与论文数字的部分归属阶段③，不作为本阶段验收依据",
        "平台统一 5 项损失的结构性结论仍然有效（论文 eq:pretraining_loss 已定义），只是具体权重待阶段②定"
    ],
    "effect_on_DEC003": "DEC-003 的结构性结论（双平台统一 5 项损失）保持有效；其数值部分（10.0 / inferred 0.5 / N_L=3）标记为 provisional，待阶段② 理论讨论重新确认",
    "validation_plan": "有界对比（lambda_multi_x in {1.0, 10.0}）推迟到阶段②结束时执行，作为理论结论的实证起点"
}


def revision() -> int:
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


envelope = {
    "schema_version": 1,
    "command_id": "t011-dec004",
    "expected_revision": revision(),
    "action": "record.create",
    "payload": {
        "kind": "decision",
        "id": "DEC-004",
        "title": "阶段顺序：代码整理 -> 理论方法讨论 -> 重训（重训不在本阶段）",
        "status": "active",
        "payload": PAYLOAD,
    },
}
path = f"{TMP}/env_t011_dec004.json"
open(path, "w", encoding="utf-8", newline="\n").write(
    json.dumps(envelope, ensure_ascii=False, indent=2)
)
print("payload bytes:", len(json.dumps(PAYLOAD, ensure_ascii=False).encode("utf-8")))
r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path],
                   capture_output=True)
print("rc:", r.returncode)
if r.returncode == 0:
    print("DEC-004 recorded -> revision", revision())
else:
    print("STDERR:", r.stderr.decode("utf-8", "replace"))
