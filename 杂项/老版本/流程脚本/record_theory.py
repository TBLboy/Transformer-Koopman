import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
DOC = Path(ROOT) / ".project-log" / "docs" / "paper_theory_section_v1.md"
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

payload = {
    "document": ".project-log/docs/paper_theory_section_v1.md",
    "document_sha256": sha(DOC),
    "scope": "Paper theory section v1: Def.1 (history-conditioned low-rank Koopman family), Prop.1 (finite-history Markovization), Def.2 (latent rollout inconsistency), Prop.2 (error propagation), Rem.1 (spectral stabilization insufficient), Def.3 (rollout-aware training), Thm.1 (finite-horizon error bound), Cor.1 (physical error), Prop.3 (RTI local approximation), scope/non-goals, numerical validation.",
    "theory_objects": ["history-conditioned low-rank A(c)", "augmented state xi / F_Theta", "latent rollout defect d_M", "transition-product amplification", "rollout-aware objective L_R", "finite-horizon bound", "RTI Taylor remainder"],
    "numerical_validation": {
        "eps_k": {"median": 0.345, "q95": 0.567},
        "dM": [0.120, 0.390, 0.574, 0.928],
        "prod_norm": [1.046, 1.247, 1.541, 2.304],
        "L_F": 1.445,
        "bound_over_actual": [4.71, 7.95, 12.1, 18.7],
        "L_C": 1.0,
        "physical_rmse": [0.0108, 0.0222, 0.0297, 0.0419],
        "corollary1_bound_over_actual": [52, 139, 234, 413],
    },
    "honesty_bounds": "All results finite-horizon only; no global Koopman stability, no common Lyapunov, no global asymptotic closed-loop stability, no recursive feasibility. Thm.1 bound and Cor.1 bound reported as valid-but-loose. Prop.1 holds only for the predictor's internal rollout. Prop.3 is classical Taylor remainder, not new SQP theory.",
    "status": "v1 draft complete; independent verification review delegated (in progress)",
}
apply("record.create", {"kind": "research", "id": "PHASE2-THEORY-SECTION-001",
      "title": "论文理论章节 v1：Def.1/Prop.1/Def.2/Prop.2/Rem.1/Def.3/Thm.1/Cor.1/Prop.3 正式化 + 数值验证", "status": "complete",
      "payload": payload}, "tZ0-theory")

covers = {"files": [".project-log/docs/paper_theory_section_v1.md"],
          "requirements": [], "tasks": ["TASK-005"]}
cpath = f"{TMP}/covers_theory.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-THEORY-SECTION-001", "--kind", "research",
                    "--subject", "Paper theory section v1",
                    "--status", "valid", "--task-id", "TASK-005", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tZ1-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "TASK-005（论文理论章节撰写，strict）v1 完成。产出 `.project-log/docs/paper_theory_section_v1.md`："
    "Def.1（history-conditioned low-rank Koopman 族, r=2）、Prop.1（有限历史 Markov 化, augmented state ξ）、"
    "Def.2（latent rollout 不一致 d_M）、Prop.2（误差传播界）、Rem.1（谱稳定不足：ρ<1 ⇏ 时变乘积收缩）、"
    "Def.3（rollout-aware 训练定位）、Thm.1（有限时域误差界，不要求 L_F<1）、Cor.1（物理空间误差, L_C=1）、"
    "Prop.3（RTI 局部二阶余项）、§3.11 范围/非目标、§3.12/§3.12.1 数值验证。"
    "数值：ε_k median 0.345；d_M 0.120/0.390/0.574/0.928；乘积范数 1.046/1.247/1.541/2.304；经验 L_F≈1.45；"
    "Thm.1 bound 保守 4.7–18.7×；Cor.1 物理 bound 保守 52–413×（已如实标注 valid-but-loose）；物理 RMSE 0.0108/0.0222/0.0297/0.0419。"
    "**诚实边界**：仅有限时域；不含全局稳定性/公共 Lyapunov/递归可行性；Prop.1 仅对预测器内部 rollout 成立；Prop.3 为经典 Taylor 余项。"
    "记录 PHASE2-THEORY-SECTION-001 / EV-PHASE2-THEORY-SECTION-001。"
    "**下一步**：(1) 独立复核（verification-reviewer，后台进行中）→ 按意见修订至 v2；(2) 修订后交 GPT 讨论理论章节；(3) 真机实验推迟（DEC-025）。"
)
apply("task.resume", {"task_id": "TASK-005", "next_action": next_action}, "tZ2-resume")
apply("task.handoff", {"task_id": "TASK-005", "next_action": next_action}, "tZ3-handoff")
print("doc_sha:", sha(DOC))
print("revision:", revision())
