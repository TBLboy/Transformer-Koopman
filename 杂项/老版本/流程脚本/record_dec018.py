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
    "decision": "将『稳定化学习模型（rho(A) 受控，目标 <= koopman.rho_max）+ T1′ 界非空泛』作为阶段③的硬前提。",
    "rationale": "S8b 证明 P2 部署模型 rho(A)=2.0878、||A||=29.1、cond(P)~2e10、T1′ 常数 ~8e15，界数学有效但数值空泛。根因：config 设 koopman.rho_max=0.9999（P2）/0.95（P1）但 svd_clipping=false，稳定性约束从未生效（INV1 分叉违规）。理论实用性要求稳定化模型。",
    "impact": "阶段③ 必须先落实稳定性约束（SVD clipping / 投影 或 训练期谱约束），再评估 T1′ 界是否非空泛；否则理论贡献无法在真实模型上展示。",
    "class": "B",
    "user_confirmed": False,
    "reversible": True,
}

apply("record.create", {"kind": "decision", "id": "DEC-018", "title": "阶段③ 硬前提：稳定化模型 + 非空泛界", "status": "active", "payload": payload}, "t50-dec018")
print("revision:", rev())
