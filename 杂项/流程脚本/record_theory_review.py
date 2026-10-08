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

findings = {
    "artifact": ".project-log/docs/paper_theory_section_v1.md",
    "reviewer": "verification-reviewer",
    "overall": "pass-with-fixes",
    "verdict_math": "core mathematics (Prop.1, Prop.2, Thm.1, Cor.1, Prop.3, Rem.1) correct and internally consistent; proofs valid; hypotheses sufficient at finite-horizon scope; no global-stability/manifold overclaim",
    "failures": "evidence binding and interpretation",
    "HIGH": [
        "P mismatch: doc said P=4, diagnostics JSON says P=8 (resolved: platform2.yaml history_length=8 is the experiment config; deployed ckpt is P=4/n_layers=3 from old experiment_006 - separate ALN-type issue)",
        "bound/actual metric mismatch: absolute epsilon vs normalized d_M (fixed: like-for-like absolute comparison 1.65-6.57x)",
        "Cor.1 used per-step product constant (~1.045) instead of augmented-map L_F=1.445 (fixed: 53-48374x, reported as extremely loose)",
        "Prop.3 diagnostic invalid: remainder noise-floor-limited at delta=1e-3; quoted M_F violated (fixed: delta^2 scaling verified, M_F~0.007)",
    ],
    "MEDIUM": [
        "S3.13 RTI row category error (fixed: Prop.3 NOT validated by oracle comparison)",
        "F* not defined on augmented space (fixed: convention stated)",
        "empirical vs certified not disclosed (fixed: assumption A4 + S3.11 item 4)",
    ],
    "LOW": ["define epsilon_0 (fixed)", "remove/define w_k (fixed: removed)", "mean-value form (fixed)", "scope Prop.1 (fixed)"],
    "fixes_applied_in": ".project-log/docs/paper_theory_section_v2.md",
}
apply("record.create", {"kind": "research", "id": "PHASE2-THEORY-SECTION-REVIEW-001",
      "title": "理论章节 v1 独立复核：数学正确，证据绑定有 4 项 HIGH 问题，已全部修订入 v2", "status": "complete",
      "payload": findings}, "tW1-theory-review")

apply("review.record", {"id": "REV-THEORY-001", "task_id": "TASK-005", "reviewer": "verification-reviewer",
      "verdict": "conditional",
      "scope": "paper_theory_section_v1.md: math correctness + evidence binding. Core math PASS; 4 HIGH evidence-binding fixes required (P mismatch, metric mismatch, L_F object, Prop.3 diagnostic). All applied in v2.",
      "evidence_refs": {"files": [".project-log/docs/paper_theory_section_v1.md",
                                  ".project-log/docs/paper_theory_section_v2.md"]}}, "tW2-rev")

# supersede v1 evidence, record v2 evidence
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "invalidate",
                    "--id", "EV-PHASE2-THEORY-SECTION-001",
                    "--reason", "superseded by v2 after independent review (4 HIGH evidence-binding fixes)"],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tW3-invalidate-v1")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:700]); print(p.stderr.decode("utf-8", "replace")[:1200])

covers = {"files": [".project-log/docs/paper_theory_section_v2.md",
                    ".project-log/docs/paper_theory_section_v1.md"],
          "requirements": [], "tasks": ["TASK-005"]}
cpath = f"{TMP}/covers_theory2.json"
with open(cpath, "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "evidence", "record",
                    "--id", "EV-PHASE2-THEORY-SECTION-002", "--kind", "research",
                    "--subject", "Paper theory section v2 (post-review)",
                    "--status", "valid", "--task-id", "TASK-005", "--covers", "@" + cpath],
                   capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tW4-evidence-v2")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:700]); print(p.stderr.decode("utf-8", "replace")[:1200])

next_action = (
    "TASK-005（论文理论章节）v2 完成（按独立复核 9 项意见修订）。**复核结论**：核心数学（Prop.1/2、Thm.1、Cor.1、Prop.3、Rem.1）正确且自洽，无全局稳定性/流形不变性过度声明；问题集中在**证据绑定**（4 项 HIGH）——已全部修订。"
    "**v2 关键修正**：(1) P 4→**8**（`platform2.yaml` history_length=8 为实验配置；部署 ckpt 为 P=4/n_layers=3 旧 experiment_006，属 ALN 类部署一致性问题，另记）；(2) bound/actual 改**同口径**（绝对 ε vs 绝对 d）→ **1.65/2.82/4.21/6.57×**（合理，取代错配的 4.7–18.7×）；(3) Cor.1 用正确 augmented-map L_F=1.445 → **53/309/1679/48374×**（极松，如实标注；取代误用 1.045 的 52–413×）；(4) Prop.3 余项重测 → δ² 标度成立、**M_F≈0.007**（取代噪声伪值 0.27）；(5) §3.13 RTI 行修正——Prop.3 **不由** oracle 对比验证；(6) 定义 F*、补 A4（经验估计 vs 认证界）、定义 ε_0、删 w_k、补中值形式、限定 Prop.1 内部 rollout。"
    "产出 `paper_theory_section_v2.md`；记录 PHASE2-THEORY-SECTION-REVIEW-001 / REV-THEORY-001（conditional）/ EV-PHASE2-THEORY-SECTION-002（v1 证据已 invalidate 为 superseded）。"
    "**下一步**：(1) v2 针对性复检（后台进行中，确认 4 项 HIGH 已闭合）→ 通过后 verdict 升 go；(2) 交 GPT 讨论理论章节；(3) 真机推迟（DEC-025）。"
)
apply("task.resume", {"task_id": "TASK-005", "next_action": next_action}, "tW5-resume")
apply("task.handoff", {"task_id": "TASK-005", "next_action": next_action}, "tW6-handoff")
print("v2_sha:", sha(V2))
print("revision:", revision())
