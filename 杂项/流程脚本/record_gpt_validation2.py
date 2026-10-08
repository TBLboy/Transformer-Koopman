import json
import subprocess
import sys
import hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

DOC = Path(ROOT) / ".project-log" / "docs" / "phase2_gpt_route_validation_addendum_r4r18_v0.1.md"
sha = hashlib.sha256(DOC.read_bytes()).hexdigest()

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

payload = {
    "document": ".project-log/docs/phase2_gpt_route_validation_addendum_r4r18_v0.1.md",
    "document_sha256": sha,
    "second_prior_art_pass_R4_R18": True,
    "residual_space_ranking": "R16 > R15 ~ R18 > R14 > R5 > R4/R7/R13 > R6/R9/R10",
    "R16": "largest remaining space: port control-sufficiency to Koopman linear latent + optimality theorem + dual-encoder; no direct Koopman precedent found",
    "strengthened_collisions": {
        "R4": "Koopman-SPC arXiv:2405.01292; Khatri-Rao multi-step arXiv:2606.02938",
        "R5": "arXiv:2509.17010 actuated/unactuated decoupling",
        "R6": "ICLR 2026 Koopman controllability Gramian regularization",
        "R9": "M_h = finite-horizon observability Gramian (classical)",
        "R10": "arXiv:2607.05718 input-Jacobian regularization",
        "R13": "Ho-Kalman/ERA; DMD=ERA equivalence",
    },
    "global_top_residual": ["R1 (unreachable residual training loss + multi-step reachable)", "R3 (residual dynamics + control theorem)", "R16 (control-sufficient Koopman dual encoder)"],
    "evidence_level": "L2/fragments; L3 not done",
    "disagreement": "R16 residual space: pass1 medium vs pass2 largest; negative search not conclusive",
    "next": "L3 full-text comparison; re-scan for goal-conditioned / control-sufficient Koopman",
}
apply("record.create", {"kind": "research", "id": "PHASE2-GPT-ROUTE-VALIDATION-002", "title": "GPT R4-R18 第二遍 prior-art：R16 残余空间最大、多条撞车坐实", "status": "complete", "payload": payload}, "t60-val2")

next_action = (
    "GPT 18 条路线验证完成（两遍 prior-art）。三项便宜测试：R1 参考不可达 ~16~21%（一阶）、R2 gauge 病理成立但属 1984 已知事实、R3 残差可预测 17~25%。"
    "prior-art（L2）：R4/R6/R9/R10/R13 换名（撞 Koopman-SPC 2405.01292、2606.02938、ICLR2026 Gramian、2607.05718、Ho-Kalman/ERA）；R5/R7/R14/R18 部分换名；R15 GCRL 双编码换名；R2 高危。"
    "全局残余空间排序：R16 > R15≈R18 > R14 > R5 > R4/R7/R13 > R6/R9/R10；结合 R1-R3 复核，残余最大三个为 R1、R3、R16。"
    "下一步：做 L3 全文对拍（2405.01292/2606.02938/2509.17010/ICLR2026-10007892/2507.19437/2601.22496/2603.17545/2607.05718/2602.14537/2311.13033/2307.15368/1709.08712/2209.08637/2402.03145），并专门再扫 goal-conditioned / control-sufficient Koopman。"
)
apply("task.resume", {"task_id": "TASK-004", "next_action": next_action}, "t60-resume")
apply("task.handoff", {"task_id": "TASK-004", "next_action": next_action}, "t60-handoff")
print("doc_sha256:", sha)
print("revision:", revision())
