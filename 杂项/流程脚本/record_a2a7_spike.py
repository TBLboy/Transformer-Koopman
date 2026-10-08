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

DOC = Path(ROOT) / ".project-log" / "docs" / "phase2_a2_a7_minimal_spike_v0.2.md"
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
    "document": ".project-log/docs/phase2_a2_a7_minimal_spike_v0.2.md",
    "document_sha256": sha,
    "scripts": [
        "C:/Users/12187/AppData/Local/Temp/opencode/spike_a2_a7.py",
        "C:/Users/12187/AppData/Local/Temp/opencode/spike_a2_relative_degree.py",
    ],
    "a2": {
        "input_predictive_gain": "current u reduces val RMSE from 0.148239 to 0.116112 (h=1), 0.283895 to 0.174287 (h=2), 0.401977 to 0.198671 (h=3)",
        "output_relative_degree_of_exported_model": 1,
        "CB_full_rank": True,
        "CB_condition_number": 1.1324244663896168,
        "verdict": "relative-degree-of-lifting idea is non-trivial only if a lifting sequence that breaks output relative degree can be exhibited; none constructed yet; A2 not established",
    },
    "a7": {
        "controllability_rank": 10,
        "sigma_min_over_sigma_max": 2.0869751354865798e-07,
        "verdict": "full rank but ill-conditioned with no defensible spectral cutoff; requires a task-error criterion and a controller change to be non-trivial",
    },
    "overall": "A2 and A7 are NOT approved. No new controller structure or non-trivial theorem yet. If neither produces a checkable new condition, escalate to C-level decision: targeted data collection vs scope reduction.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-A2A7-SPIKE-001", "title": "A2/A7 最小可证伪 spike：相对阶平凡、可控谱无隙", "status": "complete", "payload": payload}, "t54-spike")

next_action = (
    "用户反馈候选已审查并记录。P2-B 论据证伪（(A,B)可控秩10/10）；P2-A/P2-C 降为基线；P2-D 暂缓；G-A 仅DEC-018工程前置，G-B/G-E/G-F/G-G kill，G-C/G-D 辅助。"
    "A2/A7 最小 spike 均未通过：导出模型输出相对阶平凡为1且CB条件数1.13（‘保相对阶’无非平凡约束，除非能构造会破坏相对阶的lifting反例）；A7 可控性满秩但sigma_min/sigma_max=2.09e-7、无谱隙，需任务误差判据且改变控制器才非平凡。"
    "当前无候选通过‘新模型结构+新控制器结构+非平凡定理+数据可检验+prior-art delta’。下一步触发C级决策：补采能辨识相对阶/任务相关状态/闭环分布的数据，或缩小论文范围为P1-only/P2-only并接受增量创新。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t54-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t54-handoff")
print("doc_sha256:", sha)
print("revision:", revision())
