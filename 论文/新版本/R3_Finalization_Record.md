# 最终 Main 定稿与归档记录

日期：2026-10-19。

> 本文记录最初定稿时的版本绑定，非后续编辑的当前哈希。2026-10-19 用户另行授权引言重写后，活跃Main/PDF已更新；最新来源分析、差异、编译与哈希见 `杂项/Introduction_Rewrite_Analysis_20261019.md`，本记录的旧绑定保持为历史证据。

## 定稿来源

- 用户指定的最终正文来源：`C:/Users/12187/Downloads/Main_SixSection_TheoryRewritten_R3_Refined.tex`，SHA256=`ef05c90b0d2b4d8bdb4c523c5d7b6c2117107f8e5ba563fb113ba24411bdd612`。
- 活跃 `Main.tex` 以该来源逐字写入；唯一附加内容是两段 XeTeX 条件字体兼容层：一段位于 `\documentclass` 前，另一段紧跟 `amsmath`。它们对 pdfLaTeX 无操作，避免本机 Tectonic/XeTeX 缺少 TU/ptm 和 cmss10 度量时失败；正文、公式、引用、图、文献与来源文件未变。
- 原活跃 `Main.tex`（SHA256=`1ee01187dfdad058746fe9fb3e2489c467b96de09ead0ef67be7a3f2855aee69`）归档为 `杂项/历史版本/pre-final-main/Main_pre-final_20261019.tex`，没有删除。

## 目录整理

论文目录根部只保留活跃的 `Main.tex`、`Main.pdf`、`IEEEtran.cls` 和本文档。以下均已移至 `杂项/历史版本/`：

- `pre-final-main/`：定稿前 Main；
- `r1-r3-candidates/`：R1、R2、R3 的 TeX/PDF 候选；
- `review-records/`：迁移、一致性、R2/R3修订、理论核验和作者决策记录；
- `legacy-support/`：此前图片、bibtex、build_font 和写作辅助资料。

V3 理论原件、代码、实验、checkpoint及论文目录外文件未改。归档是移动，不是删除。

## 实际编译与验证

- 使用已有 Tectonic 0.17.0，`--only-cached`，对最终 `Main.tex` 连续编译两次，退出码均为 0；最终 PDF 为 10 页。
- 两次最终日志均为：0 致命错误、0 未定义引用、0 缺字、0 字体加载失败、0 Overfull；保留 7 条 Underfull。
- 用已有 uv Python 3.11、缓存 pdfminer/pypdfium2 提取并渲染最终 10 页，主 Agent 实看第1、5、6、9、10页；框图、定理、推论、附录和文献无可见裁切/越栏。
- 静态检查通过：六章、核心小节数`[0,2,2,2,0,0]`、三附录、79 个唯一标签、72 处 `ref/eqref`、26 个引用键及对应 `bibitem`，括号与环境配对。

构建证据：`C:/Users/12187/AppData/Local/Temp/opencode/final-main-build/`。

独立 strict 复审：`ses_eaba7b750ffexnLxp22qqaCfkV` 返回 **go，findings=[]**。reviewer 只读核对最终 Main、定稿记录、Task、项目规则及目录；编译、版面、哈希及附件逐字对照结论采用主 Agent 的实际证据，未自行复编或直接读取 PDF。

## 已知限制

- 实际运行的引擎是 Tectonic/XeTeX；没有在本轮独立运行 pdfLaTeX、独立 XeLaTeX 或 LuaLaTeX。附件自身的无兼容层版本在本机 Tectonic 测试时因 TU/ptm 与 cmss10 缺失失败，因此最终仅补了上述条件兼容层。
- 环境仍有 Fontconfig 默认配置、缓存算法包 UTF-8 注释和系统 Arial 绝对路径警告；未安装依赖或更改系统字体/缓存。7 条 Underfull 未消除。
- 第 V 章仍无实验结果；这次定稿不认证当前模型、plant、求解器实时性、安全性或实验性能。

## 最终文件绑定

| 文件 | SHA256 |
|---|---|
| `Main.tex` | `6348beeff76945d8f693345f19c36d7ca1b72c3c2c49ad00de5ebba9233c57bf` |
| `Main.pdf` | `07c90a36761b28cced42080412c80bfd5e4ff0ad38428cd766cecf2488378ced` |
