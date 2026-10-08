import io
src = r"D:\Project\Transformer-Koopman\.project-log\docs\phase2_gpt_handoff_v11.md"
dst = r"C:\Users\12187\Desktop\GPT讨论_阶段②_第十三轮_Gate13结果_2026-10-06.md"
s = io.open(src, "r", encoding="utf-8").read()
hdr = ("<!-- 阶段③ 交 GPT 讨论文件：第十三轮 Gate-13 结果（关键负结果：开环传播失效） -->\n"
       "<!-- 由 vibe-main 生成 2026-10-06；内容与 .project-log/docs/phase2_gpt_handoff_v11.md 一致 -->\n\n")
io.open(dst, "w", encoding="utf-8", newline="").write(hdr + s)
print("wrote", dst, len(hdr + s), "chars")
