import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"


def revision():
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def apply(action, payload, tag, label):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(), "action": action, "payload": payload}
    path = f"{TMP}/env_{tag}.json"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path], capture_output=True)
    print(("OK   " if r.returncode == 0 else "FAIL ") + label)
    if r.returncode:
        print(r.stderr.decode("utf-8", "replace")[:1000])


payload = {
    "status": "complete",
    "source": "Crossref/OpenAlex bibliographic metadata plus project paper bibliography; primary full-text reading still pending.",
    "document": ".project-log/docs/phase2_s1_literature_mapping_v0.1.md",
    "verified_signals": [
        "Robust tube-based Koopman MPC is established: Zhang et al., Automatica 2022, DOI 10.1016/j.automatica.2021.110114.",
        "Koopman-CBF safety with error-bound robustification is established: Folkestad et al., IEEE Control Systems Letters 2021, DOI 10.1109/lcsys.2020.3046159.",
        "Neural Koopman-CBF exists: Zinage and Bakolas, ACC 2023, DOI 10.23919/acc55779.2023.10156243.",
        "Adaptive online Koopman embedding for robust robotic control is established: Singh et al., IJRR 2025, DOI 10.1177/02783649251341907.",
        "Robust dual-loop finite-dimensional Koopman control exists: Pal and He, ACC 2023, DOI 10.23919/acc55779.2023.10156006.",
        "Conformant synthesis for Koopman-linearized control systems exists: Kochdumper and Bak, CDC 2022, DOI 10.1109/cdc51059.2022.9992324.",
    ],
    "screening": {
        "killed_as_standalone": ["tube Koopman MPC", "Koopman-CBF", "generic residual/adaptive Koopman", "history/Transformer lifting alone", "bilinear Koopman alone"],
        "surviving_hypothesis": "A CCK-style structure-manufacturing route addressing lifted-reference feasibility / constant-B obstruction may remain, but is not yet validated.",
    },
    "next": "Read primary full texts for Zhang 2022, Folkestad 2021, Singh 2025, CCK source, Korda-Mezic 2018 and input-dependent Koopman; extract exact assumptions/theorems/limitations and test the reference-feasibility obstruction.",
}

apply("record.create", {"kind": "research", "id": "PHASE2-S1-001", "title": "阶段② S1 文献结构化映射 v0.1", "status": "complete", "payload": payload}, "t41-s1-record", "PHASE2-S1-001")
apply("task.handoff", {"task_id": "TASK-004", "next_action": "S1 v0.1 已完成初筛：robust tube Koopman MPC、Koopman-CBF、generic residual/adaptive Koopman、history lifting alone、bilinear Koopman alone 均不能作为单独创新。下一步 L2/L4 阅读 Zhang 2022、Folkestad 2021、Singh 2025、CCK source、Korda-Mezic 2018 与 input-dependent Koopman，抽取精确定理/假设/限制，并验证 lifted-reference feasibility / constant-B obstruction。代码继续冻结。"}, "t41-s1-handoff", "TASK-004 handoff")
print("revision:", revision())
