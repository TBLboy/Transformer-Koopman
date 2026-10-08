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
    "组合路线 S6 + S7 + S8(数值) 完成：修正定理 T1 通过 C1-C9（数值验证：DARE 恒等式、原界在 ‖A_cl‖>1 时失效、T1 随 D 单调且成立、δ 项必要、β 定价、P2 型 G 注入且未指令偏置在 range(G)⊥）。"
    "已修正 phase2_theory_construction_v0.1.md 的 ker G 建模错误（G 满列秩；未指令偏置 a_perp ∈ range(G)⊥ 维数 m_a-m）。"
    "下一步 S8 剩余项（代码仍冻结）：(1) 用 P1/P2 冻结 checkpoint/验证数据估计 ε_data/ε_enc 经验值；"
    "(2) 检查 P2 数据是否有张紧/松弛模式代理量以界定 a_max 可估性。若二者不可行且 B a_perp=0，则 A9 载体失效，回退纯 rigor+A2/A7。"
)

payload = {
    "status": "complete",
    "documents": [".project-log/docs/phase2_theory_construction_v0.1.md"],
    "verification": {
        "script": "C:/Users/12187/AppData/Local/Temp/opencode/s8_verify_t1.py",
        "interpreter": "D:/conda/envs/edmddl2/python.exe",
        "C9_results": [
            "DARE identity residual ~6.8e-15",
            "non-normal A (rho=0.9, ||A||=2.37); A_cl rho=0.32 but ||A_cl||=1.1123>1 -> old bound denominator -0.1123 (meaningless)",
            "simulated worst ||e^z||=0.225 <= T1 radius 1.130",
            "T1 radius strictly monotone in D",
            "omitting feedforward-infeasibility term -> false zero; keeping -> steady offset 10.6 (delta necessary)",
            "P2-type G injective, ker G={0}; uncommanded bias a_perp in range(G)^perp satisfies G^T a_perp~1e-16; beta enters bound iff B a_perp != 0",
        ],
    },
    "doc_correction": "phase2_theory_construction_v0.1.md section 2/5/C4: fixed ker G misstatement (G full column rank; uncommanded tension bias lives in range(G)^perp, dim m_a-m).",
    "verdict": "T1 now numerically supported and self-consistent. Combination route viability still hinges on S8 data-side items (eps estimation, P2 tension-mode proxy / a_max boundability).",
}

rc = apply("record.create", {"kind": "research", "id": "PHASE2-S8-001", "title": "阶段② S8 数值验证（T1 修正定理 + 建模修正）", "status": "complete", "payload": payload}, "t47-s8")
if rc == 0:
    apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t47-resume")
    apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t47-handoff")
print("revision:", rev())
