# 文献检索日志（阶段二 / TASK-035）

- 日期：2026-10-11
- 授权：用户授权独立检索；明确「搜不到就直接跳过」（DEC-081 把本任务降级为尽力而为、不作为前置）
- 工具：通用 web 搜索（非学术数据库 API、非全文库）
- 交付：`Theory_Package/09_Reference_List.md`

## 1. 实际执行的检索

| # | 查询串 | 目的 | 主要回收 |
|---|---|---|---|
| Q1 | `deep Koopman operator learning for control survey` | 基础/受控 Koopman 与 Koopman-MPC 的现状 | 教程 arXiv:2607.01819（EDMD / 带输入系统 / Koopman MPC，含代码） |
| Q2 | `Hankel delay embedding Koopman model predictive control` | T1 延迟坐标 | Korda & Mezić 2018（Automatica 93, DOI `10.1016/j.automatica.2018.03.046`，arXiv:1611.03537）；HAVOK-MPC（AAU 2023，机构库稳定链接） |
| Q3 | `parameter-varying context-dependent Koopman operator MPC scheduling variable` | T4 调度 | arXiv:2309.10278（PVKO + MPC，含可行性与稳定性分析） |
| Q4 | `Transformer Koopman operator deep learning nonlinear dynamics lifting` | T3 Transformer 提升 | npj Artificial Intelligence (2026) DOI `10.1038/s44387-026-00085-3`（DeepKoopFormer）；arXiv:2602.02592（含 low-rank Koopman 参数化）；ISA Transactions 2025 PII `S0019057825001880`；arXiv:2206.01272（KDNN + 电网 MPC）；Nature Communications 9 (2018) DOI `10.1038/s41467-018-07210-0`（Lusch et al.）；Mach. Learn.: Sci. Technol. 6 (2025) 015063 DOI `10.1088/2632-2153/adb9b5`；Cambridge 机构库 lifting 手稿 |
| Q5 | `LSTM recurrent sequence model Koopman lifting predictive control` | T2 LSTM/GRU | UCLA PDCLab PDF（Luo et al. 2023，电解反应器在线线性化 MPC）；Neurocomputing (2025) PII `S0925231225003844`（LSTM/GRU-MPC 综述）；arXiv:2005.02762（RNN vs Koopman）；arXiv:2408.02315（input-augmented Koopman / DKOIA）；IEEE 稿件 `9154669` |
| Q6 | `extended dynamic mode decomposition with control EDMDc Korda Mezic` | 受控 Koopman / DMDc 规范来源 | Proctor/Brunton/Kutz DMDc（SIAM J. Appl. Dyn. Syst. 15(1)，arXiv:1409.6358）；Korda & Mezić EDMD 收敛（arXiv:1703.04680）；Princeton OAR「Extending Data-Driven Koopman Analysis to Actuated Systems」（输入作时变参数 + LPV + L1,2 正则） |

检索共 6 次。**未**下载任何全文；判断只依据检索返回的题录与正文片段。

## 2. 检索的边界与已知弱点

1. 通用 web 搜索会给出**聚合页/镜像页**；同一篇的题录在多个来源一致时才记为「已核验」（例如 Korda & Mezić 2018 同时出现在 ACM DL 条目、UCSB 课题组 PDF 与 arXiv:1611.03537 三处）。
2. 未使用 DOI 解析器逐条解析，因此**卷期页码一律未核实**；`09` 中只给 DOI/arXiv ID 本身。
3. 2024–2026 的条目（含旧稿引用的多篇 2025/2026 工作）在本次检索中信息最少，全部标 `待核实`。
4. 计划书 §6.1 提到的「双线性 Koopman 论文」**未找到唯一对应物**；已如实留空（`09` §2.4）。

## 3. 旧稿引用核对（机械扫描）

脚本 `02_ref_scan.py`（**已落盘在本目录**，只用标准库，路径自推导）：遍历仓库内全部 `.tex` / `.bib`，抽取 `\cite*{...}` 的 key 集合、`.bib` 的 `@type{key,` 集合，以及 `.tex` **内联 `thebibliography`** 中的 `\bibitem{key}` 集合，做集合运算与逐条题录文本比对。原始输出见同目录 `03_ref_scan_output.txt`（由脚本自行以 UTF-8 写出，不经 shell 重定向，以免控制台编码污染）。

> **方法更正（第一版错误）**：第一版脚本**只**抽取了 `.bib` 的 `@type{key,`，**没有**抽取 `.tex` 内联 `thebibliography` 的 `\bibitem`，因而错误地得出「48 个 key 在仓库内没有任何定义」。实际上旧稿题录内联在 `Main.tex` 第 824–982 行（52 条）。该错误由 TASK-035 第一轮独立复核者指出（M1），第二版已改正。下面是**更正后**的完整口径。

```
.tex 文件 8 个：
  杂项/老版本/_new_abstract.tex, _new_intro.tex, _new_related.tex,
  _new_related2.tex … _new_related5.tex
  论文/老版本/Main.tex                          ← 使用 48 个 cite key
.bib 文件 6 个（论文/{新版本,老版本}/bibtex/）：
  IEEEabrv.bib   (263 entries)  IEEEfull.bib (263 entries)   ← IEEEtran 刊名缩写表
  IEEEexample.bib (72 entries)                              ← IEEEtran 示例条目
```

**更正后的结论**（三段式；详见 `09` §3.2–§3.5）：

1. **题录位置**：`论文/老版本/Main.tex` 的 52 条 `\bibitem` **内联在正文**（第 824–982 行），**不在** `.bib` 文件里。正文使用 48 个 cite key，全部有题录；4 条题录未被引用（`duran2025control`、`han2020deep`、`shi2022deep`、`strasser2026overview`）。
2. **`.bib` 的性质**：仓库内 6 个 `.bib`（`论文/{新版本,老版本}/bibtex/`）**全部是 IEEEtran 模板**（`IEEEabrv` 263 / `IEEEfull` 263 缩写表 + `IEEEexample` 72 示例），**不含任何论文题录**。这一点第一版是对的。
3. **`杂项/老版本/_new_related*.tex`（related work 草稿系列）**：共用 52 个 key，其中 11 个不出现在 `Main.tex` 的引用中；核对宇宙 = 52 ∪ 11 = **63 个 key**。

**既有 strict 审计的继承范围（TASK-006 / DEC-030 / `EV-PHASE2-CITATION-AUDIT-002`）**：`杂项/老版本/_audit_bib.json` 的 **50 条**题录与当前 `Main.tex` 的 52 条中对应的 50 条**逐条文本完全一致**（空白归一化）→ 该审计对这 50 条的 Crossref/OpenAlex 核验**可继承**；`han2024robust`、`shenoy2025temporal` 是审计之后加入的 **2 条**，**不受覆盖**；草稿专用键亦不受覆盖。

→ 逐条分级见 `09` §3.5（A 3 / A′ 50 / B 2 / C 6 / D 2（已判伪造，禁止使用）），计数自洽性检查也在该节。

`09` 与本次核对**未**修改任何 `.bib`、**未**改动 `Main.tex`；新建 bibliography 的动作留给论文阶段。
