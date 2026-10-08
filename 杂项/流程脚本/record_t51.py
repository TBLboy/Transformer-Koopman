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


next_action = (
    "阶段② 组合路线理论构造完成并经独立复核（REV-PHASE2-THEORY-001=conditional；EV-PHASE2-THEORY-001=valid，sha256 绑定）。"
    "复核 C-1..C-4 CONFIRMED（原定理为假、须补 P_G 项、DARE 恒等式、T1′ 正确）；已按复核修正：A1 补 lambda>0、T1′ 补 A6、定理2 降级为命题1、记号 B≡B_G/m=2、脚本改谱范数并加 DARE 残差断言。"
    "新发现：P2 上 DARE 残差 1.3e4（病态，LQR 解不可靠），进一步支持 DEC-018 稳定化硬前提。"
    "剩余：novelty delta（vs Strasser 2026 / Cibulka-Korda-Hanis 2025 / Nuske）全文比对未做；C11 离域阈值标定未决；P1 无 checkpoint。"
    "下一步：进入阶段③（落实稳定化 + 重训 + 论文 T1′/命题1 落地），或先补 novelty delta。"
)

apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t51-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t51-handoff")
print("revision:", rev())