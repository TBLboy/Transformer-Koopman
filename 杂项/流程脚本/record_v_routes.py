import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

VAL = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_v_routes_validation_v1.md"
HO = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v6.md"
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
    "document": ".project-log/docs/phase2_gpt_v_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scope": "GPT round-5 routes V1-V6 validation (paradigm-level, non-Koopman) via T5-A/B/C/E",
    "verdicts": {
        "V1 CSMRO": "KILLED on P2: local response Jacobian symmetric part 99.71% indefinite (saddle), PD 0.29%, ND 0%; P1 supports (92.57% PD)",
        "V2 CMPD (convex potential/Legendre dual)": "KILLED on P2: near-symmetric (curl 0.05) but indefinite -> saddle potential, not convex",
        "V3 MMICR (maximal monotone relation)": "KILLED on P2: monotone operators require PSD symmetric part; saddle is not monotone",
        "V4 FMOSI": "not tested; prior-art very high (Chen-Fliess/Volterra); backup only",
        "V5 AFISC": "premise weak: conditional ambiguity only 0.21 (not dominant); needs new probing data",
        "V6 MSIC": "out of frozen-data scope; strategic fallback",
    },
    "key_findings": [
        "P1 control response is strongly monotone (92.57% PD symmetric part) consistent with M(q)>>0",
        "P2 control response is a near-symmetric saddle: 99.71% indefinite, PD 0.29%, ND 0%, curl 0.05",
        "P2 sign asymmetry: corr(u,d) diagonal = [-0.61, +0.62]",
        "P2 is nearly deterministic (ambiguity 0.21) and locally invertible (sigma_min 9.6e-4) but NOT monotone/convex",
        "No single invertible-response geometry unifies P1 and P2",
    ],
    "meta": "After R(18)/N(6)/M(12)/Q(7)/V(6), still no candidate survives gate v0.2.",
    "user_directive": "validate + feedback only, do not invent new routes",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-V-ROUTES-001",
      "title": "GPT 第五轮 V1-V6 验证：P1 强单调成立；P2 为近对称鞍点，V1/V2/V3 被杀死", "status": "complete",
      "payload": val_payload}, "tB0-vroutes")

exp_payload = {
    "document": ".project-log/docs/phase2_gpt_v_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scripts": ["V_P12.py", "V_P12b.py"],
    "P1": {"n": 74640, "corr_u_d_diag": [0.5762, 0.4051, 0.2144],
           "local_lam_min_median": 25.82, "local_lam_max_median": 225.43,
           "frac_PD": 0.9257, "frac_ND": 0.0, "frac_indefinite": 0.0743,
           "curl_local_median": 0.2048, "ambiguity_over_baseline": 0.342},
    "P2": {"n": 20720, "corr_u_d": [[-0.6107, 0.0348], [0.0407, 0.6204]],
           "local_lam_min_median": -0.001228, "local_lam_max_median": 0.001260,
           "frac_PD": 0.00286, "frac_ND": 0.0, "frac_indefinite": 0.9971,
           "curl_local_median": 0.0544, "sigma_min_median": 9.6e-4,
           "ambiguity_over_baseline": 0.214},
    "interpretation": "V1/V2/V3 require monotone/convex response; P2 response is a near-symmetric indefinite saddle (sign flip cannot fix). P1 is strongly monotone.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-V-EXPERIMENTS-001",
      "title": "V 轮廉价实验 T5-A/B/C/E：P1 单调 / P2 鞍点（99.7% 不定）", "status": "complete",
      "payload": exp_payload}, "tB1-vexp")

covers = {"files": [".project-log/docs/phase2_gpt_v_routes_validation_v1.md",
                    ".project-log/docs/phase2_gpt_handoff_v6.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_vroutes.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-GPT-V-ROUTES-001", "--kind", "research",
                    "--subject", "GPT round-5 V1-V6 validation",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tB2-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "已推进 GPT 第五轮 V1–V6（非-Koopman 范式）报告：完成机制级 prior-art + 廉价证伪实验 T5-A/B/C/E，产出 phase2_gpt_v_routes_validation_v1.md 与独立交接稿 phase2_gpt_handoff_v6.md。"
    "判决：P1 控制响应强单调成立（局部 Jacobian 对称部 92.57% 正定，与 M(q)≻0 一致）；P2 控制响应为近对称鞍点（局部对称部 99.71% 不定、PD 仅 0.29%、ND 0%，符号翻转无法挽救；corr(u,d) 对角 [−0.61,+0.62]）→ V1（强单调）死、V2（凸势/Legendre 对偶）死、V3（极大单调关系）死；"
    "V4 prior-art 极高（Chen–Fliess/Volterra）；V5 前提弱（条件歧义仅 0.21）；V6 超冻结数据。P2 近乎确定（歧义 0.21）、近可积（curl 0.05）、局部可逆（σ_min>0）但结构为鞍——不能被任何漂亮定理利用。"
    "跨五轮元结论：R(18)/N(6)/M(12)/Q(7)/V(6) 无候选存活；p1 处处满足经典结构，P2 处处不满足，同一机制难以统一两平台。"
    "下一步：等待 GPT 依据交接稿 v6 返回方向性判断与第六轮；返回后按同法验证。若 GPT 判断无新机制，则转向‘可逆控制响应几何’严谨表征论文（门禁选项 A 的变体）。GOAL-001 门禁仍拒绝；DEC-018 未满足；代码/配置/论文冻结。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tB3-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tB4-handoff")
print("val_sha:", sha(VAL))
print("ho_sha:", sha(HO))
print("revision:", revision())
