import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

def rev():
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]

def apply(action, payload, tag):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": rev(), "action": action, "payload": payload}
    p = f"{TMP}/env_{tag}.json"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", p], capture_output=True)
    print(("OK   " if r.returncode == 0 else "FAIL ") + tag)
    if r.returncode:
        print(r.stderr.decode("utf-8", "replace")[:1200])
    return r.returncode

payload = {
    "status": "complete",
    "documents": [
        ".project-log/docs/phase2_route_reset_v0.1.md",
        ".project-log/docs/phase2_psr_audit_v0.1.md",
    ],
    "reset": {
        "old_route": "Transformer history lifting + constant (A,B) Koopman + B† feedforward + LQR; T1′ proof repair is baseline only, not innovation.",
        "new_gate": "Both modeling parameterization/identification objective and controller structure must change; no generic wrapper or proof-only contribution.",
    },
    "psr_audit": {
        "train_val_test_trajectories": [70, 20, 10],
        "trajectory_length": 300,
        "dt": "~0.2s",
        "unique_action_vectors": 30000,
        "integer_exact_fraction": 0.0,
        "max_distance_to_integer": 0.4999979,
        "repeated_prefixes_h1_h2_h3": {"h1": 0, "h2": 0, "h3": 0},
        "verdict": "kill offline discrete-action PSR / integer pulse planning for current data: no action-prefix support and continuous floating logs.",
        "script": "C:/Users/12187/AppData/Local/Temp/opencode/audit_p2_psr.py",
    },
    "bilinear_spike": {
        "script": "C:/Users/12187/AppData/Local/Temp/opencode/spike_p2_bilinear.py",
        "affine_val_rmse": 0.11611185576589274,
        "bilinear_val_rmse": 0.1160477869936142,
        "affine_val_mae": 0.09402716723388588,
        "bilinear_val_mae": 0.09406242634453521,
        "verdict": "no meaningful evidence that first-order state-input bilinear terms improve P2 generalization; retain only as low-priority fallback, not route.",
    },
    "literature": {
        "input_operator_family": "Haseli/Mezic/Cortes CDC 2025 DOI 10.1109/cdc57313.2025.11312881; generic operator families are active prior art.",
        "koopman_feedback_linearization": "Gadginmath/Krishnan/Pasqualetti TAC 2024 DOI 10.1109/tac.2024.3417188; direct data-driven feedback linearization already exists.",
        "lpv_koopman_control": "Cisneros et al. IFAC 2020 DOI 10.1016/j.ifacol.2020.12.1676; Chen et al. CDC 2024 DOI 10.1109/cdc56724.2024.10886066; generic LPV/operator route crowded.",
    },
    "current_verdict": "No theory route is selected. Old T1′ route is baseline; PSR is killed on current data support; bilinear is not supported by minimal spike. Continue exploration with a new requirement: a controller-structure change must be justified by a data-identifiable mechanism, not only literature composition.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-RESET-002", "title": "阶段② 重启：旧路线降级、PSR 数据否证、bilinear spike 无收益", "status": "complete", "payload": payload}, "t52-reset")
next_action = (
    "用户已否定旧路线的创新性，已重置：T1′/量化/有效域只作纠错基线。P2 PSR/离散 pulse planning 因 action support 失败淘汰（30000 action 全唯一、h=1/2/3 prefix 重复均为0、浮点非整数）。"
    "P2 affine vs 一阶 bilinear 最小 spike：val RMSE 0.116112 vs 0.116048，几乎无收益，bilinear 不升格路线。文献检索显示 operator family/LPV/Koopman feedback-linearization 已有直接先例。"
    "当前无选定理论路线；下一步必须寻找能被现有连续数据识别、且真正改变控制器结构的候选，否则应明确要求补采数据/调整论文范围。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t52-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t52-handoff")
print("revision:", rev())
