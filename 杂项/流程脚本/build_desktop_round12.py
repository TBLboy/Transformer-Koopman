import io, os
src = r"D:\Project\Transformer-Koopman\.project-log\docs\phase2_gpt_handoff_v10.md"
dst = r"C:\Users\12187\Desktop\GPT讨论_阶段②_第十二轮_结构Gate结果_2026-10-06.md"
s = io.open(src, "r", encoding="utf-8").read()
hdr = ("<!-- 阶段②/③ 交 GPT 讨论文件：第十二轮 结构 Gate 结果（locus 反转：A-only） -->\n"
       "<!-- 由 vibe-main 生成 2026-10-06；内容与 .project-log/docs/phase2_gpt_handoff_v10.md 一致 -->\n\n")
io.open(dst, "w", encoding="utf-8", newline="").write(hdr + s)
print("wrote", dst, len(hdr + s), "chars")
