from pathlib import Path
ROOT = Path(r"D:\Project\Transformer-Koopman")
D = ROOT / ".project-log" / "docs"
DESK = Path(r"C:\Users\12187\Desktop")
enc = "utf-8"
r = lambda p: Path(p).read_text(encoding=enc)

header = r(r"C:\Users\12187\AppData\Local\Temp\opencode\delivery_header.md") if Path(r"C:\Users\12187\AppData\Local\Temp\opencode\delivery_header.md").exists() else ""

handoff = r(D / "phase2_gpt_handoff_v9b.md")
valid = r(D / "phase2_gpt_y_routes_validation_v1.md")

head = (
    "# GPT 交付 —— 阶段② 第九轮请求（禁止新增观测）\n\n"
    "- 说明：本文件包含两部分：**第一部分**=致 GPT 的第九轮交接稿 v9b（独立可读）；"
    "**第二部分**=第八轮 Y1–Y6 的本地验证报告（证据）。\n"
    "- 结论摘要：第八轮 0/6 通过门禁 v0.3（Y3 实验被否；Y2 被 2606.26188 占位；Y1 重包装）。\n"
    "- **用户裁定**：控制器设计不得以新增观测为前提；第九轮必须在现有观测内给出路线，或给出严谨的不可能性论证。\n\n"
    "---\n\n# 第一部分：第九轮交接稿（v9b，禁止新增观测）\n\n"
)
mid = "\n\n---\n\n# 第二部分：第八轮 Y1–Y6 验证报告\n\n"
out = head + handoff + mid + valid
dst = DESK / "GPT交付_阶段②_第九轮_控制器_禁止新增观测_2026-10-05.md"
with open(dst, "w", encoding=enc, newline="\n") as f:
    f.write(out)
print("written:", dst, len(out), "chars")
