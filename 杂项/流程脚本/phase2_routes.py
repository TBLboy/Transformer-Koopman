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
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(),
           "action": action, "payload": payload}
    p = f"{TMP}/env_{tag}.json"
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(env, ensure_ascii=False, indent=2))
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", p], capture_output=True)
    ok = r.returncode == 0
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:400]))


DEC = {
    "id": "DEC-015",
    "title": "阶段② 理论重构的约束与目标定位",
    "status": "accepted",
    "decision": (
        "阶段② 聚焦论文理论路线重构（建模 + 控制器），代码冻结。"
        "自由度：保留 Koopman 框架，建模（lifting 方式）与控制器（控制律/分析）均可重新设计。"
        "目标定位：机器人/应用期刊（RA-L / T-RO / 会议）——理论够用即可，重创新与实验验证，"
        "控制器要有实用保证。"
    ),
    "rationale": "用户明确：论文与代码均非最终版，不再纠结二者对齐；核心问题是创新点不够、理论强度不足，控制器尤甚。",
    "alternatives": [
        "保留核心只强化理论（被否：自由度不足）",
        "完全开放可换核心（被否：保留 Koopman 积累）",
        "控制顶刊 TAC/Automatica（被否：目标为机器人/应用期刊）",
    ],
}

ROUTES = {
    "key_asset": (
        "z=[x;h]，x 精确可读出（C=[I 0]）。建模误差 w_k=z_{k+1}-(Az_k+Bu_k) 可分解为："
        "w_k^x=x_{k+1}-(A_x z_k+B_x u_k)（物理残差，在线可测，因 x_{k+1} 可观测）；"
        "w_k^h=h_{k+1}-(A_h z_k+B_h u_k)（latent 残差，不可测）。"
        "这是与主流 Koopman（全状态升维、无精确物理读出）的本质区别，也是被现有论文浪费的资产。"
    ),
    "modeling_routes": [
        {"id": "M1", "name": "延迟嵌入充分性（Takens）", "idea": "有限历史窗口何时是 Koopman 演化的充分统计量",
         "novelty": 2, "theory": 3, "provable": 4, "fit": 4, "robotics": 3, "experiment": 3},
        {"id": "M2", "name": "有限维近似误差界", "idea": "P,p,d 与 Koopman 谱的关系",
         "novelty": 3, "theory": 4, "provable": 3, "fit": 4, "robotics": 3, "experiment": 3},
        {"id": "M3", "name": "三段估计收敛性/样本复杂度", "idea": "Stage 0/1/2 的一致性",
         "novelty": 2, "theory": 4, "provable": 3, "fit": 3, "robotics": 2, "experiment": 3},
        {"id": "M4", "name": "结构化 lifting（物理精确读出 + latent 残差）", "idea": "把 lifting 重构为物理块 + 残差块，给出 latent 维数需求",
         "novelty": 4, "theory": 4, "provable": 3, "fit": 5, "robotics": 4, "experiment": 4},
        {"id": "M5", "name": "残差学习（w_k 建模为 z,u 的函数）", "idea": "把建模误差从『有界』升级为『可学习结构』",
         "novelty": 4, "theory": 3, "provable": 3, "fit": 4, "robotics": 4, "experiment": 4},
    ],
    "controller_routes": [
        {"id": "C1", "name": "结构感知 LQR", "idea": "利用 x=Cz 直接界物理跟踪误差",
         "novelty": 3, "theory": 3, "provable": 4, "fit": 5, "robotics": 4, "experiment": 4},
        {"id": "C2", "name": "可测物理残差驱动的扰动抑制/积分控制", "idea": "用在线可测 w_k^x 做扰动抑制，用 w_k^h 界给认证界",
         "novelty": 5, "theory": 4, "provable": 4, "fit": 5, "robotics": 5, "experiment": 4},
        {"id": "C3", "name": "有限样本认证控制", "idea": "EDMD 残差 -> 高概率闭环界",
         "novelty": 4, "theory": 5, "provable": 3, "fit": 4, "robotics": 4, "experiment": 3},
        {"id": "C4", "name": "安全关键控制（物理 CBF + latent 误差有界扰动）", "idea": "物理状态前向不变性保证",
         "novelty": 4, "theory": 4, "provable": 4, "fit": 4, "robotics": 5, "experiment": 4},
        {"id": "C5", "name": "两时间尺度分层控制 + 分离原理", "idea": "形式化 hierarchical 结构",
         "novelty": 4, "theory": 4, "provable": 2, "fit": 3, "robotics": 3, "experiment": 3},
        {"id": "C6", "name": "在线自适应 Koopman", "idea": "用可测物理残差在线更新 A,B",
         "novelty": 4, "theory": 4, "provable": 3, "fit": 5, "robotics": 4, "experiment": 4},
        {"id": "C7", "name": "Conformal Koopman 控制", "idea": "分布无关有限样本误差界 -> 认证控制",
         "novelty": 5, "theory": 4, "provable": 4, "fit": 4, "robotics": 5, "experiment": 4},
    ],
    "screening": {
        "eliminated": [
            {"id": "M1", "reason": "Takens/延迟嵌入已成熟，创新低"},
            {"id": "M3", "reason": "增量式收敛性分析，机器人相关性低"},
            {"id": "C5", "reason": "可证性低（分离原理难证），与 Koopman 核心契合度低"},
        ],
        "kept": ["M4", "M5", "C1", "C2", "C3", "C4", "C6", "C7"],
    },
    "recommended": {
        "main": "M4 + C2",
        "name": "可测物理残差驱动的认证 Koopman 控制",
        "story": (
            "结构化 lifting（物理精确读出 + latent 残差）把建模误差分解为可测物理残差与不可测 latent 残差；"
            "控制器用可测物理残差做扰动抑制/积分控制，用 latent 残差界给物理跟踪误差的认证界。"
        ),
        "theory": "物理跟踪误差认证界 + 可测/不可测误差分离；可选 tube 形式（tube 在 latent 空间，保证在物理状态）。",
        "robotics": "扰动抑制、安全、实时。",
        "reinforcement": "C7（Conformal）作为理论强化模块，给 M4+C2 提供分布无关有限样本界。",
        "application": "C4（安全关键控制）作为应用场景。",
    },
}

print("== DEC-015 ==")
apply("record.create", {"kind": "decision", "id": "DEC-015", "title": DEC["title"],
                        "status": "accepted", "payload": DEC}, "t38-dec015", "DEC-015")

print("\n== PHASE2-ROUTES-001 ==")
apply("record.create", {"kind": "research", "id": "PHASE2-ROUTES-001",
                        "title": "阶段② 理论路线候选与筛选（建模 + 控制器）",
                        "status": "complete", "payload": ROUTES}, "t38-routes", "PHASE2-ROUTES-001")

print("\nfinal revision:", revision())
