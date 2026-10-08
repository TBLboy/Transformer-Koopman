import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

H9B = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v9b.md"
SEED = Path(ROOT) / ".project-log" / "docs" / "phase2_response_geometry_characterization_seed_v0.1.md"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def revision():
    p = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(p.stdout.decode("utf-8", "replace"))["revision"]

def apply(action, payload, tag):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(),
           "action": action, "payload": payload}
    path = f"{TMP}/env_{tag}.json"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    p = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path], capture_output=True)
    print(("OK   " if p.returncode == 0 else "FAIL ") + tag)
    if p.returncode:
        print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

dec_payload = {
    "id": "DEC-022", "kind": "decision", "status": "active",
    "title": "用户裁定：控制器设计不得以新增观测为前提；第九轮禁止以转 C 作答",
    "payload": {
        "class": "C",
        "decided_by": "user",
        "reason": "用户在第八轮 0/6 后质疑：控制器设计为何要新增观测才行。判定 GPT 第六/七轮提出的『A′ 或 C』中，C（新增观测）不应作为控制器设计的前提。",
        "decision": "阶段② 控制器工作必须留在现有观测内；第九轮交 GPT 的请求（v9b）明确禁止建议新增观测（C1/C2/C3），要求 GPT 要么给出仅用现有观测、非经典包装、可廉价证伪的控制器路线（机制或保证/目标层面均可），要么给出『为何在该对象上不存在此类贡献』的严谨不可能性论证。新增观测仅作为最后手段，不得替代对控制方法本身的思考。",
        "reversible": True,
        "signals": ["conclusion"],
        "notes": [
            "明确了卡点不是可观测性，而是『该控制问题太古典、太容易』：响应 bulk 强单调+良态，常数增益已近最优（oracle 余量 1.25–2×），故新机制无赢的空间。",
            "保留路径：若第九轮给出不可能性论证，则诚实结论可能收敛到 A′（响应几何表征/证伪论文），但需与 DEC-021（控制器创新为首要）协调后再定。",
            "产出：phase2_gpt_handoff_v9b.md（禁止新增观测版交接稿）+ phase2_response_geometry_characterization_seed_v0.1.md。",
        ],
    },
}
apply("record.create", dec_payload, "tZ0-dec022")

covers = {"files": [".project-log/docs/phase2_gpt_handoff_v9b.md",
                    ".project-log/docs/phase2_response_geometry_characterization_seed_v0.1.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_dec022.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-DEC022-001", "--kind", "decision",
                    "--subject", "DEC-022 user ruling: controller work stays on existing observations",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tZ1-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "第八轮（Y1–Y6 控制器专项）验证完成：0/6 通过门禁 v0.3（Y3 Chebyshev 经离线 replay 被否；Y2 被 arXiv:2606.26188 占位；Y1 重包装；Y4/Y5/Y6 排除）。产出 phase2_gpt_y_routes_validation_v1.md、phase2_gpt_handoff_v9.md、桌面交付件。"
    "随后用户 C 级裁定（DEC-022）：控制器设计不得以新增观测为前提，第九轮禁止以转 C 作答。已据此产出 phase2_gpt_handoff_v9b.md（禁止新增观测版：要求 GPT 仅用现有观测给出非经典、可廉价证伪的控制器路线【机制或保证/目标层面均可】，或给出严谨不可能性论证），并产出 phase2_response_geometry_characterization_seed_v0.1.md（响应几何已核实事实集，作为 A′ 种子/C 动机）。交付文件已更新为 GPT交付_阶段②_第九轮_控制器_禁止新增观测_2026-10-05.md。"
    "关键认识：卡点不是可观测性，而是该控制问题太古典（响应 bulk 强单调+良态，常数增益近最优，oracle 余量仅 1.25–2×），导致新机制无赢的空间。"
    "下一步：转发 v9b 给 GPT，等待第九轮（现有观测内的路线或不可能性论证）；返回后按同法验证。若为不可能性论证，则与 DEC-021 协调决定是否转 A′。GOAL-001 门禁仍拒绝；DEC-018 未满足；代码/配置/论文冻结。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tZ2-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tZ3-handoff")
print("h9b_sha:", sha(H9B))
print("seed_sha:", sha(SEED))
print("revision:", revision())
