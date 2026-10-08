import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
V2 = Path(ROOT) / ".project-log" / "docs" / "paper_theory_section_v2.md"
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

apply("record.create", {"kind": "decision", "id": "DEC-026",
      "title": "GPT 第十七轮：理论路线 CLOSED，RTI-SP/N=5/1-iter 冻结，P2 真机 GO（理论优先执行）",
      "status": "active",
      "payload": {
        "level": "C", "basis": "GPT 第十七轮裁定（用户转发）",
        "decision": "理论路线正式 CLOSED；RTI-SP/N=5/1 SQP iteration 冻结为 P2 主部署配置；P2 HARDWARE GO。论文理论结构固定为：Prop.1（Finite-History Markovization）→ Def（History-Conditioned Low-Rank Koopman Family）→ Prop.2（Latent Rollout Inconsistency Propagation）→ Thm.1（Finite-Horizon Prediction Error Bound）→ Cor.1（Physical-Space Prediction Bound）→ Prop.3（RTI Local Approximation）。physical-space bound 建议补 sanity plot，但非 Gate。",
        "execution_note": "用户 DEC-025 优先完成论文理论章节，真机 GO 状态保留但暂缓执行；当前活跃 Track = Paper Theory（Track B）。",
        "stop_rules_v5": ["route exploration CLOSED", "model family FROZEN", "RTI-SP/N=5/1-iter FROZEN", "matched oracle PASS", "theory diagnostics PASS", "physical-space bound optional (not a gate)", "P2 hardware GO", "真机失败先排查 implementation/distribution shift，不立即换算法"],
      }}, "tV1-dec026")

apply("record.create", {"kind": "research", "id": "PHASE2-ROUND17-NUMCORR-001",
      "title": "第十七轮数字修正：GPT §5 引用的是复核前旧数字，应替换为 v2 修正值",
      "status": "complete",
      "payload": {
        "issue": "GPT 第十七轮 §5/§9 引用 Prop.2 bound/actual = 4.7/7.95/12.1/18.7x 与 linearization remainder 0.27(delta=1e-3)/0.015(delta=1e-2)。这些正是独立复核判定有误的项。",
        "correction_1": "bound/actual 原为口径错配（绝对 epsilon bound vs 归一化 d_M）。同口径（绝对 epsilon vs 绝对 d）修正值 = 1.65/2.82/4.21/6.57x（H=1/5/10/20）；bound>=actual 仍成立。",
        "correction_2": "linearization remainder 在 delta=1e-3 时受浮点噪声主导（非二次标度），M_F 伪值 0.27 无效。修正：delta in {1e-2,3e-2,1e-1} 下 delta^2 标度稳定，拟合 M_F≈0.007。",
        "correction_3": "Cor.1 physical bound 应使用 augmented-map L_F=1.445（非每步乘积常数 1.045）：53/309/1679/48374x（极松，如实标注）。",
        "correction_4": "P=8（platform2.yaml history_length=8），非 4；部署 ckpt 为 P=4/n_layers=3 旧 experiment_006（ALN 类问题，另记）。",
        "unchanged": "epsilon_k median 0.345/q90 0.516/q95 0.567/q99 0.655；d_M 0.120/0.390/0.574/0.928；prod 1.046/1.247/1.541/2.304；L_F median 1.445/q95 1.450/max 1.452；RTI runtime p50 78/p95 120ms。",
        "action_needed": "下一份交 GPT 的 handoff 必须明确标注：§5/§9 的数字已被 v2 修正，请 GPT 以 1.65-6.57x / M_F≈0.007 / L_F=1.445 为准。",
      }}, "tV2-numcorr")

covers = {"files": [".project-log/docs/paper_theory_section_v2.md"],
          "requirements": [], "tasks": ["TASK-005"]}
cpath = f"{TMP}/covers_theory3.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-THEORY-SECTION-003", "--kind", "research",
                    "--subject", "Paper theory section v2.1 (review fixes + GPT round-17 wording constraint)",
                    "--status", "valid", "--task-id", "TASK-005", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tV3-evidence-v21")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:700]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "TASK-005（论文理论章节）v2.1 完成。**第十七轮裁定已接收**：理论路线 CLOSED、RTI-SP/N=5/1-iter 冻结、P2 真机 GO（DEC-026）；理论结构固定为 Prop.1→Def(HCLTK)→Prop.2→Thm.1→Cor.1→Prop.3。"
    "**v2.1 追加**：按 GPT §10 收紧 ε_k 措辞——ε_k>0 仅表示有限维模型有非零一步一致性缺陷，**不能单独**推出训练/部署分布不一致；分布缺口结论须由四元合取支撑（ε_k>0 ∧ d_M(H)↑ ∧ naive propagation failure ∧ rollout-aware recovery），已写入 §3.7 与 §3.12。"
    "**关键提醒（已记 PHASE2-ROUND17-NUMCORR-001）**：GPT §5/§9 引用的 bound/actual 4.7–18.7× 与余项 0.27 是**复核前旧数字**，已被 v2 修正为 **1.65–6.57×**（同口径）与 **M_F≈0.007**（δ² 标度）；Cor.1 应用 L_F=1.445 → 53–48374×；P=8。下次交 GPT 须明确标注该修正。"
    "**下一步**：(1) v2 针对性复检（后台）确认 4 项 HIGH 闭合 → verdict 升 go；(2) 出 handoff v15（含数字修正说明）交 GPT 讨论理论章节；(3) 真机按 DEC-025 推迟。"
)
apply("task.resume", {"task_id": "TASK-005", "next_action": next_action}, "tV4-resume")
apply("task.handoff", {"task_id": "TASK-005", "next_action": next_action}, "tV5-handoff")
print("v2_sha:", sha(V2))
print("revision:", revision())
