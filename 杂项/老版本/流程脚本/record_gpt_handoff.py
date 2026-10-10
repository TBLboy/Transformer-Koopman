import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

DOC = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v1.md"
sha = hashlib.sha256(DOC.read_bytes()).hexdigest()

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
        print(p.stdout.decode("utf-8", "replace")[:800])
        print(p.stderr.decode("utf-8", "replace")[:1500])

payload = {
    "document": ".project-log/docs/phase2_gpt_handoff_v1.md",
    "document_sha256": sha,
    "scope": "remaining L3 gates completed + R16 negative scan + final standalone GPT handoff report",
    "l3_full_texts": ["2509.17010", "2606.02938", "2603.27548", "2601.11901", "2601.22496"],
    "new_key_results": {
        "2602.14537": "exact Koopman linear embedding exists <=> CAP structure (necessary+sufficient); constrains any exact-linear-representation claim",
        "2603.15091": "principal angle decomposition (PAD) as dynamics-informed SVD alternative + multi-step bounds + dictionary refinement (hits R1/R2/R18)",
        "2209.08637": "control-aware Koopman embedding refinement (hits R16)",
        "2603.17545": "data-driven Vinnicombe nu-gap (control-relevant mismatch metric, hits R2 space)",
        "2603.27548": "CCI gauge-invariant KCF accuracy measure (hits R2/R16/R18)",
        "2601.22496": "action sufficiency for goal representations; value suff !=> action suff (hits R16)",
    },
    "residual_space_ranking": "R16 (Koopman-specific control sufficiency) > R3 (P1 residual + control theorem) > rest (renamed/downgraded)",
    "verdict": "no route qualifies as stage-2 main result; 18 routes renamed/downgraded/partial; only R16/R3 retain conceptual room but need mechanism-level restatement",
    "r16_negative_scan": {"goal_conditioned_koopman": 0, "action_or_control_sufficient": 22},
    "unverified": "ICLR2026 Gramian not located on arXiv; some 2026 IDs need re-verification",
    "user_directive": "validate + feedback only; deliver standalone md to GPT",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-ROUTE-VALIDATION-004",
      "title": "剩余 L3 闸门补完 + R16 负面扫描：产出最终 GPT 交接稿，无主结果",
      "status": "complete", "payload": payload}, "t90-val4")

next_action = (
    "已按用户要求补完全部剩余 L3/负面扫描闸门，并产出**最终独立交接稿** phase2_gpt_handoff_v1.md（自包含，可直接交给 GPT：含背景/闸门、Test A/B/B′/C 复现数据、R1–R18 机制级占位、R16 负面扫描、组合评估、残余排序、对下一轮 8 条要求、完整引用清单与边界）。"
    "新增关键占位：2602.14537（精确 Koopman 线性嵌入 ⇔ CAP 结构）、2603.15091（PAD 主动角度分解）、2209.08637（控制感知 Koopman 精化）、2603.17545（数据驱动 ν-gap）。"
    "残余空间：R16（Koopman 专属控制充分性）> R3（P1 残差+控制定理）。"
    "下一步：等待外部构思方（GPT）依据交接稿返回机制级新路线报告，返回后按同法做 L1/L2/L3 验证与廉价证伪实验。GOAL-001 门禁仍拒绝完成；DEC-018 未满足；代码/配置/论文冻结。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t90-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t90-handoff")
print("handoff_sha256:", sha)
print("revision:", revision())
