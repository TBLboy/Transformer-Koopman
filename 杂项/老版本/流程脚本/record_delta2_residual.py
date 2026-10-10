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

DOC = Path(ROOT) / ".project-log" / "docs" / "phase2_delta2_residual_structure_v0.1.md"
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
    "document": ".project-log/docs/phase2_delta2_residual_structure_v0.1.md",
    "document_sha256": sha,
    "lag1_autocorrelation": {"joint1": 0.6532438824412483, "joint2": 0.5912642597595695, "joint3": 0.5573769500797434},
    "corr_with_acc": {"joint1": 0.0209, "joint2": 0.0032, "joint3": -0.0011},
    "corr_with_dq": {"joint1": 0.2709, "joint2": 0.1717, "joint3": 0.1844},
    "verdict": "EL residual is structured (high lag-1 autocorrelation ~0.56-0.65), not white noise. delta 2 cannot be revived by noise separation; requires stronger structural identification.",
    "implication": "delta 1 (finite-data closed-loop bound) and delta 3 (unified bound) would be dominated by the same structured residual and yield vacuous bounds unless the residual is modeled.",
    "script": "C:/Users/12187/AppData/Local/Temp/opencode/p1_residual_structure.py",
}
apply("record.create", {"kind": "research", "id": "PHASE2-DELTA2-RESIDUAL-001", "title": "delta 2 残差结构：结构化未建模动力学，不能靠噪声分离复活", "status": "complete", "payload": payload}, "t57-res")

next_action = (
    "P1 输入=力矩；P1-only 主线被 arXiv:2509.17010 占据。delta 2（保无源 lifting）可证伪最小版本未通过："
    "P1 可辨识 PD 惯量 M≻0，但富 EL 模型残差 val RMSE≈0.35（相对力矩std 0.37~0.48，R²≈0.77~0.86）。"
    "残差结构分析：滞后1自相关 0.56~0.65（非白噪声），与加速度≈0、与速度弱相关 → 残差是结构化未建模动力学，不能靠噪声分离复活，需更强结构辨识。"
    "由此 delta 1（有限数据闭环界）与 delta 3（统一界）也会被同一残差支配而空泛。"
    "当前无候选通过硬门槛。建议进入 C 级决策：补采数据 vs 缩小论文范围（P1-only/P2-only 增量）vs 投入更强结构辨识。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t57-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t57-handoff")
print("doc_sha256:", sha)
print("revision:", revision())
