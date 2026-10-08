# -*- coding: utf-8 -*-
"""Resume + handoff TASK-006 with the post-v3 next_action (avoids PowerShell arg quoting)."""
import subprocess
import sys
from pathlib import Path

VIBE_PY = Path(r"C:\Users\12187\.config\opencode\vibe-python").read_text(encoding="utf-8").strip()
CLI = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"

NA = (
    "TASK-006（论文新版本, strict）进行中。**FRONT MATTER 已冻结**；**Section III 已重构**；"
    "**理论部分已收口**；**一致性核查已收口**；**符号/排版缺陷修复完成（DEC-036）**；"
    "**叙事链重构 v1 P0（DEC-037）+ v2 P1/P2（DEC-038）已落地**；"
    "**v3 密度/防御性压缩已完成（DEC-039；EV-PHASE2-COMPRESSION-V3-001 valid；"
    "EV-PHASE2-NARRATIVE-V2-001 已置 stale）**。"
    "v3 已落实 20 处：Related Work 由四小节压回三小节（History-Based Koopman Representation / "
    "Context-Dependent Koopman Dynamics and Recursive Prediction / Real-Time Predictive Control，"
    "原独立 Recursive Multi-Step Deployment 并入 B）；III-A 结尾压成一句 bridge、删 EDMD 伪逆回归式；"
    "III-B 删 R1/R2/R3 显式标签改自然段、length-H 段移入 Training（改写为 H_R，顺带解决 H/H_R 重复）；"
    "§IV opening 压成一句；§IV-A 改名 Temporal Lifting and History-Conditioned Transition、"
    "context/lifting 解释压成一句、Definition 内只留正式定义（解读移到 Definition 之后）、"
    "删 not-an-exact-invariant-subspace-operator / not-fixed-LTI 负向表述；§IV-B 删谱稳定化讨论、"
    "压缩 L_R 防御段；§IV-C Modeling Error 缩短；Eq.(1) non-Markov 说明压缩。"
    "**关键偏离（已向用户报告）**：v3 #7/#18 若照删会移除早先理论审阅要求的免责声明 → 已**搬迁**到 "
    "§V scope Remark（minimizing it is not claimed to imply any bound on epsilon_k, d_M(H), or L_F），"
    "未删除；length-H 段虽曾被用户标注为暂缓勿再提，但 v3 从 training 细节归属角度重提，故按 v3 处理。"
    "当前产物 Main.tex sha256 **76FEEE60FD5D (77220 B)**、build/Main.pdf sha256 **45A5585C89C1 (291282 B)**、"
    "**11 页（由 12 页压缩而来）**、0 undefined citation/reference、0 overfull、underfull 8"
    "（含 page 5 一处 Underfull vbox badness 10000，系 12→11 重排的列填充 cosmetic 现象，"
    "page 5 已目视确认版面无明显空隙）。"
    "防御性表达扫描：we do not claim / deliberately / not claimed 各 1，全部位于 §V scope Remark；Abstract 214 词。"
    "**遗留（低优先）**：Abstract 214 词（略高于早先 190-210 建议）；underfull hbox 5533（§VI-B）与 6110（参考文献）；"
    "page 5 vbox；超参数取值归属 §VII 超参数表（P1-11）；Fig.1 需重绘为 representation path + "
    "transition-scheduling path 两条线并改 caption 为 conditional-linear lifted dynamics。"
    "**下一步候选（均需用户启动）**：§VII 实验章节（DEC-025 暂缓；落地后需回头让 §VII 四元合取句引用具体结果、"
    "并把 A-modulation 经验证据接到叙事上）、中英转换、Fig.1/Fig.2（用户：最后统一处理）、TASK-007（P=8 重训）。"
)


def run(*args):
    r = subprocess.run([VIBE_PY, CLI, "--root", ROOT] + list(args),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("$ vibe", " ".join(a if len(a) < 40 else a[:37] + "..." for a in args))
    print("  exit=%d" % r.returncode)
    out = (r.stdout or "") + (r.stderr or "")
    for line in out.splitlines():
        if any(k in line for k in ('"status"', '"action"', '"revision"', "error", "Error", "Traceback")):
            print("  " + line.strip())
    return r.returncode


rc1 = run("task", "resume", "--task-id", "TASK-006", "--next-action", NA)
rc2 = run("task", "handoff", "--task-id", "TASK-006", "--next-action", NA)
sys.exit(0 if (rc1 == 0 and rc2 == 0) else 1)
