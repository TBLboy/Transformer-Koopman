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
    "gpt_round19_rulings_applied": {
        "M1": "ADDED Remark 'epsilon versus epsilon_k' after Thm.1 with the exact wording of GPT round-19 sec.6 (label rem:eps_vs_epsk)",
        "M2": "ADDED explicit definition of F* before Thm.1 (reference augmented transition induced by true observed finite-history evolution + encoder-consistent representation; explicitly NOT the plant); mismatch semantics closed",
        "M3": "SPLIT the single assumption block into Assumption 1 (operating-set model mismatch), Assumption 2 (Lipschitz continuity, no contraction assumed), Assumption 3 (second-order regularity for RTI); all \\ref sites updated",
        "M4": "UNIFIED notation: Prop.2 now states z_hat = z^P (propagated latent) and uses z^P / z^E throughout; Cor.1 and the Thm.1 preamble updated to z^P",
        "Q3": "Def.1 stays in the Methodology section; theory section now opens with 'We recall the history-conditioned low-rank Koopman family introduced in Section ...'",
        "sec14": "Prop.2 now also states the d_k = 0 (encoder-consistent start) simplification",
    },
    "eps_k_conflict_resolved": {
        "rule": "GPT round-19 sec.17: go back to the final script output; do not average, do not choose from memory.",
        "root_cause": "the two earlier scripts used different sampling: gate16_theory_diagnostics.py computed eps_k with stride 1 over the full k-range (median 0.3454), while gate16_diag_fix.py used stride 4 with a shorter k-range (median 0.3473). d_M / product norms were stride 4 in BOTH, hence identical.",
        "resolution": "new single-source script gate16_diag_final.py recomputes eps_k, d_abs, d_M, product norms, L_F, Prop.2 ratio and Cor.1 ratio under ONE documented sampling (stride 1 for eps_k and the rollout diagnostics; L_F unchanged sampling). Output: gate16_diag_final.json.",
        "eps_k_abs": {"median": 0.3454, "q90": 0.5159, "q95": 0.5673, "q99": 0.655, "max": 0.7998},
        "confirmed": "eps_k median = 0.345 -> matches the frozen round-18 value; the 0.347 was the stride-4 subsample.",
        "dependent_shifts": {
            "d_abs(H)": "0.346/1.122/1.645/2.663 (was stride-4 0.347/1.114/1.673/2.678)",
            "Prop.2 bound/actual": "1.64/2.77/4.22/6.52x (was 1.65/2.82/4.21/6.57x)",
            "Cor.1 bound/actual": "53/305/1657/47750x (was 53/309/1679/48374x)",
        },
        "unchanged": "d_M 0.120/0.390/0.574/0.928; product norms 1.046/1.247/1.541/2.304; L_F median 1.445 / max 1.452; M_F ~ 0.007; physical RMSE 0.011/0.022/0.030/0.042; RTI p50 78 / p95 120 ms",
        "paper_table_updated": "eps_k 0.345/0.567; d_abs 0.346/1.122/1.645/2.663; Prop.2 ratio 1.64/2.77/4.22/6.52x; Cor.1 text 53-47750x; footnote documents the sampling",
    },
    "static_checks": {"missing_bibitem_for_cite": "none", "dangling_refs": "none",
                      "env_mismatch": "none", "brace_balance": 0, "dollar_parity": "even",
                      "proof_blocks": "5/5", "cite_keys_used": 39, "bibitems": 50},
    "not_verified": "no LaTeX toolchain -> not compiled; static structural checks only.",
    "open_for_gpt": [
        "Confirm the unified stride-1 diagnostic set replaces the frozen round-18 sec.21 list for the epsilon-dependent rows (eps_k, d_abs, Prop.2 ratio, Cor.1 ratio); d_M / product / L_F / M_F / RMSE / RTI unchanged.",
        "Training section still writes the one-step/multi-step training predictions as z_hat (a different context from the theory rollout); confirm whether M4 should also rename those to z^P for whole-paper uniformity or leave them.",
    ],
}
apply("record.create", {"kind": "research", "id": "PHASE2-ROUND19-EDITS-001",
      "title": "GPT round-19 applied: M1-M4 theory-text edits; eps_k conflict resolved at 0.345 (unified stride-1 diagnostic)",
      "status": "complete", "payload": payload}, "tZ40-r19")

covers = {"files": ["Transformer-Koopman/论文/新版本/Main.tex"], "requirements": [], "tasks": ["TASK-006"]}
cpath = f"{TMP}/covers_r19.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-ROUND19-EDITS-001", "--kind", "research",
                    "--subject", "Round-19 M1-M4 edits and eps_k resolution",
                    "--status", "valid", "--task-id", "TASK-006", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tZ41-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:700]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "TASK-006（论文新版本，strict）进行中。**目标**：只做论文理论部分的文字内容（含证明/定理/参考文献），实验与绘图暂停，继续与 GPT 迭代直至理论文字定稿。"
    "**第十九轮裁定已执行**：Proof Audit = PASS。M1 已加 ε vs ε_k Remark（rem:eps_vs_epsk）；M2 已在 Thm.1 前显式定义 F*（reference augmented transition，非 plant）；M3 已拆为 Assumption 1/2/3 并更新全部引用；M4 已统一 z^P/z^E 记号（Prop.2 声明 ẑ≡z^P，Cor.1/Thm.1 前文同步）；Q3 Def.1 保留在 Methodology，理论节加 'Recall ...' 开场；§14 补 d_k=0 简化。"
    "**ε_k 冲突已解决（GPT §17）**：根因是两个旧脚本采样步长不同（stride 1 → 0.3454；stride 4 → 0.3473）。新建单一事实源脚本 `gate16_diag_final.py`（统一 stride 1）→ **ε_k median = 0.345（与冻结值一致）**，q95 = 0.567。依赖量同步更新：d_abs 0.346/1.122/1.645/2.663；Prop.2 比值 1.64/2.77/4.22/6.52×；Cor.1 文本 53–47750×。表格已更新并加采样脚注。d_M/prod/L_F/M_F/RMSE/RTI 不变。"
    "静态检查：引用无缺失、无悬空引用、环境配对、括号/美元符平衡、5/5 证明块。记录 PHASE2-ROUND19-EDITS-001 / EV-...-001。"
    "**下一步**：(1) 把回执交 GPT 确认统一 stride-1 数值集是否取代第十八轮 §21，并确认训练节 ẑ 是否也统一为 z^P；(2) 按裁定做最后语言整理；(3) 理论文字冻结后再考虑实验/图/翻译。"
)
apply("task.resume", {"task_id": "TASK-006", "next_action": next_action}, "tZ42-resume")
apply("task.handoff", {"task_id": "TASK-006", "next_action": next_action}, "tZ43-handoff")
print("main_sha:", sha(MAIN))
print("revision:", revision())
