import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
MAIN = Path(ROOT) / "Transformer-Koopman" / "论文" / "新版本" / "Main.tex"
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

apply("record.create", {"kind": "decision", "id": "DEC-027",
      "title": "论文写作位置与模板：论文/新版本 + 论文/草稿 的 IEEEtran 模板",
      "status": "active",
      "payload": {
        "level": "B", "basis": "用户明确指令（2026-10-06）",
        "decision": "后续论文写作统一在 `Transformer-Koopman/论文/新版本/` 进行；模板沿用 `Transformer-Koopman/论文/草稿/` 的 IEEEtran 模板（IEEEtran.cls）。已将必要资源复制到新版本：IEEEtran.cls、pictures/（Figure1-3.pdf）、bibtex/，并以 Main34.tex 为基线生成 Main.tex。",
        "consequence": "新版本 Main.tex 已从旧路线（固定 A + hierarchical LQR + UUB）改写为新路线（history-conditioned low-rank A(c) + rollout-aware scheduled training + RTI-SP MPC + finite-horizon theory）。旧草稿保留不动。",
      }}, "tZ1-dec027")

apply("task.create", {"id": "TASK-006", "goal_id": "GOAL-001",
      "title": "论文新版本撰写（论文/新版本/）：理论部分优先，IEEEtran 模板（strict）",
      "extensions": {"implementer": "vibe-main", "owner": "user", "risk_class": "strict"}}, "tZ2-task006")
apply("task.begin", {"task_id": "TASK-006", "run_id": "RUN-006",
      "next_action": "论文新版本 Main.tex：已完成标题/摘要/贡献/引言/方法论(Def.1)/新理论章节(Prop.1,Def.2,Prop.2,Rem.1,Def.3,Thm.1,Cor.1,Prop.3,scope,diagnostics)/RTI-SP 控制器/结论的改写；结构检查通过。待办：实验章节、相关工作总结、图1-3 适配、参考文献补充。"},
      "tZ3-begin")

payload = {
    "artifact": "Transformer-Koopman/论文/新版本/Main.tex",
    "artifact_sha256": sha(MAIN),
    "baseline": "Transformer-Koopman/论文/草稿/Main34.tex (copied to 新版本/Main.tex, then revised)",
    "resources_copied": ["IEEEtran.cls", "pictures/Figure1-3.pdf", "bibtex/"],
    "changes": [
        "title/abstract/keywords rewritten to the new route (history-conditioned low-rank lifting + rollout-aware training + RTI MPC)",
        "contributions rewritten to the 3 GPT round-17 contributions",
        "Def.1 (History-Conditioned Low-Rank Koopman Family, r=2) added to methodology; eq:temporal_dynamics now A(c)",
        "new Sec. Finite-Horizon Theory: Prop.1 (Markovization), Def.2 (rollout inconsistency), Prop.2 (error propagation), Rem.1 (spectral insufficiency), Def.3 (rollout-aware), Thm.1 (finite-horizon bound), Cor.1 (physical), Prop.3 (RTI local), scope/non-goals, diagnostics table",
        "Sec. Real-Time Predictive Control: RTI-SP scheduled predictor + 1-iteration RTI + matched-oracle table",
        "old hierarchical-LQR/UUB section removed; modeling-error subsection adapted to A(c)",
        "conclusion updated",
    ],
    "static_checks": {"env_balance": "ok", "dangling_refs": "none", "brace_balance": 0, "dollar_parity": "even"},
    "not_verified": "LaTeX not installed in this environment -> no compile check (pdflatex/latexmk/tectonic absent); experiments section still empty; figures not yet adapted to the new architecture.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-PAPER-DRAFT-001",
      "title": "论文新版本 Main.tex：新路线（HCLTK + rollout-aware + RTI-SP + finite-horizon theory）改写完成（结构检查通过，未编译）", "status": "complete",
      "payload": payload}, "tZ4-paper")

covers = {"files": ["Transformer-Koopman/论文/新版本/Main.tex"], "requirements": [], "tasks": ["TASK-006"]}
cpath = f"{TMP}/covers_paper.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-PAPER-DRAFT-001", "--kind", "research",
                    "--subject", "Paper new-version Main.tex draft",
                    "--status", "valid", "--task-id", "TASK-006", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tZ5-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:700]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "TASK-006（论文新版本，strict）进行中。**已完成**：在 `论文/新版本/` 建立 IEEEtran 工作区（复制 IEEEtran.cls / pictures / bibtex，以 Main34.tex 为基线生成 Main.tex），并把论文从旧路线（固定 A + hierarchical LQR + UUB）改写为新路线："
    "标题/摘要/关键词/贡献/引言全部重写；方法论加入 **Def.1（History-Conditioned Low-Rank Koopman Family, r=2）**，转移改为 $A(c)$；新增 **§Finite-Horizon Theory**（Prop.1 Markovization → Def.2 rollout inconsistency → Prop.2 error propagation → Rem.1 spectral insufficiency → Def.3 rollout-aware → Thm.1 finite-horizon bound → Cor.1 physical → Prop.3 RTI local → scope/non-goals → diagnostics 表）；新增 **§Real-Time Predictive Control**（RTI-SP scheduled predictor + 1-iter RTI + matched-oracle 表）；删除旧 LQR/UUB 章节；结论更新。"
    "静态检查通过（环境配对无误、无悬空引用、括号/美元符平衡）。记录 DEC-027 / PHASE2-PAPER-DRAFT-001 / EV-PHASE2-PAPER-DRAFT-001。"
    "**未验证**：本机无 LaTeX（pdflatex/latexmk/tectonic 均缺失）→ **未编译**；实验章节仍为空；图 1-3 尚未适配新架构。"
    "**下一步**：(1) 撰写实验章节（需真机 E1–E5 或先用离线结果占位）；(2) 更新 Related Work / Positioning 以覆盖 history-conditioned transition 与 RTI 相关工作；(3) 适配/重绘图 1-3；(4) 补参考文献；(5) 若有 LaTeX 环境则编译验证。"
)
apply("task.resume", {"task_id": "TASK-006", "next_action": next_action}, "tZ6-resume")
apply("task.handoff", {"task_id": "TASK-006", "next_action": next_action}, "tZ7-handoff")
print("main_sha:", sha(MAIN))
print("revision:", revision())
