import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

VAL = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_y_routes_validation_v1.md"
HO = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_handoff_v9.md"
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
    "document": ".project-log/docs/phase2_gpt_y_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scope": "GPT round-8 controller routes Y1-Y6 validation via C8-1 spectral bounds, C8-2/3 offline replay, L1/L2 prior-art",
    "gate": "phase2_gate_update_v0.3.md (controller-centric)",
    "verdicts": {
        "Y1 RDIC": "fail/weak - repackaging of response-space PI + inverse geometry; Bregman/mirror-descent classical",
        "Y2 PCMSF": "fail/occupied - arXiv:2606.26188 (continuum arm, Broyden secant + Kalman online Jacobian compensation) + classical resolved-rate Broyden servo",
        "Y3 CMRC/SARC": "KILLED empirically - Chebyshev gains never beat best constant gain on real time-varying response",
        "Y4 MPDRC": "KILLED - subset of Y3",
        "Y5 SARF": "fail - Anderson acceleration = numerical-acceleration transplant (gate-excluded)",
        "Y6 IPRC": "fail - proximal/resolvent classical (GPT self-labeled fallback)",
    },
    "round8_outcome": "0/6 pass gate v0.3",
    "cumulative": "Rounds 1-8 consistent: on existing observables the searchable mechanism space (modeling AND control) is exhausted (occupied or ineffective on this data).",
    "reframed_axis_needed": "Round 9 must move OUTSIDE the iterative-inverse / spectral-acceleration / online-Jacobian-adaptation family, else switch to new observable (C1/C2/C3) or characterization/falsification paper (A').",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-Y-ROUTES-001",
      "title": "GPT 第八轮 Y1-Y6 控制器路线验证：0/6 通过门禁 v0.3；Y3 实验被否，Y2 占位", "status": "complete",
      "payload": val_payload}, "tY0-yroutes")

exp_payload = {
    "document": ".project-log/docs/phase2_gpt_y_routes_validation_v1.md",
    "document_sha256": sha(VAL),
    "scripts": ["V_C8.py", "V_C8b.py", "V_C8c.py"],
    "C8_1_spectral_bounds": {
        "P1_symJ": {"mu_q05": -7.27, "L_q95": 585.2, "kappa_q": None,
                    "mu_median": 25.21, "L_median": 228.6, "kappa_median": 9.07, "frac_pd": 0.906},
        "P2_rectified_S0J": {"mu_q05": 5.5e-4, "L_q95": 6.5e-3, "kappa_q": 11.84,
                             "mu_median": 9.7e-4, "L_median": 1.61e-3, "kappa_median": 1.67, "frac_pd": 0.9967},
        "P2_unrectified": {"frac_pd": 0.0},
    },
    "C8_2_replay_wide_tight": {
        "P2_wide_kappa12.18": {"N6": {"const_med": 0.047, "cheb_med": 0.142, "cheb_better_frac": 0.235}, "oob": 0.106},
        "P2_tight_kappa1.69": {"N6": {"const_med": 0.0325, "cheb_med": 0.0436, "cheb_better_frac": 0.365}, "oob": 0.895},
        "P1_wide_kappa114.8": {"N6": {"const_med": 0.144, "cheb_med": 1.656, "cheb_better_frac": 0.023}, "oob": 0.092},
        "P1_tight_kappa8.21": {"N6": {"const_med": 0.269, "cheb_med": 1.366, "cheb_better_frac": 0.168}, "oob": 0.882},
    },
    "interpretation": "No fixed spectral interval is both tight and accurate; open-loop spectral acceleration (Chebyshev) is structurally worse than best constant gain on this time-varying signed response operator. Per-window oracle constant gain beats global constant by only ~1.25-2x.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-Y-EXPERIMENTS-001",
      "title": "C8 谱界 + 离线 replay：Y3 Chebyshev 在真实时变响应上被常数增益击败；谱信息收益上界 ~1.25-2x", "status": "complete",
      "payload": exp_payload}, "tY1-yexp")

covers = {"files": [".project-log/docs/phase2_gpt_y_routes_validation_v1.md",
                    ".project-log/docs/phase2_gpt_handoff_v9.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_yroutes.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-GPT-Y-ROUTES-001", "--kind", "research",
                    "--subject", "GPT round-8 Y1-Y6 controller route validation",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tY2-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "已推进 GPT 第八轮 Y1–Y6（控制器专项）报告：产出 phase2_gpt_y_routes_validation_v1.md 与独立交接稿 phase2_gpt_handoff_v9.md，记录 PHASE2-GPT-Y-ROUTES-001 / PHASE2-Y-EXPERIMENTS-001 / EV-PHASE2-GPT-Y-ROUTES-001。"
    "关键结论：第八轮 0/6 通过门禁 v0.3。"
    "① Y3（Chebyshev 最小极大响应控制，GPT 首推）经离线 exact-J replay 被否：在 P1/P2、N=4/6/8、wide/tight 两种谱区间下，Chebyshev 增益从未优于最优常数增益（更优占比 1.3%–37.5%）；原因是结构性的——wide 区间按构造排除约 10% 样本、tight 区间排除约 89%，Chebyshev 带外增长快。"
    "② 谱界实测：P2 整流后 κ(q05/q95)=11.8、中位 κ=1.67；P1 κ=116.8、中位 9.07、PD 90.6%；逐窗 oracle 最优常数增益相对全局常数仅快 1.25–2×，谱信息收益上界很小。"
    "③ Y2（PCMSF）被 arXiv:2606.26188（连续体臂 Broyden secant + Kalman 在线 Jacobian 补偿）与经典 resolved-rate/Broyden 伺服直接占位；Y1 为响应空间 PI+逆几何重包装；Y4 是 Y3 子集；Y5 属数值加速移植（门禁排除）；Y6 为 classic proximal。"
    "累积判断（第 1–8 轮一致）：在现有观测上，建模侧与控制器侧的『迭代逆 / 谱加速 / 在线 Jacobian 自适应』机制空间已被占位或在本数据上失效。"
    "下一步为 C 级决策（DEC-022 待定）：(a) 新增最小观测 C1/C2/C3，或 (b) A′ 表征/证伪论文（把学习到的响应几何 + 经典逆/加速控制为何失效本身作为贡献）。第九轮请求已随 v9 发出，要求 GPT 换出迭代逆/加速族或转 C。GOAL-001 门禁仍拒绝；DEC-018 未满足；代码/配置/论文冻结。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tY3-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tY4-handoff")
print("val_sha:", sha(VAL))
print("ho_sha:", sha(HO))
print("revision:", revision())
