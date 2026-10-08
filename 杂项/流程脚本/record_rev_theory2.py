import json, subprocess
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

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

apply("review.record", {"id": "REV-THEORY-002", "task_id": "TASK-005", "reviewer": "verification-reviewer",
      "verdict": "go",
      "scope": {"artifact": ".project-log/docs/paper_theory_section_v2.md",
                "type": "targeted re-verification after REV-THEORY-001 (conditional)",
                "high_items_closed": ["P mismatch", "bound/actual metric mismatch", "Cor.1 L_F object", "Prop.3 diagnostic"],
                "verdict_detail": "PASS with minor fixes; all 4 HIGH closed and independently re-computed; no mathematical claim broken",
                "minor_fixes_applied": ["N1 bind eps q90/q99 to source", "N2 stop calling the P=8 diagnostic model the deployment predictor", "N3 relabel the oracle-vs-RTI row"],
                "recommendation": "raise REV-THEORY-001 to go for the theory-section content"},
      "evidence_refs": ["EV-PHASE2-THEORY-SECTION-003"]}, "tW1-rev002")
print("revision:", revision())
