import io
src = r"D:\Project\Transformer-Koopman\.project-log\docs\phase2_gpt_handoff_v15.md"
dst = r"C:\Users\12187\Desktop\GPT讨论_阶段③_第十七轮_理论章节v2.1与数字修正_2026-10-06.md"
s = io.open(src, "r", encoding="utf-8").read()
hdr = ("<!-- 阶段③ 交 GPT 讨论文件：第十七轮回应——理论章节 v2.1 完成 + 数字修正说明（重要） -->\n"
       "<!-- 由 vibe-main 生成 2026-10-06；内容与 .project-log/docs/phase2_gpt_handoff_v15.md 一致 -->\n\n")
io.open(dst, "w", encoding="utf-8", newline="").write(hdr + s)
print("wrote", dst, len(hdr + s), "chars")
