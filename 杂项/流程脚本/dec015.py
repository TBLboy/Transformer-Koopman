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
    p = f"{TMP}/env_{tag}.json"
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(env, ensure_ascii=False, indent=2))
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", p], capture_output=True)
    ok = r.returncode == 0
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:400]))


DEC = {
    "id": "DEC-015",
    "title": "阶段② 理论重构的约束与目标定位",
    "status": "active",
    "decision": (
        "阶段② 聚焦论文理论路线重构（建模 + 控制器），代码冻结。"
        "自由度：保留 Koopman 框架，建模（lifting 方式）与控制器（控制律/分析）均可重新设计。"
        "目标定位：机器人/应用期刊（RA-L / T-RO / 会议）——理论够用即可，重创新与实验验证，"
        "控制器要有实用保证。"
    ),
    "rationale": "用户明确：论文与代码均非最终版，不再纠结二者对齐；核心问题是创新点不够、理论强度不足，控制器尤甚。",
    "alternatives": [
        "保留核心只强化理论（被否：自由度不足）",
        "完全开放可换核心（被否：保留 Koopman 积累）",
        "控制顶刊 TAC/Automatica（被否：目标为机器人/应用期刊）",
    ],
}

apply("record.create", {"kind": "decision", "id": "DEC-015", "title": DEC["title"],
                        "status": "active", "payload": DEC}, "t39-dec015", "DEC-015")
print("final revision:", revision())
