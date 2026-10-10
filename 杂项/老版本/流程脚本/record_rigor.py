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

payload = {
    "artifact": "Transformer-Koopman/论文/新版本/Main.tex",
    "artifact_sha256": sha(MAIN),
    "scope": "Rigorous audit of the theory text (definitions, propositions, theorem, corollary, remarks, assumption, references) - proofs must be genuine and closed, not casually generated.",
    "audit_verdict_per_result": {
        "Prop.1 Finite-History Markovization": "proof present and correct (shift + context + transition composition)",
        "Prop.2 Latent Rollout Error Propagation": "proof present and correct (insert-subtract + triangle inequality + unrolling)",
        "Thm.1 Finite-Horizon Prediction Error Bound": "proof present and correct given (A1)-(A3); finite-horizon form only (L_F>1)",
        "Cor.1 Physical-Space Prediction Bound": "proof ADDED; coordinate wording FIXED (current state = LAST n coords of history block, not first n)",
        "Prop.3 RTI Local Approximation": "proof FIXED: the single-t mean-value form is invalid for vector-valued maps; replaced by the integral Taylor remainder + operator-norm bound; A3 restated in terms of the second-derivative operator norm",
        "Remark (spectral insufficiency)": "assertion correct; CITATIONS ADDED (Rota-Strang 1960; Daubechies-Lagarias 1992; Jungers 2009)",
    },
    "defects_fixed": [
        "Prop.3 proof: mean-value form -> integral Taylor remainder (rigorous)",
        "Cor.1: missing proof added + 'first n' -> 'last n coordinates of the history block' wording fix",
        "Def.2: 'bounded below' -> 'the quantity for which Proposition 2 provides an upper bound'",
        "Assumption A3: bounded Hessian -> bounded second-derivative operator norm ||D^2 F|| <= M_F",
    ],
    "citations_added": [
        "rota1960joint: G.-C. Rota and G. Strang, Nederl. Akad. Wetensch. Proc. Ser. A 63 (Indag. Math. 22), 379-381, 1960",
        "daubechies1992sets: I. Daubechies and J. C. Lagarias, Linear Algebra Appl. 161, 227-263, 1992",
        "jungers2009joint: R. M. Jungers, The Joint Spectral Radius, LNCIS 385, Springer, 2009",
        "diehl2005realtime: M. Diehl, H. G. Bock, J. P. Schloeder, SIAM J. Control Optim. 43(5), 1714-1736, 2005",
        "gros2020rti: S. Gros et al., Int. J. Control 93(1), 62-80, 2020",
    ],
    "static_checks": {"missing_bibitem_for_cite": "none", "dangling_refs": "none",
                      "env_mismatch": "none", "brace_balance": 0, "dollar_parity": "even",
                      "proof_blocks": "5/5", "cite_keys_used": 39, "bibitems": 50},
    "open_questions_for_gpt": [
        "Q1 relation between epsilon (Thm.1) and epsilon_k (Prop.2): distinct quantities; table reports only epsilon_k. Add a short remark?",
        "Q2 should the definition of F* (re-encode) vs F_Theta (propagate) be made explicit so readers see that (A1)'s epsilon absorbs the encode/propagate gap?",
        "Q3 Def.1 (HCLTK) sits in Methodology while GPT's frozen chain writes Prop.1 -> Def.1 -> Prop.2; move it?",
        "Q4 assumption numbering: single block (A1)(A2)(A3) vs separate Assumption 1/2/3?",
        "Q5 should Prop.2 state explicitly that z_hat is the propagated latent z^P?",
    ],
    "reports": [".project-log/docs/phase2_theory_rigor_audit_v1.md",
                "Desktop/GPT讨论_阶段③_第十八轮后_理论严谨性审计与修正_2026-10-06.md"],
    "not_verified": "no LaTeX toolchain -> not compiled; static structural checks only.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-THEORY-RIGOR-AUDIT-001",
      "title": "Theory rigor audit: 2 real defects fixed (Prop.3 mean-value, Cor.1 wording), 5 verified citations added; 5 wording/positioning questions for GPT",
      "status": "complete", "payload": payload}, "tZ30-audit")

covers = {"files": ["Transformer-Koopman/论文/新版本/Main.tex",
                    ".project-log/docs/phase2_theory_rigor_audit_v1.md"],
          "requirements": [], "tasks": ["TASK-006"]}
cpath = f"{TMP}/covers_rigor.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-THEORY-RIGOR-AUDIT-001", "--kind", "research",
                    "--subject", "Theory rigor audit and fixes",
                    "--status", "valid", "--task-id", "TASK-006", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tZ31-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:700]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "TASK-006（论文新版本，strict）进行中。**目标已收敛**：只做论文**理论部分的文字内容**（含证明/定理/参考文献），实验与绘图暂停。"
    "**本轮完成理论严谨性逐条审计**：5 个证明块（Prop.1/Prop.2/Thm.1/Cor.1/Prop.3）全部通过审计；**修复 2 处真实缺陷**——(a) Prop.3 的向量值'中值形式'不严格 → 改用积分型 Taylor 余项 + 算子范数界，并统一 A3 口径；(b) Cor.1 坐标措辞错（first n → history 块最后 n 个坐标）并补证明；另修 Def.2 'bounded below' 措辞错误。**补齐 5 条经核实的真实引用**（Rota-Strang 1960 / Daubechies-Lagarias 1992 / Jungers 2009 用于谱稳定 Remark；Diehl 2005 / Gros 2020 用于 RTI）。"
    "静态检查：引用无缺失、无悬空引用、环境配对、括号/美元符平衡、5/5 证明块。产出 `phase2_theory_rigor_audit_v1.md` + 桌面 GPT 讨论稿；记录 PHASE2-THEORY-RIGOR-AUDIT-001 / EV-...-001。"
    "**待 GPT 裁定 5 项**（均非证明漏洞）：Q1 ε(Thm.1) 与 ε_k(Prop.2) 关系是否加 Remark；Q2 F*（重编码）vs F_Θ（传播）口径差是否显式说明；Q3 Def.1 是否移入理论节；Q4 assumption 编号是否拆分；Q5 Prop.2 是否显式定义 ẑ=z^P。"
    "**下一步**：(1) 把审计报告与 5 个问题交 GPT 讨论；(2) 按 GPT 裁定修订理论文字；(3) 理论文字定稿后再考虑实验/图/翻译。"
)
apply("task.resume", {"task_id": "TASK-006", "next_action": next_action}, "tZ32-resume")
apply("task.handoff", {"task_id": "TASK-006", "next_action": next_action}, "tZ33-handoff")
print("main_sha:", sha(MAIN))
print("revision:", revision())
