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
    "gpt_round20_status": "THEORY ROUTE CLOSED / PROOF AUDIT PASS / NUMERICAL CONSISTENCY PASS / THEORY TEXT FROZEN",
    "round20_actions": {
        "Q-A": "adopted: the unified stride-1 diagnostic set (gate16_diag_final.json) replaces round-18 sec.21 for the epsilon-dependent rows; already applied in the paper table",
        "Q-B_sec17": "ADDED the semantic binding sentence in the training section: 'During rollout training, z_hat_{k+i} denotes the recursively predicted latent state and therefore corresponds to the propagated latent state z^P_{k+i} used in the theoretical analysis.' Training keeps z_hat; theory keeps z^P/z^E.",
        "language_polish": [
            "theory section opener rewritten as 'This section develops a finite-horizon theory for ... i.e. ...' (was 'We recall ...')",
            "'propagated recursively rather than re-encoded' -> 'instead of being re-encoded at every step'",
            "'governed by two independent factors: the local defect' -> 'governed by two factors: the local one-step defect'",
            "'This supports the local validity' -> 'This result supports the local validity'",
        ],
    },
    "static_checks": {"missing_bibitem_for_cite": "none", "dangling_refs": "none",
                      "env_mismatch": "none", "brace_balance": 0, "dollar_parity": "even",
                      "proof_blocks": "5/5", "cite_keys_used": 39, "bibitems": 50},
    "known_cosmetic_issue": "the manuscript still carries revision color markers from the previous draft: \\textcolor{red} x20, \\textcolor{blue} x5, \\color{red} x10 (mostly in the methodology/training sections, not the theory section). These are formatting markers, not content; they should be removed before submission. Not removed unilaterally because they may be intentionally kept for GPT review.",
    "remaining_track_items": [
        "LaTeX compilation (typesetting QA, not a gate): full compile + bibtex + second pass + warning inspection + PDF visual check - no LaTeX toolchain locally",
        "final history-length P configuration audit (P=8 per platform2.yaml and all experiments; deploy ckpt P=4 is stale legacy) - already audited (PHASE2-CONFIG-AUDIT-001 / DEC-028), pending the actual P=8 model training + deploy re-export",
        "Experiments/Results/Discussion sections",
        "Figures 1-3 adaptation; mechanism figure already generated",
        "Chinese/English version",
    ],
}
apply("record.create", {"kind": "research", "id": "PHASE2-ROUND20-EDITS-001",
      "title": "GPT round-20: theory text FROZEN; sec.17 training/theory notation binding added; theory-section language polish applied",
      "status": "complete", "payload": payload}, "tZ50-r20")

covers = {"files": ["Transformer-Koopman/论文/新版本/Main.tex"], "requirements": [], "tasks": ["TASK-006"]}
cpath = f"{TMP}/covers_r20.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-ROUND20-EDITS-001", "--kind", "research",
                    "--subject", "Round-20 sec.17 binding + theory language polish",
                    "--status", "valid", "--task-id", "TASK-006", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tZ51-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:700]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "TASK-006（论文新版本，strict）进行中。**目标**：论文理论部分的文字内容（含证明/定理/参考文献）；实验与绘图暂停；与 GPT 迭代。"
    "**第二十轮裁定已执行**：THEORY ROUTE CLOSED / PROOF AUDIT PASS / NUMERICAL CONSISTENCY PASS / **THEORY TEXT FROZEN**。"
    "Q-A = YES（统一 stride-1 数值集取代第十八轮 §21，已在表格落地）；Q-B：训练节保留 ẑ，已按 §17 在训练节首次 rollout latent 处加入语义绑定句（ẑ_{k+i} ≡ 理论 z^P_{k+i}）。另按 Priority 1 完成理论节语言润色（开场句、propagation 措辞、two factors、local validity 等）。"
    "静态检查：引用无缺失、无悬空引用、环境配对、括号/美元符平衡、5/5 证明块。记录 PHASE2-ROUND20-EDITS-001 / EV-...-001。"
    "**遗留（非理论 Gate）**：(a) 全文仍带旧稿修订颜色标记（\\textcolor{red}×20、\\textcolor{blue}×5、\\color{red}×10，主要在方法/训练节）——投稿前应移除，未擅自删除以免影响 GPT 审阅；(b) 本机无 LaTeX，未编译（排版 QA）；(c) P_final 配置审计已完成（P=8；部署 ckpt P=4 系旧遗留），待训练 P=8 最终模型并重导部署资产；(d) Experiments/Results/Discussion、图 1–3、中英转换。"
    "**下一步**：按 GPT §24 优先级——P1 理论节语言整理（本轮已做主要部分，可再复核）；P2 P_final 审计（已做）；P3 LaTeX 编译；P4 P2 真机；P5 实验章节。"
)
apply("task.resume", {"task_id": "TASK-006", "next_action": next_action}, "tZ52-resume")
apply("task.handoff", {"task_id": "TASK-006", "next_action": next_action}, "tZ53-handoff")
print("main_sha:", sha(MAIN))
print("revision:", revision())
