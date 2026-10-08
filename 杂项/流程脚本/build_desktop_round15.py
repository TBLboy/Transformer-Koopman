import io
src = r"D:\Project\Transformer-Koopman\.project-log\docs\phase2_gpt_handoff_v13.md"
dst = r"C:\Users\12187\Desktop\GPT讨论_阶段③_第十五轮_Gate14D结果_2026-10-06.md"
s = io.open(src, "r", encoding="utf-8").read()
hdr = ("<!-- 阶段③ 交 GPT 讨论文件：第十五轮 Gate-14D RTI 实时性结果（§23 表 + GO/NO-GO） -->\n"
       "<!-- 由 vibe-main 生成 2026-10-06；内容与 .project-log/docs/phase2_gpt_handoff_v13.md 一致 -->\n\n")
io.open(dst, "w", encoding="utf-8", newline="").write(hdr + s)
print("wrote", dst, len(hdr + s), "chars")
