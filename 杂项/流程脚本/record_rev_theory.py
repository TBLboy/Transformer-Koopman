import json, subprocess
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

def revision():
    p = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(p.stdout.decode("utf-8", "replace"))["revision"]

env = {"schema_version": 1, "command_id": "tX1-rev-theory", "expected_revision": revision(),
       "action": "review.record",
       "payload": {"id": "REV-THEORY-001", "task_id": "TASK-005", "reviewer": "verification-reviewer",
                   "verdict": "conditional",
                   "scope": {"artifact": ".project-log/docs/paper_theory_section_v1.md",
                             "dimensions": ["math_correctness", "evidence_binding", "overclaiming", "numeric_consistency"],
                             "core_math": "PASS",
                             "required_fixes": ["P mismatch", "bound/actual metric mismatch", "L_F object in Cor.1", "Prop.3 diagnostic invalid"],
                             "fixes_applied_in": ".project-log/docs/paper_theory_section_v2.md",
                             "note": "conditional on the 4 HIGH evidence-binding fixes, all applied in v2; re-check pending"},
                   "evidence_refs": ["EV-PHASE2-THEORY-SECTION-002"]}}
path = f"{TMP}/env_tX1-rev-theory.json"
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(env, f, ensure_ascii=False, indent=2)
p = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path], capture_output=True)
print(("OK   " if p.returncode == 0 else "FAIL ") + "tX1-rev-theory")
if p.returncode:
    print(p.stdout.decode("utf-8", "replace")[:700]); print(p.stderr.decode("utf-8", "replace")[:1200])
print("revision:", revision())
