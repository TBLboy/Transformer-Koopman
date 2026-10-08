import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

VAL = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_w_routes_validation_v1.md"
HO = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v7.md"
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
    "document": ".project-log/docs/phase2_gpt_w_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scope": "GPT round-6 routes W1-W6 validation via T6-0/1/2/3; T6-0 audit point confirmed -> round-5 conclusion revised",
    "correction_of_round5": {
        "round5_claim": "'sign flip cannot rescue, because SJS stays indefinite' - stated for CONGRUENCE (both input and output)",
        "corrected": "one-sided OUTPUT change d~=Sd gives Jacobian SJ (not SJS); sym(SJ) CAN be positive definite; with stable eigenframe a CONSTANT S0 suffices",
        "impact": "P2 is NOT an un-saveable saddle; it is monotone under a fixed output reflection S0=diag(-1,1). Round-5 V1 kill is technically overturned; V1's monotone premise holds on P2 up to a constant sign convention.",
    },
    "verdicts": {
        "W1 Morse-indexed gradient response": "premise holds (index 1 stable, near-integrable) but constant output reflection makes it monotone -> genuine structure simpler than Morse machinery; over-machinery",
        "W2 saddle inverse": "premise dissolved (not a genuine saddle)",
        "W3 degree atlas": "degree stably -1, locally invertible -> certificate trivial",
        "W4 polar factorization": "premise dissolved (near-integrable + constant-reflection monotone)",
        "W5 signature rectification": "CONFIRMED as fact correction (constant S0 works) -> sign convention, not novel (as GPT predicted)",
        "W6 Morse-degree continuation": "built on dissolved saddle premise",
    },
    "round6_outcome": "no new route; but a significant fact correction and a cleaner two-platform characterization",
    "corrected_fact_base": "Both platforms have monotone (P2 up to a fixed output-axis reflection), near-integrable, locally invertible control-response operators.",
    "user_directive": "validate + feedback only, do not invent new routes",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-W-ROUTES-001",
      "title": "GPT 第六轮 W1-W6 验证：T6-0 审计点成立，第五轮鞍点结论被修正；无新路线", "status": "complete",
      "payload": val_payload}, "tC0-wroutes")

exp_payload = {
    "document": ".project-log/docs/phase2_gpt_w_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scripts": ["V_T6.py"],
    "P2_T6_0_signature": {"pd_symJ": 0.0, "pd_symS0J_constant_diag(-1,1)": 0.99667,
                          "pd_symScJ_adaptive": 0.99778, "n": 900},
    "P2_T6_1_inertia": {"(1,1,0)_index1": 899, "(0,2,0)": 1, "(2,0,0)": 0,
                        "eigenframe_circ_std_deg": 3.16},
    "P2_T6_2_orientation": {"det_pos_frac": 0.00222, "det_neg_frac": 0.99778,
                            "sigma_min_median": 9.8e-4},
    "P2_T6_3_integrability": {"potential_gradient_val_rmse": 0.01881, "unrestricted_vector_val_rmse": 0.01957},
    "interpretation": "P2 response is near-integrable, stable Morse index 1, locally invertible, and monotone under a CONSTANT output reflection S0=diag(-1,1); the 'saddle' is a fixed output-orientation convention.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-W-EXPERIMENTS-001",
      "title": "W 轮 T6-0/1/2/3：常数输出反射使 P2 单调(99.67%)、index1 稳定、势模型不损精度", "status": "complete",
      "payload": exp_payload}, "tC1-wexp")

covers = {"files": [".project-log/docs/phase2_gpt_w_routes_validation_v1.md",
                    ".project-log/docs/phase2_gpt_handoff_v7.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_wroutes.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-GPT-W-ROUTES-001", "--kind", "research",
                    "--subject", "GPT round-6 W1-W6 validation + round-5 correction",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tC2-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "已推进 GPT 第六轮 W1–W6（Morse/拓扑度/鞍型响应）报告：完成 Gate-0 数学审计（T6-0）+ T6-1/2/3，产出 phase2_gpt_w_routes_validation_v1.md 与独立交接稿 phase2_gpt_handoff_v7.md。"
    "关键：GPT 的 T6-0 审计点成立——我方第五轮把'符号翻转'写成双侧共轭 SJS，而只改输出坐标时 Jacobian 是 SJ；实测常数输出反射 S0=diag(-1,1) 即把 P2 局部响应正定率从 0% 提到 99.67%（自适应 S(c) 仅 99.78%）。"
    "故 P2 的'鞍点'是固定输出取向的记号约定，不是不可单调化的鞍 obstruction；第五轮 V1 的技术结论被修正（P2 差一个常数符号约定即单调）。"
    "T6-1 inertia (1,1,0) 899/900、特征架旋转仅 3.16°；T6-2 det<0 99.78%、σ_min>0；T6-3 势梯度模型 val RMSE 0.01881 vs 向量 0.01957（近可积、势模型不损精度）。"
    "判决：W5 证实（常数 S0 即可，属事实修正非贡献）；W1 前提成立但常数反射即可单调化 → 真结构比 Morse 更简单，过度机械；W2/W4 前提消解；W3 degree 恒 −1 平凡；W6 建立在被消解的鞍前提上。第六轮无新路线，但修正了事实库。"
    "修正后事实：两平台均有'单调（P2 差固定输出反射）+ 近可积 + 局部可逆 + 低歧义'的控制响应；核心仍是单调响应+逆控制（被经典文献占据）。"
    "下一步：等待 GPT 依据交接稿 v7 回答决定性问题（在已被完全刻画且被经典机制覆盖的结构上是否还有非经典、无需新传感的机制级路线）；若答无，团队倾向转 A′（统一可逆控制响应几何表征论文）或 C（改变可观测量）。GOAL-001 门禁仍拒绝；DEC-018 未满足；代码/配置/论文冻结。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tC3-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tC4-handoff")
print("val_sha:", sha(VAL))
print("ho_sha:", sha(HO))
print("revision:", revision())
