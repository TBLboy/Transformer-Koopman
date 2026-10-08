import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"


def run(args, tag):
    r = subprocess.run([PY, VIBE, "--root", ROOT] + args, capture_output=True)
    ok = r.returncode == 0
    print(("OK   " if ok else "FAIL ") + tag)
    out = (r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")).strip()
    if out:
        print(out[:1500])
    return ok


covers = {
    "files": [
        ".project-log/docs/phase2_theory_construction_v0.1.md",
        ".project-log/docs/phase2_theory_construction_v0.2.md",
        ".project-log/docs/phase2_outcome_v0.1.md",
    ],
    "requirements": [],
    "tasks": ["TASK-004"],
}
with open(f"{TMP}/ev_covers.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump(covers, f, ensure_ascii=False)

subject = (
    "阶段② 组合路线理论构造：修正定理 T1'（Lyapunov 形式，去除错误的 Schur=>||A_cl||<1 推理，"
    "含前馈不可达 delta 项）+ 量化/饱和接口项 + 有效性域命题1。独立复核 C-1..C-4 CONFIRMED，"
    "判定 REVISE 后接受。脚本 sha256: s8_verify_t1.py=E46ED18554B1FA484EB1BE1BFC12D117B51075C371E33705230305E295D7AE02; "
    "s8b_p2_terms.py=C7DCA30BA6A877CF122B671F8FF43FED2098A265246A440B5F1B1B2F7D43B823"
)

run(["evidence", "record", "--id", "EV-PHASE2-THEORY-001", "--kind", "analysis",
     "--subject", subject, "--status", "valid", "--task-id", "TASK-004",
     "--covers", f"@{TMP}/ev_covers.json"], "EV-PHASE2-THEORY-001")

scope = {
    "artifact": ".project-log/docs/phase2_theory_construction_v0.2.md",
    "sha256_v0.2": "E034C1A964B6A921F7EA220D1CC2C51B0A6B8780B8E39184EE72EEFB4BB2D8D1",
    "in_scope": "T1' 推导与常数、DARE 恒等式、误差动力学补项(P_G)、反例、假设完整性、命题1定位、物理载体一致性、novelty 表述诚实性",
    "out_of_scope": "论文正文改写、阶段③实现与重训、P1 无 checkpoint 的空白",
    "rounds": 1,
    "final_blocking_items": 0,
    "verdict_detail": "C-1..C-4 CONFIRMED (math core sound); required revisions: A1 lambda>0, T1' include A6, Theorem 2 demote to Proposition, norm/label fixes, hash-bound evidence, novelty delta pending",
    "limitation": "Reviewer could not re-run Python (policy); main agent re-ran with corrected spectral norms. Numeric claims reproduced by main agent post-correction.",
}
with open(f"{TMP}/rev_scope.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump(scope, f, ensure_ascii=False)

run(["review", "record", "--id", "REV-PHASE2-THEORY-001", "--task-id", "TASK-004",
     "--reviewer", "verification-reviewer", "--verdict", "conditional",
     "--scope", f"@{TMP}/rev_scope.json",
     "--evidence-ref", "EV-PHASE2-THEORY-001"], "REV-PHASE2-THEORY-001")
