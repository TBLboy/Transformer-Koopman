import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
VAL = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_z_routes_validation_v1.md"
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

val_payload = {
    "document": ".project-log/docs/phase2_gpt_z_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scope": "GPT round-9 Z0/Z1/Z2 validation under DEC-022 (no new observations)",
    "verdicts": {
        "Z0 NFATSR": "CONFIRMED numerically (const adversarial N6 == (q*)^N exactly; Chebyshev amplified 89x/372x). Elementary proof, adjacent to regret-optimal control -> modest novelty, better as one section of a characterization paper.",
        "Z1 ERCRC": "KILLED - tail error worsens (P2 q95 0.192 vs 0.027; P1 q95 0.475 vs 0.204), memory grows unbounded (max 281), naive clip not better. All 3 self-set kill criteria met.",
        "Z2 REIC": "KILLED - geometric-median aggregation improves inverse-command error only ~2.5-5% (threshold 20%); failures correlated; prior-art mature.",
    },
    "round9_outcome": "no controller route passes gate v0.3; but Z0 is a valid negative/limit result",
    "lockdown_chain": "bulk strongly monotone + constraints inactive + no output/task nullspace + no low-order residual dynamics + Newton/secant occupied + polynomial acceleration killed by time-variation + best constant gain minimax-optimal + tail-robust recycling ineffective + inverse aggregation ineffective + robust/DLS/IQC/Hinf/funnel/sliding/conformal classical + new observations forbidden (DEC-022)",
    "conclusion": "Under current observations and gate v0.3, no empirically-motivated non-classical controller route remains.",
    "recommended": "A' characterization/impossibility paper (no new observations required): learned response geometry + no-free-acceleration + empirical falsification of Y3/Z1/Z2 + constant-gain response feedback more robust than deployed Koopman+LQR.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-Z-ROUTES-001",
      "title": "GPT 第九轮 Z0/Z1/Z2 验证：Z0 成立，Z1/Z2 被否；现有观测内控制器搜索正式封闭", "status": "complete",
      "payload": val_payload}, "tZ9-zroutes")

exp_payload = {
    "document": ".project-log/docs/phase2_gpt_z_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scripts": ["V_Z1.py", "V_Z2.py"],
    "Z0_numerical": {"P2": {"kappa": 12.22, "const_adv_N6": 0.3738, "cheb_adv_N6": 33.41, "theory": 0.3738},
                     "P1": {"kappa": 114.25, "const_adv_N6": 0.9003, "cheb_adv_N6": 335.21, "theory": 0.9003}},
    "Z1_errc": {"P2_const_q95": 0.0266, "P2_errc_q95": 0.1923, "P2_errc_mem_max": 281.2,
                "P1_const_q95": 0.2041, "P1_errc_q95": 0.4753},
    "Z2_geomed": {"P2_single_q95": 408.93, "P2_geomed_q95": 396.33,
                  "P1_single_q95": 6.056, "P1_geomed_q95": 5.908},
    "interpretation": "Z1 and Z2 provide no tail-robustness benefit on actual response Jacobians; Z0 confirms best constant gain is minimax under adversarial time-varying sector.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-Z-EXPERIMENTS-001",
      "title": "Z0/Z1/Z2 便宜证伪：常数增益 minimax 确认；ERCRC 尾部更差；几何中位聚合无收益", "status": "complete",
      "payload": exp_payload}, "tZA-zexp")

covers = {"files": [".project-log/docs/phase2_gpt_z_routes_validation_v1.md",
                    ".project-log/docs/phase2_response_geometry_characterization_seed_v0.1.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_zroutes.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-GPT-Z-ROUTES-001", "--kind", "research",
                    "--subject", "GPT round-9 Z0/Z1/Z2 controller validation (no-new-observation)",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tZB-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "第九轮（Z0/Z1/Z2，禁止新增观测）验证完成：Z0（时变 sector 下无免费加速）数值确认——常数增益对抗 N=6 收缩精确等于 ((κ-1)/(κ+1))^N（P2 0.3738、P1 0.9003），Chebyshev 被放大 89×/372×，解释第八轮 Y3 失败；Z1（ERCRC 误差回收剪切）被否——尾部误差更差（P2 q95 0.192 vs 0.027）、记忆发散（max 281）、naive clip 不优，三条 kill 判据全中；Z2（逆命令几何中位聚合）被否——改善仅 2.5–5%（门槛 20%）。"
    "产出 phase2_gpt_z_routes_validation_v1.md；记录 PHASE2-GPT-Z-ROUTES-001 / PHASE2-Z-EXPERIMENTS-001 / EV-PHASE2-GPT-Z-ROUTES-001。"
    "累积结论（第 1–9 轮）：在当前观测 + 门禁 v0.3 下，不再存在有经验动机的非经典控制器路线（完整封锁链见报告 §5）。唯一存活资产=Z0 边界结果 + 响应几何表征。"
    "建议方向：转 A′『表征/不可能性』论文（无需新增观测，满足 DEC-022）：学习响应几何 + no-free-acceleration + Y3/Z1/Z2 经验否证 + 直接响应反馈比已部署 Koopman+LQR 更稳健。是否满足 DEC-021（控制器创新为首要）需用户裁定。"
    "下一步：等待用户就『A′ 论文 vs 其他』拍板。GOAL-001 门禁仍拒绝；DEC-018 未满足；代码/配置/论文冻结。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tZC-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tZD-handoff")
print("val_sha:", sha(VAL))
print("revision:", revision())
