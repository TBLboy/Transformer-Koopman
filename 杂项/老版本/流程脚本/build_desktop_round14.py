import io
src = r"D:\Project\Transformer-Koopman\.project-log\docs\phase2_gpt_handoff_v12.md"
dst = r"C:\Users\12187\Desktop\GPT讨论_阶段③_第十四轮_Gate14结果_2026-10-06.md"
s = io.open(src, "r", encoding="utf-8").read()
hdr = ("<!-- 阶段③ 交 GPT 讨论文件：第十四轮 Gate-14 结果（含两个关键负结果） -->\n"
       "<!-- 由 vibe-main 生成 2026-10-06；内容与 .project-log/docs/phase2_gpt_handoff_v12.md 一致 -->\n\n")
io.open(dst, "w", encoding="utf-8", newline="").write(hdr + s)
print("wrote", dst, len(hdr + s), "chars")
