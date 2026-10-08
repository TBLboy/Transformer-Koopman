import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
MAIN = Path(ROOT) / "Transformer-Koopman" / "论文" / "新版本" / "Main.tex"
FIG = Path(ROOT) / "Transformer-Koopman" / "论文" / "新版本" / "pictures" / "Figure_mechanism.pdf"
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
        print(p.stdout.decode("utf-8", "replace")[:700]); print(p.stderr.decode("utf-8", "replace")[:1200])

payload = {
    "artifact": "Transformer-Koopman/论文/新版本/Main.tex",
    "artifact_sha256": sha(MAIN),
    "frozen_structure_check": {
        "Prop.1 Finite-History Markovization": "statement + proof (present)",
        "Def.1 HCLTK (r=2)": "present, in Methodology section (not inside the theory section)",
        "Prop.2 Latent Rollout Error Propagation": "statement + proof (present)",
        "Thm.1 Finite-Horizon Prediction Error Bound": "statement + proof (present)",
        "Cor.1 Physical-Space Prediction Bound": "statement + proof (proof ADDED this round)",
        "Prop.3 RTI Local Approximation": "statement + proof (proof ADDED this round)",
        "Def.2 Latent Rollout Inconsistency": "present",
        "Def.3 Rollout-Aware Scheduled Objective": "present",
        "Remark (decoded-feedback only)": "present",
        "Remark (spectral insufficiency)": "present",
        "Assumption A1-A3": "present",
        "Numerical validation table": "present (Tab. diagnostics)",
        "Mechanism figure": "ADDED this round (Fig. fig:mechanism)",
    },
    "changes_this_round": [
        "generated the mechanism figure from gate16_diag_fix.json (normalized ‖ΠA‖₂ / d_M(H) / e_x(H) vs H=1,5,10,20) -> pictures/Figure_mechanism.pdf (+png)",
        "inserted \\begin{figure} with label fig:mechanism into §Numerical Validation, with the 'consistent with ... not causal proof' wording required by GPT §9, and referenced it in the observations paragraph",
        "added the missing proof block for Proposition 3 (mean-value form + A3)",
        "added the missing proof block for Corollary 1 and corrected its coordinate wording (the current physical state is the LAST n coordinates of the history block, not the first n)",
        "static re-check: env pairing ok, no dangling refs, braces balanced, dollars even, 5/5 proof blocks",
    ],
    "proof_count": {"begin_proof": 5, "end_proof": 5},
    "open_gaps": [
        "Experiments section is empty -> Section~\\ref{sec:experiments} cross-references currently point to an empty section (user deferred this until the theory is fully confirmed).",
        "Def.1 sits in the Methodology section while GPT's frozen chain lists Prop.1 -> Def.1 -> Prop.2; confirm with GPT whether Def.1 must move into the theory section or an explicit forward reference suffices.",
        "Figures 1-3 not yet adapted to the new architecture (user deferred).",
        "Chinese/English version conversion not started (GPT §16).",
        "Not compiled: no LaTeX toolchain in this environment.",
    ],
}
apply("record.create", {"kind": "research", "id": "PHASE2-THEORY-COMPLETENESS-001",
      "title": "Theory package completeness audit: 6 frozen results all have proofs; mechanism figure added; Experiments section still empty",
      "status": "complete", "payload": payload}, "tZ20-complete")

covers = {"files": ["Transformer-Koopman/论文/新版本/Main.tex",
                    "Transformer-Koopman/论文/新版本/pictures/Figure_mechanism.pdf"],
          "requirements": [], "tasks": ["TASK-006"]}
cpath = f"{TMP}/covers_complete.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-THEORY-COMPLETENESS-001", "--kind", "research",
                    "--subject", "Theory package completeness + mechanism figure",
                    "--status", "valid", "--task-id", "TASK-006", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tZ21-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:700]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "TASK-006（论文新版本，strict）进行中。**理论包完备性已核**：GPT §7 冻结结构的 6 项核心结果（Prop.1 / Def.1 / Prop.2 / Thm.1 / Cor.1 / Prop.3）**全部具备陈述**，且 **5 个证明块齐全**（本轮补上 Cor.1 与 Prop.3 的 proof，并修正 Cor.1 坐标措辞）；支撑性 Def.2/Def.3/两条 Remark/Assumption A1–A3/诊断表均在。"
    "**本轮新增**：机制图（GPT §9）——由 gate16_diag_fix.json 生成归一化曲线（‖∏A‖₂ 1.00→2.20、d_M 1.00→7.71、e_x 1.00→3.89 vs H=1,5,10,20），已入 `pictures/Figure_mechanism.pdf` 并在 §Numerical Validation 以 `fig:mechanism` 引用（措辞用 'consistent with ... not causal proof'）。记录 PHASE2-THEORY-COMPLETENESS-001 / EV-...-001。"
    "**未闭合**：(a) Experiments 章节仍为空 → 理论对 §sec:experiments 的交叉引用暂指空节（用户已推迟）；(b) Def.1 位于 Methodology 节，与 GPT 冻结链 'Prop.1→Def.1→Prop.2' 的位置需与 GPT 确认是否需移入理论节；(c) 图 1–3 未适配（用户推迟）；(d) 中英版本转换未开始；(e) 本机无 LaTeX，未编译。"
    "**下一步**：(1) 待用户确认理论部分整体无误后，再写实验章节；(2) 与 GPT 确认 Def.1 位置与交叉引用策略；(3) 图 1–3 适配；(4) 参考文献；(5) 训练并导出 P=8 最终模型 + 更新部署栈（P2 真机前置）。"
)
apply("task.resume", {"task_id": "TASK-006", "next_action": next_action}, "tZ22-resume")
apply("task.handoff", {"task_id": "TASK-006", "next_action": next_action}, "tZ23-handoff")
print("main_sha:", sha(MAIN))
print("fig_sha:", sha(FIG))
print("revision:", revision())
