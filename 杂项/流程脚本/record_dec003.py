import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

PAYLOAD = {
    "decision": "双平台统一使用论文 eq:pretraining_loss 的 5 项 Stage-1 损失；多步物理损失权重按老提案取 10x",
    "decided_by": "user",
    "authority": "论文 eq:pretraining_loss（红字新增，定义 5 项且保留 L_c）为唯一权威损失定义",
    "loss_vector_confirmed_by_user": {
        "multi_step_physical": 10.0,
        "note": "用户选择 C：采用老提案的高权重 10x"
    },
    "loss_vector_inferred_by_agent": {
        "prediction": 1.0,
        "latent": 0.5,
        "consistency": 0.5,
        "multi_step_latent": 0.5,
        "horizon_N_L": 3,
        "why": "沿用 platform1.yaml 中已被真实训练跑过的值；提案只规定多步物理权重，未规定多步 latent 与 N_L",
        "status": "inferred - 待用户纠正"
    },
    "blast_radius": [
        "platform1 与 platform2 都必须重训（platform1 的 0.157 不再适用）",
        "消融实验须整体重跑：platform1 19 变体 + platform2 18 变体",
        "论文配图与表格须重新生成",
        "部署资产须重新导出（4 个基线控制器）",
        "论文结果表中的数字须整体更新"
    ],
    "risk": [
        "10x 权重作用在 L_multi = sum_{i=1..N_L} ||.||^2 上，N_L=3 时有效量级约为单步损失的 30 倍，梯度尺度可能压过单步项",
        "10x 从未被任何实验验证过（老提案只是引用他文做法）",
        "论文正文无需改动（lambda 写作非负超参数、N_L 未写死），但结果相关性需重新建立"
    ],
    "validation_plan": "先做有界对比（platform2、固定小 epoch、multi_step_physical in {1.0, 10.0}）确认 10x 不导致训练失稳或收敛劣化，再投入全面重训",
    "supersedes": "老 .project-log 的 Q-20260605-004（状态由 待用户确认 转为 已决策）",
    "traceability_gap": "论文 Platform1 的 0.157 是否来自当前 platform1.yaml（5 项、N_L=3）尚无证据，需用 results/ 或重训绑定"
}


def revision() -> int:
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


envelope = {
    "schema_version": 1,
    "command_id": "t010-dec003",
    "expected_revision": revision(),
    "action": "record.create",
    "payload": {
        "kind": "decision",
        "id": "DEC-003",
        "title": "双平台统一 5 项损失，多步物理权重取 10x（用户决策 C）",
        "status": "active",
        "payload": PAYLOAD,
    },
}
path = f"{TMP}/env_t010_dec003.json"
open(path, "w", encoding="utf-8", newline="\n").write(
    json.dumps(envelope, ensure_ascii=False, indent=2)
)
print("payload bytes:", len(json.dumps(PAYLOAD, ensure_ascii=False).encode("utf-8")))
r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path],
                   capture_output=True)
out = r.stdout.decode("utf-8", "replace").strip()
err = r.stderr.decode("utf-8", "replace").strip()
print("rc:", r.returncode)
if r.returncode == 0:
    print("DEC-003 recorded -> revision", revision())
else:
    print("STDERR:", err)
