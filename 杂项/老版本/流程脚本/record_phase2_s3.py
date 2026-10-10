import json
import subprocess
import sys

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
    path = f"{TMP}/env_{tag}.json"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path], capture_output=True)
    ok = r.returncode == 0
    print(f"{'OK  ' if ok else 'FAIL'} {label}")
    if not ok:
        print(r.stderr.decode("utf-8", "replace")[:1000])


payload = {
    "status": "complete",
    "files": [
        ".project-log/docs/phase2_research_brief.md",
        ".project-log/docs/phase2_s3_gap_mining.md",
        "论文/草稿/Main34.tex",
    ],
    "findings": [
        "S0 Research Brief 固化：保留 Koopman，建模与控制器可重设，代码冻结，目标 RA-L/T-RO/会议。",
        "S3 发现 G1-G6：模型级/真实系统级断裂、前馈伪逆可行性缺失、epsilon 无认证路径、temporal lifting 无误差刻画、hierarchical 无结构定理、候选路线 prior-art 未验证。",
        "已验证基础反例：Schur 稳定不推出 2-范数小于 1；A=[[0.95,3],[0,0.95]] 的谱半径为 0.95、2-范数约 3.2755。",
        "因此 Main34.tex 第 737 行的 Schur -> norm<1 推理不能继续作为理论基础。",
    ],
    "next": "S1 文献映射：对 robust Koopman control/MPC、Koopman+CBF、finite-sample/distribution-free learned-model control、residual/adaptive Koopman、history lifting、bilinear/input-dependent Koopman 逐类抽取 Problem/Assumptions/Main Theorem/Limitation/Unresolved Gap。",
}

apply("record.create", {
    "kind": "research",
    "id": "PHASE2-S3-001",
    "title": "阶段② S3 假设与理论 Gap 挖掘",
    "status": "complete",
    "payload": payload,
}, "t40-s3-record", "PHASE2-S3-001")

apply("task.handoff", {
    "task_id": "TASK-004",
    "next_action": "S3 已完成并发现现有 UUB 证明缺陷（Schur 不推出 ||A_cl||_2<1，见 PHASE2-S3-001）。下一步执行 S1 文献结构化映射：robust Koopman control/MPC、Koopman+CBF、finite-sample/distribution-free learned-model control、residual/adaptive Koopman、history lifting、bilinear/input-dependent Koopman；每类抽取 Problem/Assumptions/Main Theorem/Limitation/Unresolved Gap。代码继续冻结。",
}, "t40-s3-handoff", "TASK-004 handoff")

print("revision:", revision())
