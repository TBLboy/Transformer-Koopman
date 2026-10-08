import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

def revision():
    p = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(p.stdout.decode("utf-8", "replace"))["revision"]

def apply(action, payload, tag):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(), "action": action, "payload": payload}
    path = f"{TMP}/env_{tag}.json"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    p = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path], capture_output=True)
    print(("OK   " if p.returncode == 0 else "FAIL ") + tag)
    if p.returncode:
        print(p.stderr.decode("utf-8", "replace")[:1500])

review_payload = {
    "document": ".project-log/docs/phase2_feedback_route_review_v0.1.md",
    "source": "用户提交的 Transformer-Koopman 理论路线头脑风暴 v0.1；两份独立 solution-researcher 审查；导出 checkpoint 数值诊断。",
    "confirmed": [
        "P2 deployed (A,B) has controllability rank 10/10; B's two columns do not imply a two-dimensional multi-step controllable subspace.",
        "For C=[I_2,0], exported checkpoint observability matrix rank is 10/10 and unstable-mode PBH ranks are all 10.",
        "The same observability matrix has condition number approximately 9.44e8; numerical detectability is therefore ill-conditioned.",
        "P2-A is materially overlapping with the existing history-window lifting unless a new control-relevant delay criterion is supplied.",
        "P2-D lacks confirmed fast variables or measurable time-scale separation in the current data contract.",
        "G-A is useful as DEC-018 stabilization engineering prerequisite but is not a center innovation by itself.",
    ],
    "candidate_or_unverified": [
        "Prior-art exclusions for P2-A/C/D and G-* are currently summary/metadata or abstract-level and require full-text delta checks before final publication claims.",
        "A2 relative-degree-preserving lifting and A7 control-relevant subspace remain candidates, not accepted routes.",
    ],
    "rejected_or_downgraded": {
        "P2-B": "kill current argument: controllability decomposition is degenerate at rank 10/10.",
        "P2-A": "baseline candidate only; explicit delay coordinates alone are not innovation.",
        "P2-C": "observability/controller baseline only; standard observer structure and ill-conditioning.",
        "P2-D": "defer pending measured fast variable or time-scale evidence.",
        "G-B": "kill as center: closed-loop identification/loss change, no real closed-loop data.",
        "G-C": "auxiliary certificate only; standard Lyapunov/CLF unless a new transfer theorem appears.",
        "G-D": "auxiliary error analysis only; no controller-structure change.",
        "G-E": "kill as center: standard disturbance/residual observer and direct neighboring prior art.",
        "G-F": "kill current form: no mode labels and standard switched Koopman prior art.",
        "G-G": "kill current form: no repeated distribution samples, real-time concern, and DRO prior art.",
    },
    "next_gate": {
        "A2": "Specify a measurable relative-degree-preservation condition from available P2 input/output histories, then test whether it differs from ordinary delay lifting and changes controller synthesis.",
        "A7": "Specify a retained/discarded subspace and a data-computable task-error bound; demonstrate a controller different from fixed full-space LQR.",
        "fallback": "If A2 and A7 fail their minimum spikes, escalate C-level decision: collect targeted data or narrow paper scope.",
    },
    "diagnostic_script": "C:/Users/12187/AppData/Local/Temp/opencode/diagnose_p2_observability.py",
    "diagnostic_result": "C:/Users/12187/AppData/Local/Temp/opencode/p2_observability_diagnostic.json",
    "a2_a7_spike": {
        "document": ".project-log/docs/phase2_a2_a7_minimal_spike_v0.1.md",
        "script": "C:/Users/12187/AppData/Local/Temp/opencode/spike_a2_a7.py",
        "a2_val_rmse_without_current_u": {"h1": 0.14823855460268187, "h2": 0.28389470702345626, "h3": 0.4019766977246135},
        "a2_val_rmse_with_current_u": {"h1": 0.11611185576589274, "h2": 0.17428789958359708, "h3": 0.19867137947037916},
        "a2_verdict": "input has measurable predictive information, but relative-degree preservation is not established",
        "a7_controllability_rank": 10,
        "a7_sigma_min_over_sigma_max": 2.0869751354865798e-7,
        "a7_verdict": "full rank but ill-conditioned; no predeclared control-relevant spectral cutoff",
    },
}
apply("record.create", {"kind": "research", "id": "PHASE2-FEEDBACK-REVIEW-001", "title": "用户反馈路线审查：P2-A/B/C/D 与 G/P1 候选", "status": "complete", "payload": review_payload}, "t53-review")

next_action = (
    "用户反馈候选已审查并记录。P2-B 的‘B两列所以可控子空间两维’论据已证伪：导出(A,B)可控秩10/10，当前分解路线kill。"
    "P2-A延迟嵌入与现有history lifting重叠，P2-C导出checkpoint数值可检测但条件数约9.44e8，均降为基线；P2-D无快变量/时间尺度证据暂缓。"
    "G-A仅作DEC-018稳定化工程前置，G-B/G-E/G-F/G-G当前kill，G-C/G-D仅作辅助。下一步只对A2 relative-degree-preserving与A7 control-relevant subspace做最小可证伪规格化；若均失败，触发补采数据或缩小论文范围的C级决策。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t53-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t53-handoff")
print("revision:", revision())
