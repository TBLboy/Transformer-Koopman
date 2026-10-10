# -*- coding: utf-8 -*-
import json, subprocess, sys, os

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"


def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def run(args):
    print(">>>", " ".join(args))
    p = subprocess.run([PY, VIBE, "--root", ROOT] + args,
                       capture_output=True, text=True, encoding="utf-8")
    print(p.stdout)
    if p.stderr:
        print("STDERR:", p.stderr)
    return p.returncode


payload = {
    "compiler": "Tectonic 0.17.0 (x86_64-pc-windows-msvc)",
    "compiler_path": r"C:\Users\12187\AppData\Local\Temp\opencode\tectonic\tectonic.exe",
    "command": "tectonic --keep-logs --outdir build Main.tex (workdir=Transformer-Koopman/论文/新版本)",
    "artifact": "Transformer-Koopman/论文/新版本/Main.tex",
    "artifact_sha256": "d05220a24ce43733f0fefabf12e1f9ec80954532a2a11c6ee9b341762d13836b",
    "output_pdf": "Transformer-Koopman/论文/新版本/build/Main.pdf",
    "output_pdf_sha256": "bbfe2cd701f78a89b25ac4aee7d1600dc683d4935ddc90a8913b2fee970e71cc",
    "pages": 12,
    "pdf_bytes": 301037,
    "resolves_leftover": "round-20 leftover (b): previously 'no LaTeX toolchain locally, uncompiled'",
    "compile_fixes": [
        "added undefined math macros to preamble: \\newcommand{\\vc}{\\mathbf{c}}, \\mV, \\mS",
        "Prop.2 proof -> align* (3 lines) to remove overfull hbox",
        "Thm.1 proof -> align* (4 lines) to remove overfull hbox",
        "training/deployment distribution equation -> gathered (2 lines)",
        "augmented-state equation -> gathered (2 lines)",
        "Assumption 2 quantifier moved out of the equation body",
    ],
    "remaining_warnings": {
        "overfull": "Main.tex:831 Overfull 0.86623pt (Cor.1 eq, visually negligible)",
        "underfull": "several underfull hboxes (cosmetic)",
        "fonts": "TU/ptm/* shapes undefined -> Tectonic substitutes; final IEEE submission should use the official IEEE template / full TeX Live",
    },
    "static_checks": {
        "bibitems": 50,
        "cite_keys_used": 39,
        "dangling_refs": "none",
        "env_mismatch": "none",
        "proof_blocks": "5/5",
    },
    "verdict": "PASS (typesetting QA): 12-page PDF built cleanly; theory section + diagnostics table render correctly; frozen theory text unchanged",
    "no_content_change": True,
}
pfile = os.path.join(TMP, "latex_compile_payload.json")
write_json(pfile, payload)

covers = {
    "files": [
        "Transformer-Koopman/论文/新版本/Main.tex",
        "Transformer-Koopman/论文/新版本/build/Main.pdf",
    ],
    "requirements": [],
    "tasks": ["TASK-006"],
}
cfile = os.path.join(TMP, "latex_compile_covers.json")
write_json(cfile, covers)

next_action = (
    "TASK-006（论文新版本，strict）进行中。"
    "**目标**：论文理论部分的文字内容（含证明/定理/参考文献）；实验与绘图暂停；与 GPT 迭代。"
    "**第二十轮裁定已执行**：THEORY ROUTE CLOSED / PROOF AUDIT PASS / NUMERICAL CONSISTENCY PASS / **THEORY TEXT FROZEN**。"
    "Q-A = YES（统一 stride-1 数值集）；Q-B：训练节 ẑ 语义绑定句已加（§17）。"
    "**P3 LaTeX 编译已完成（PHASE2-LATEX-COMPILE-001 / EV-PHASE2-LATEX-COMPILE-001）**："
    "本机装 Tectonic 0.17.0，成功编译 `论文/新版本/build/Main.pdf`（12 页，301037 字节）；"
    "修复未定义宏（\\vc/\\mV/\\mS）与证明 overfull（align*/gathered）；"
    "剩余仅 0.87pt overfull + 若干 underfull（外观性）与 ptm 字体替代警告；"
    "静态检查通过（39 cite/50 bibitem、环境配对、5/5 证明块）；理论文本未改内容。"
    "**遗留（非理论 Gate）**：(a) 全文仍带旧稿修订颜色标记（\\textcolor{red}×20、\\textcolor{blue}×5、\\color{red}×10，主要方法/训练节）"
    "——投稿前应移除，用户暂缓删除（\"不用\"），待其审阅 PDF 后决定；"
    "(b) P_final 配置审计已完成（P=8；部署 ckpt P=4 系旧遗留），待训练 P=8 最终模型并重导部署资产；"
    "(c) Experiments/Results/Discussion（§VII 现为空标题）、图 1–3、中英转换。"
    "**下一步**：用户审阅编译后的 PDF → 依 GPT §24 优先级推进（P3 排版 QA 已基本完成；P4 P2 真机；P5 实验章节；颜色标记清理待定）。"
)

steps = [
    ["task", "resume", "--task-id", "TASK-006", "--next-action", next_action],
    ["record", "create", "--kind", "research", "--id", "PHASE2-LATEX-COMPILE-001",
     "--title", "LaTeX typesetting QA: 12-page PDF built with Tectonic 0.17.0; undefined macros + proof overfull fixed; frozen theory text unchanged",
     "--status", "complete", "--payload", "@" + pfile],
    ["evidence", "record", "--id", "EV-PHASE2-LATEX-COMPILE-001", "--kind", "research",
     "--subject", "LaTeX compile QA: 12-page PDF built with Tectonic 0.17.0",
     "--status", "valid", "--task-id", "TASK-006", "--covers", "@" + cfile],
    ["task", "handoff", "--task-id", "TASK-006", "--next-action", next_action],
]

for s in steps:
    rc = run(s)
    if rc != 0:
        print("STEP FAILED rc=", rc)
        sys.exit(rc)
print("ALL DONE")
