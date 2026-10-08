import json
import subprocess
import sys
import hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

DOC = Path(ROOT) / ".project-log" / "docs" / "phase2_delta2_passivity_minimal_v0.1.md"
sha = hashlib.sha256(DOC.read_bytes()).hexdigest()

def revision():
    p = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(p.stdout.decode("utf-8", "replace"))["revision"]

def apply(action, payload, tag):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(), "action": action, "payload": payload}
    path = f"{TMP}/env_{tag}.json"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    p = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path], capture_output=True)
    print(("OK   " if p.returncode == 0 else "FAIL ") + tag)
    if p.returncode:
        print(p.stderr.decode("utf-8", "replace")[:1500])

payload = {
    "document": ".project-log/docs/phase2_delta2_passivity_minimal_v0.1.md",
    "document_sha256": sha,
    "hypothesis": "A passivity-preserving lifting with PD inertia and non-vacuous dissipativity margin can be constructed for P1, enabling a passive-controller closed-loop guarantee.",
    "sampling": {"dt_s": 0.004, "rate_hz": 250},
    "constant_M_model": {
        "val_rmse_per_joint": [0.48050584529062645, 0.5630576900275885, 0.3322826731708466],
        "torque_std_per_joint": [0.9186093640786607, 0.9185555670100428, 0.546099734724709],
        "M_eigenvalues": [0.000754657710259067, 0.0014688208905796142, 0.002160583390313845],
        "M_positive_definite": True,
        "M_condition_number": 2.862997834570773,
    },
    "rich_EL_model": {
        "n_blocks": 75,
        "val_rmse_per_joint": [0.34418772994785735, 0.421417469054225, 0.2597745485936561],
        "val_rmse_over_std": [0.3746834545857999, 0.45878277176629156, 0.47569066980889396],
        "approx_R2": [0.8596, 0.7895, 0.7737],
    },
    "verdict": "delta 2 minimal version does NOT pass: PD inertia exists, but EL residual (37-48% of torque std) prevents a non-vacuous passivity margin. Not a mathematical disproof; a data/modeling limitation.",
    "revival_conditions": [
        "separate measurement noise from dynamics and show residual is mostly noise",
        "stronger structural identification (current-torque map, friction, flexibility) to reduce EL residual",
        "show passivity margin numerically exceeds residual bound and yields a NEW closed-loop theorem",
    ],
    "scripts": [
        "C:/Users/12187/AppData/Local/Temp/opencode/spike_p1_passivity.py",
        "C:/Users/12187/AppData/Local/Temp/opencode/spike_p1_passivity_v2.py",
        "C:/Users/12187/AppData/Local/Temp/opencode/p1_dt_noise_check.py",
    ],
}
apply("record.create", {"kind": "research", "id": "PHASE2-DELTA2-PASSIVITY-001", "title": "delta 2 保无源 lifting 可证伪最小版本：未通过", "status": "complete", "payload": payload}, "t56-pass")

next_action = (
    "P1 输入语义=力矩已确认，P1-only 评估完成：主结构被 arXiv:2509.17010 占据，手工结构化 lifting 无收益。"
    "已构造 delta 2（保无源/正定 lifting）可证伪最小版本：P1 可辨识 PD 惯量 M≻0（特征值0.00075/0.00147/0.00216，cond2.86），"
    "但含 M(q)/科氏/库仑摩擦的富 EL 模型仍有 val RMSE≈0.35（相对力矩std 0.37~0.48，R²≈0.77~0.86），"
    "无法得到非空泛无源裕度 → delta 2 最小版本未通过（是数据/建模限制，非数学证伪）。"
    "下一步：要么用噪声分离/更强结构辨识复活 delta 2，要么转 delta 1（有限数据闭环界）或 delta 3（统一界），"
    "要么进入补采数据/缩小论文范围的 C 级决策。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t56-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t56-handoff")
print("doc_sha256:", sha)
print("revision:", revision())
