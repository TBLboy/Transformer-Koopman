import json, subprocess, sys, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
VAL = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_round10_routeA_validation_v1.md"
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
    "document": ".project-log/docs/phase2_gpt_round10_routeA_validation_v1.md",
    "document_sha256": sha(VAL),
    "scope": "GPT round-10 Route A (HC-LRK-RCMPC) core modeling gate (A-Gate 1) validation on existing P2 data",
    "method": "observation-space proxy: noctx vs additive-context vs low-rank-operator-modulation; self-consistent free-running rollout H=1/5/10/20",
    "result": {
        "one_step_val_rmse": {"noctx": 0.1168, "add": 0.0365, "mult": 0.0271},
        "rollout_val_rmse_H1_5_10_20": {"noctx": [0.165, 0.505, 0.697, 0.982],
                                        "add": [0.051, 0.285, 0.761, 1.471],
                                        "mult": [0.035, 0.180, 0.369, 0.605]},
        "mult_vs_noctx_pct": [79.0, 64.4, 47.1, 38.4],
        "mult_vs_add_pct": [32.5, 36.8, 51.5, 58.9],
    },
    "verdict": "A-Gate 1 PASSES strongly: history/context is highly informative; low-rank OPERATOR modulation beats additive context increasingly with horizon; additive diverges at H>=10 while modulation stays stable.",
    "prior_art_spotcheck": "arXiv:2606.23957 (AFT-Koopman, latent memory + dynamic re-encoding) real -> Route C core occupied; arXiv:2505.00354 (Deep Koopman MPC soft robot) real -> occupied. GPT literature map accurate.",
    "constraint_conflicts": [
        "Round-10 explicitly lowers novelty bar -> conflicts with strict reading of DEC-021 (controller innovation primary).",
        "Requires re-collection of P2 data + real hardware closed-loop (Phase 3) -> needs clarification vs code/paper freeze and DEC-022 (no new observations; same-observation re-collection is not new sensors but is a scope change).",
        "This validation is an observation-space proxy, not the full latent Transformer-Koopman pipeline.",
        "Controller part (response corrector = constant-gain response feedback) is consistent with Z0 (constant gain minimax-optimal) -> low risk.",
    ],
    "preliminary": "Technically viable; publication at tier-2/tier-3 engineering venue plausible. GO/NO-GO depends on user C-level decision (relax novelty target; enter Phase 3 hardware/re-collection).",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-ROUND10-ROUTEA-001",
      "title": "第十轮路线 A 核心 gate 验证：A-Gate 1 大幅通过（低秩算子调制优于加法 context 33-59%）", "status": "complete",
      "payload": val_payload}, "tR0-routeA")

exp_payload = {
    "document": ".project-log/docs/phase2_gpt_round10_routeA_validation_v1.md",
    "document_sha256": sha(VAL),
    "scripts": ["V_A_GATE2.py", "V_A_GATE3.py"],
    "P2_self_consistent_rollout": {
        "mult_lowrank_r3": {"H1": 0.0346, "H5": 0.1799, "H10": 0.3691, "H20": 0.6051},
        "additive_context": {"H1": 0.0514, "H5": 0.2848, "H10": 0.7605, "H20": 1.4706},
        "noctx": {"H1": 0.1647, "H5": 0.5048, "H10": 0.6972, "H20": 0.9820},
    },
    "interpretation": "History context is highly predictive; multiplicative low-rank operator modulation dominates additive context and remains stable at long horizon. Supports Route A modeling premise.",
}
apply("record.create", {"kind": "research", "id": "PHASE2-ROUNDA-EXPERIMENTS-001",
      "title": "路线 A 建模 gate 实验：低秩 context 调制 vs 加法 vs 无 context 的自洽多步 rollout", "status": "complete",
      "payload": exp_payload}, "tR1-routeAexp")

covers = {"files": [".project-log/docs/phase2_gpt_round10_routeA_validation_v1.md"],
          "requirements": [], "tasks": ["TASK-004"]}
cpath = f"{TMP}/covers_routeA.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-ROUND10-ROUTEA-001", "--kind", "research",
                    "--subject", "Round-10 Route A core modeling gate (A-Gate 1) validation",
                    "--status", "valid", "--task-id", "TASK-004", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tR2-evidence")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:600]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "第十轮（GPT 务实转向 v1.0）验证：对首选路线 A（History-Conditioned Low-Rank Koopman + Response-Corrected MPC）做核心建模 gate（A-Gate 1）。"
    "在现有 P2 数据上用观测空间代理做自洽多步 rollout：noctx `(u,x)` / 加法 context `(u,x,φ)` / 低秩算子调制 `J(φ)u+W[x;φ]+b`(r=3)。"
    "结果：mult vs noctx 在 H=1/5/10/20 分别改善 79%/64%/47%/38%；mult vs add 改善 33%/37%/52%/59%（且加法式在 H≥10 开环发散，调制式全程稳定）。→ A-Gate 1（门槛 10–15%）大幅通过，路线 A 的核心假设（history 应调制算子而非只构造 state）在现有数据上成立。"
    "prior-art 抽查：2606.23957（AFT-Koopman，latent memory + dynamic re-encoding）真实→路线 C 核心被占；2505.00354（Deep Koopman MPC 软体机器人真机）真实→占位。GPT 文献图准确。"
    "产出 phase2_gpt_round10_routeA_validation_v1.md；记录 PHASE2-GPT-ROUND10-ROUTEA-001 / PHASE2-ROUNDA-EXPERIMENTS-001 / EV-PHASE2-ROUND10-ROUTEA-001。"
    "待用户裁定的 C 级问题：(1) 第十轮主动下调 novelty 门槛，与 DEC-021（控制器创新为首要）冲突，需更新其解读；(2) 路线 A 依赖重采 P2 数据 + 真机闭环（阶段③），与代码/论文冻结及 DEC-022（禁止新增观测——重采相同观测非新传感器，但仍是显著范围变化）的边界需澄清；(3) 本验证为观测空间代理，需阶段③用真实 pipeline 复现。"
    "初步判决：技术上可行，二区/三区工程论文可期；是否推进取决于用户拍板。GOAL-001 门禁仍拒绝；代码/配置/论文冻结。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "tR3-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "tR4-handoff")
print("val_sha:", sha(VAL))
print("revision:", revision())
