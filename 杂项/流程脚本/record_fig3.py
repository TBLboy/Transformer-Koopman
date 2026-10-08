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
    print(">>>", " ".join(args)[:200])
    p = subprocess.run([PY, VIBE, "--root", ROOT] + args,
                       capture_output=True, text=True, encoding="utf-8")
    print(p.stdout)
    if p.stderr:
        print("STDERR:", p.stderr)
    return p.returncode


payload = {
    "artifact": "Transformer-Koopman/论文/新版本/pictures/Figure_mechanism.pdf",
    "artifact_sha256": "f1e9e1d38b38fce5282df2d7d50e2bea62a185db44c177802429113b48e760e1",
    "source_script": r"C:\Users\12187\AppData\Local\Temp\opencode\plot_mechanism_v2.py",
    "data_source": "gate16_diag_fix.json (stride-4 d_M and transition-product norms, consistent with the Table I footnote)",
    "defects_fixed": [
        "y-axis label 'Normalized value (divided by value at H = 1)' was ~2.5 in long, i.e. longer than the 2.5 in figure height -> it was clipped at the top in the compiled PDF; shortened to 'Normalized value' (the normalization is already stated in the caption)",
        "at H = 1 all three curves equal 1.00, so three '1.00' labels were stacked on the same point; replaced with a single shared '1.00' label",
        "the blue '1.19' label at H = 5 was clipped below the axes; ylim lowered to 0.15 and label offsets made consistent (blue below its curve, red/green above)",
        "figure saved with bbox_inches='tight' so no text can be clipped",
    ],
    "values_unchanged": {
        "prod_norm": [1.0, 1.192, 1.474, 2.204],
        "dM_norm": [1.0, 3.242, 4.768, 7.712],
        "ex_norm": [1.0, 2.058, 2.761, 3.888],
    },
    "recompiled": "Transformer-Koopman/论文/新版本/build_v2/Main.pdf (300624 bytes, 12 pages, sha256 69489d0b...)",
    "canonical_build_note": "build/Main.pdf could not be overwritten because it is open in a PDF viewer (os error 32); build_v2 is the current review copy",
    "verdict": "PASS: figure renders cleanly in the single-column layout; no clipping, no overlapping labels; data values unchanged",
}
pfile = os.path.join(TMP, "fig3_payload.json")
write_json(pfile, payload)

covers = {
    "files": [
        "Transformer-Koopman/论文/新版本/pictures/Figure_mechanism.pdf",
        "Transformer-Koopman/论文/新版本/build_v2/Main.pdf",
        "Transformer-Koopman/论文/新版本/Main.tex",
    ],
    "requirements": [],
    "tasks": ["TASK-006"],
}
cfile = os.path.join(TMP, "fig3_covers.json")
write_json(cfile, covers)

next_action = (
    "TASK-006（论文新版本，strict）进行中。"
    "**目标**：论文理论部分的文字内容（含证明/定理/参考文献）；实验与绘图暂停；与 GPT 迭代。"
    "**理论文本 FROZEN（第二十轮）**；**P3 LaTeX 编译已完成**（PHASE2-LATEX-COMPILE-001，Tectonic 0.17.0）。"
    "**本轮修复 Figure 3（PHASE2-FIG3-FIX-001 / EV-PHASE2-FIG3-FIX-001）**：用户指出图 3 纵轴标题超限且标签重叠。"
    "根因：(1) y 轴标题字符串约 2.5 in，长于 2.5 in 的图高 → 被裁切；改为 \"Normalized value\"（归一化已在 caption 说明）。"
    "(2) H=1 三曲线均为 1.00 → 三个 \"1.00\" 标签叠在同一位置；改为单个共享 \"1.00\"。"
    "(3) H=5 蓝色 \"1.19\" 被坐标轴裁切；ylim 降到 0.15，并统一偏移（蓝在下、红/绿在上）。"
    "(4) 用 bbox_inches='tight' 保存杜绝裁切。数值未变（prod 1.00/1.19/1.47/2.20；d_M 1.00/3.24/4.77/7.71；e_x 1.00/2.06/2.76/3.89）。"
    "**重新编译**：`论文/新版本/build_v2/Main.pdf`（300624 字节，12 页）已含新图，逐页核对通过；"
    "**注意**：canonical `build/Main.pdf` 因被 PDF 阅读器占用（os error 32）未能覆盖，build_v2 为当前审阅副本。"
    "**遗留（非理论 Gate）**：(a) 全文旧稿修订颜色标记（\\textcolor{red}×20、\\textcolor{blue}×5、\\color{red}×10）待用户审阅后决定；"
    "(b) 待训练 P=8 最终模型并重导部署资产（DEC-028）；(c) Experiments/Results/Discussion（§VII 空标题）、图 1–2 适配、中英转换。"
    "**下一步**：用户关闭旧 PDF 后我重建 canonical build/；用户审阅 build_v2 PDF → 依 GPT §24 优先级推进。"
)

steps = [
    ["task", "resume", "--task-id", "TASK-006", "--next-action", next_action],
    ["record", "create", "--kind", "research", "--id", "PHASE2-FIG3-FIX-001",
     "--title", "Figure 3 fix: y-axis label clipping + overlapping data labels; figure rebuilt and paper recompiled",
     "--status", "complete", "--payload", "@" + pfile],
    ["evidence", "record", "--id", "EV-PHASE2-FIG3-FIX-001", "--kind", "research",
     "--subject", "Figure 3 rebuild: no clipping, no overlapping labels; data values unchanged",
     "--status", "valid", "--task-id", "TASK-006", "--covers", "@" + cfile],
    ["task", "handoff", "--task-id", "TASK-006", "--next-action", next_action],
]

for s in steps:
    rc = run(s)
    if rc != 0:
        print("STEP FAILED rc=", rc)
        sys.exit(rc)
print("ALL DONE")
