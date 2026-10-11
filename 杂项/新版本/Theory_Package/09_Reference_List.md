# 09 — Reference List（阶段二：文献调研）

> **本文件的性质**：前期工作的可核验文献清单，服务于理论包（`01`–`08`）的定位与假设来源，**不进入论文正文**（论文写作阶段的文献工作另行授权）。
>
> **诚实规则（REQ-002 / DEC-081）**
> 1. 本清单**不编造引用键**。每条给出**本会话实际检索到**的标识（DOI / arXiv ID / PII / 稳定链接）。
> 2. 标 **`待核实`** 的条目**不得**给出被当作已核实的 **DOI 或卷期页码**；但可以给出**检索命中位置**（arXiv ID / PII / 稿件 ID / URL）作为他人继续核实的线索 —— 二者区别在于：命中位置说明「我在哪里看到它」，DOI/卷期页说明「我认为它的题录就是如此」。
> 3. 本会话的检索为**尽力而为**（用户授权：搜不到就跳过），检索工具为通用 web 搜索，**未**逐篇下载原文精读。因此「已核验」= 至少两个独立来源给出同一标识；**不等于**读过全文。
> 4. 旧稿参考文献的核对另有**既有 strict 审计**可继承，见 §3 —— 那里同时记录了本文件**第一版的错误**及其更正。

---

## 0. 术语与路线定位（先读）

本工作的方法 = **scheduled Koopman predictor + measurement-dependent input modulation**（DEC-079），即

```
z_{k+1} = A(c_k) z_k + B(chi_k) u_k ,  c_k = C_phi(X_k, U^in_k) ,  chi_k = C_x z_k
```

它由两条**成熟的**文献路线组合而成：

- **（甲）受控 Koopman 预测器**：把受控系统嵌入扩展状态空间、限制可观测函数结构，使有限维近似具有 `A z + B u` 的形式 → §2.1。
- **（乙）参数变化 / 上下文相关算子**：让（甲）中的算子依赖调度变量（参数、操作点或历史窗口）→ §2.2。

**本工作相对（甲）（乙）的增量**（必须诚实陈述）：
- 调度变量**只**来自历史窗口测得的测量与过去输入（`c_k`），**当前输入 `u_k` 不进入 `c_k`**；
- **输入矩阵也依赖状态**：`B(chi_k)`，`chi_k = C_x z_k`（measurement-dependent input modulation）——这在（甲）（乙）中没有直接对应物，**是本工作引入的扩展**；
- 两类修正都取**低秩**形式（`r_A`、`r_B`），并给出**显式有界性与 Lipschitz 常数**（`03`、`04`），进而给出冻结误差界与条件次优性（`07`、`08`）。

> **命名提示（DEC-079）**：当 `B` 依赖状态时，`B(chi)u` 是状态与输入的乘积项，形式上与双线性系统同族。但「bilinear Koopman」在文献中通常特指**提升坐标下的双线性模型**这一类构造。本阶段**不使用**「bilinear Koopman」这一名称，命名裁决推迟到论文阶段。

---

## 1. 四主题清单

分类标签：**支撑**（支持本文建模/证明选择）、**竞争**（与本文方法直接可比、必须在 Related Work 中区分）、**待核实**（本会话未能独立核实；若该条目已被既有 strict 审计覆盖，见 §3.5）。

### T1 — 时序提升：延迟坐标 / 延迟嵌入

| # | 条目 | 标识 | 类别 | 与本文的关系 |
|---|---|---|---|---|
| T1-1 | Korda & Mezić, *Linear predictors for nonlinear dynamical systems: Koopman operator meets model predictive control*, Automatica **93** (2018) | DOI `10.1016/j.automatica.2018.03.046`；arXiv:1611.03537 | **支撑** | （甲）的核心来源：受控 Koopman → 线性预测器 → **MPC 化为凸 QP**。本文 `06` 的 QP 结构与「提升坐标中线性预测」这一立场直接来自此路线 |
| T1-2 | *HAVOK Model Predictive Control for Time-Delay Systems with Applications to District Heating* (2023, Aalborg University) | 稳定链接：`vbn.aau.dk` 机构库条目 | **支撑（需区分）** | 用投影时间延迟坐标（HAVOK）构造 MPC，并**显式界定计算复杂度**。是「用历史窗口换线性性」的同类路线，Related Work 必须与本文的 `c_k = C_phi(X_k, U^in_k)` 区分 |
| T1-3 | *Koopman-based lifting techniques for nonlinear systems identification* | 稳定链接：Cambridge 机构库（Apollo）PDF | 竞争 | 以提升方式做非线性辨识（主方法/对偶方法）；其「提升坐标不可直接对应当前状态」的讨论与本文 `C_x z = x` 的保状态设计形成对照 |
| T1-4 | 延迟坐标与 Koopman 谱 | 旧稿 keys `das2019delay`、`kamb2020timedelay` | 支撑（见证 §3.5） | 二者均在既有 strict 审计覆盖的 50 条题录内（§3.5），题录文本与当前 `Main.tex` 逐字一致 |

### T2 — 时序提升：LSTM / GRU 路线

| # | 条目 | 标识 | 类别 | 与本文的关系 |
|---|---|---|---|---|
| T2-1 | Luo et al., *Machine learning-based predictive control using on-line model linearization: Application to an experimental electrochemical reactor* (2023; © IChemE / Elsevier) | 稳定链接：UCLA PDCLab 公开 PDF | **竞争（最近）** | **最接近本工作动机的对照**：LSTM 过程模型 → 用 Koopman 方法**在线线性化** → MPC 化为 QP。差异：其线性化逐采样点做、无历史窗口调度变量、**无误差界**；本文给 `A(c)`、`B(chi)` 的显式有界性与冻结误差界 |
| T2-2 | *LSTM and GRU type recurrent neural networks in model predictive control: A Review*, Neurocomputing (2025) | ScienceDirect PII `S0925231225003844` | 竞争 | 综述：LSTM/GRU 进 MPC 的各种方式与**计算复杂度**讨论；用于界定「序列模型 + MPC」这条路的现状 |
| T2-3 | Xie & Ren (2020)（RNN 模型 Koopman 线性化的源头工作） | 仅在 T2-1 正文被他引（`Xie and Ren (2020)`） | `待核实` | 本会话**未**直接检索到该文的题录；**不给**标识。论文阶段须逐条核对后再引 |
| T2-4 | *Linearization of recurrent-neural-network-based models for predictive control*（IEEE） | 检索命中位置：IEEE Xplore 稿件 ID `9154669`（题录 `待核实`） | `待核实` | 仅确认该稿件存在；作者/刊名/年份本会话未核实 |
| T2-5 | *Recurrent neural networks and Koopman-based frameworks for temporal predictions in a low-order model of turbulence* | arXiv:2005.02762 | 支撑 | RNN 与 Koopman 路线的**预测能力对照**（含 KNF）；支持「Koopman 代理在长时预测上可优于 RNN」的动机，但不涉及控制 |
| T2-6 | 其它 LSTM 提升 | 旧稿 keys `takeishi2017koopman`、`yeung2019learning`、`azencot2020forecasting` | 支撑（见证 §3.5） | 三者均在既有 strict 审计覆盖的 50 条题录内（§3.5） |

### T3 — 时序提升：Transformer 路线

| # | 条目 | 标识 | 类别 | 与本文的关系 |
|---|---|---|---|---|
| T3-1 | *DeepKoopFormer: a Koopman enhanced transformer based architecture for time series forecasting*, npj Artificial Intelligence (2026) | DOI `10.1038/s44387-026-00085-3` | **竞争** | Transformer 编码器 + **谱约束线性传播子**（ODO 分解，`rho(K) < 1`）+ 线性解码。差异（关键）：传播子**固定线性**、非调度、**只做预测**（单次施加传播子）、无控制回路 |
| T3-2 | *Learnable Koopman-Enhanced Transformer-Based Time Series Forecasting with Spectral Control* | arXiv:2602.02592 | **竞争（最近）** | 提出**四类可学习 Koopman 参数化**，含 **low-rank Koopman**（`rank r << d`）与 MLP 形状的谱映射 —— 与本文「低秩调制」在**结构上最接近**的公开工作。差异：面向预测、无测量依赖输入调制、无控制、无误差界 |
| T3-3 | *An attention-based approach for Koopman modeling and control*（ISA Transactions, 2025） | 检索命中位置：ScienceDirect PII `S0019057825001880`（完整题录 `待核实`） | 竞争 | 注意力 + Koopman 建模与控制；本会话只拿到部分信息 |
| T3-4 | *Networked Systems: Model-Predictive Grid Control*（Koopman-inspired deep NN 编码-解码 + MPC；IEEE 39-bus） | arXiv:2206.01272 | 支撑 | 「无需字典的端到端提升 + 提升空间中做 MPC」的工程代表；其「线性嵌入使 MPC 实时」的措辞**不得**被本文复用（本文不作实时性声称，`06` §5） |
| T3-5 | 序列骨干网络 | 旧稿 keys：`vaswani2017attention`、`liu2023koopa`、`nie2023time`（审计覆盖内）；`zhou2021informer`、`wu2021autoformer`、`zhou2022fedformer`、`wang2020linformer`、`choromanski2021performer`（仅草稿键） | 支撑 / `待核实` | 见 §3.5：前三者在既有 strict 审计覆盖的 50 条题录内；后五者**不在**审计覆盖内 → `待核实`，论文阶段须逐条核对 |

### T4 — 上下文相关 / 参数变化调度

| # | 条目 | 标识 | 类别 | 与本文的关系 |
|---|---|---|---|---|
| T4-1 | *Parameter-varying Koopman operator (PVKO)* + MPC | arXiv:2309.10278 | **竞争（最接近）** | 在提升空间中**插值局部时不变线性系统**，得到参数变化算子并据此设计 MPC，且**分析可行性与稳定性**。与本文 `A(c)` 的调度思想同源。差异：其调度来自**外部参数/未来参数信息**；本文调度来自**历史测量窗口** `c_k = C_phi(X_k, U^in_k)`，且输入侧额外引入状态依赖 `B(chi)` |
| T4-2 | Proctor, Brunton & Kutz, *Dynamic Mode Decomposition with Control* (DMDc), SIAM J. Applied Dynamical Systems **15**(1) | arXiv:1409.6358；期刊页公开 PDF | **支撑** | 「输入如何线性进入提升模型」的规范来源：`x_{k+1} ≈ A x_k + B u_k` 的数据驱动辨识。本文无调度时 `A_0 z + B_0 u` 即属此类 |
| T4-3 | *Extending Data-Driven Koopman Analysis to Actuated Systems* | 稳定链接：Princeton OAR 公开 PDF | **竞争（需区分）** | 把**输入当作时变参数**、与 EDMD 结合成 **LPV 形式的 Koopman 近似**并加 L1,2 正则 —— 与本文「调度算子」在方法论上直接可比，Related Work 必须说明本文的调度变量来自测量窗口而非输入参数 |
| T4-4 | Korda & Mezić, *On Convergence of Extended Dynamic Mode Decomposition to the Koopman Operator* | arXiv:1703.04680 | **支撑** | 有限维截断的收敛性（`M → ∞`、`N → ∞`，有限时域预测的 L2 收敛）。**用于界定「代理」一词的含义**：有限维 `A(c), B(chi)` 是**近似代理**，不假定不变子空间存在 |
| T4-5 | Lusch, Kutz & Brunton, *Deep learning for universal linear embeddings of nonlinear dynamics*, Nature Communications **9** (2018) | DOI `10.1038/s41467-018-07210-0` | **支撑** | 用深度自编码器学习 Koopman 特征函数坐标（`y_{k+1} = K y_k`）。本文的编码器 `g_theta`（`z = g_theta(X)`）属于此路线；本文**不**声称编码器学到精确特征函数 |
| T4-6 | Goyal et al., *Deep learning for structure-preserving universal stable Koopman-inspired embeddings…*, Mach. Learn.: Sci. Technol. **6** (2025) 015063 | DOI `10.1088/2632-2153/adb9b5` | **竞争（需区分）** | 结构保持 + **有界稳定**的嵌入构造。与本文同为「Koopman 嵌入 + 约束」路线，须在 Related Work 中区分：本文只给**有界性**（`03`）而非稳定性 |
| T4-7 | *Machine learning-based input-augmented Koopman modeling and predictive control of nonlinear processes* (DKOIA) | arXiv:2408.02315 | **竞争** | **对状态与输入分别做提升**，得到「输入非线性」的 Koopman 模型，再用**迭代凸近似**避免非凸优化。与本文 `B(chi) u` 的动机相邻，但技术路线不同（迭代凸化 vs. 冻结调度 + 误差界）。**Related Work 必须区分** |
| T4-8 | *Koopman operator theory: fundamentals, control, and applications*（教程） | arXiv:2607.01819 | 支撑 | 入门教程 + 代码：EDMD、带输入系统和 Koopman MPC。用于统一记号与背景 |
| T4-9 | 控制侧（LPV / qLMPC / RTI / 高级步） | 旧稿 keys `diehl2005realtime`、`diehl2005rtistability`、`gros2020rti`、`cisneros2016qlmpc`、`cisneros2020qlpv`、`zavala2009advancedstep`、`leith1998velocity`、`rugh2000gain` | 支撑（见证 §3.5） | 八者**全部**在既有 strict 审计覆盖的 50 条题录内（§3.5）。**重要**：本文 `06` §5 明确**不声称**已实现 RTI 或满足实时截止时间 |

---

## 2. 为什么 `A(c) z + B(chi) u` 是合理的 controlled Koopman 代理（done_when #2）

### 2.1 无调度部分有明确的文献身份

- 无控系统的 Koopman 算子是**线性但无穷维**的；有限维近似 = 提升坐标中的**线性预测器**（T1-1、T4-4）。
- **受控**情形的标准处理（Korda & Mezić, T1-1）：把受控系统看作**扩展状态空间**（原状态 × 控制序列空间）上的无控系统，并**施加结构约束**于可观测函数集合，使有限维 EDMD 近似**恰好具有线性受控形式** `z_{k+1} = A z_k + B u_k`。
- 因此 `z = [x; psi]` 上的 `A_0 z + B_0 u` **不是**本文的发明，而是「受控 Koopman 线性预测器」的规范形式（T1-1、T4-2）。

**关键限定（必须写进论文）**：这条路线**不保证**存在有限维不变子空间；它保证的是（在采样意义下的）**投影收敛**（T4-4）。所以 `A(c) z + B(chi) u` 的准确身份是**有限维近似代理**，不是「真实 Koopman 算子」。

### 2.2 调度部分是两条成熟路线的组合

单一时不变线性预测器在远离操作点时精度有限（T4-1、T4-7 都以这一点为动机）。让算子依赖调度变量的成熟做法有两种：

1. **参数变化路线**：把输入或操作点当作参数，得到 LPV 形式的 Koopman 近似（T4-3），或插值局部 LTI 系统得到 PVKO（T4-1）。
2. **数据驱动提升路线**：用神经网络学编码器/提升（T4-5），并可加入结构保持与稳定性约束（T4-6）。

本文取 `c_k = C_phi(X_k, U^in_k)`（历史窗口 → 调度变量）与低秩调制 `A(c) = A_0 + U_A diag(gamma_A(c)) V_A^T`，属于路线 1 的结构化、可分析版本：**低秩 + 显式常数**，因此才能给出 `03`/`04` 的有界性与 Lipschitz 界，并一路推到 `07`/`08` 的误差界与条件次优性。**T4-2 与 T4-3 的存在说明「`A z + B u` 中的 `A` 随参数变化」在文献中是有先例的**。

### 2.3 本文的增量（**没有**文献直接支撑的部分）

`B(chi_k)`（`chi_k = C_x z_k`，即输入矩阵依赖当前**测量**）在（甲）（乙）中**没有直接对应物**：

- T1-1 的 `B` 是**常数**矩阵；
- T4-7 走的是**把输入一起提升**、使模型在输入上非线性的另一条路（并须用迭代凸近似规避非凸性）。

因此 `B(chi) u` 的合理性**只能**由本文自己的结构假设与命题支撑（`02` 的 A3/A4、`03` 命题 1、`04` 命题 2），论文中必须写成 **"a measurement-dependent input modulation introduced in this work"**，**不得**写成「文献中的标准做法」。

同理，`B(chi) u` 使完整调度问题一般**非凸**（`06` §1 已证），这正是 `06`–`08` 必须给「冻结 + 误差界 + 条件次优性」的原因 —— 这条推理链也**依赖本文自己的结果**，不能引文献代劳。

### 2.4 关于「双线性 Koopman」与计划书 §6.1 的那篇文献

- 计划书 §6.1 提到「你读到的双线性 Koopman 论文」。用户明确表示记不得该文，并授权独立检索（搜不到即跳过）。
- **本轮检索未找到**与该描述唯一对应的文献。最接近的两个候选是 **T4-7（输入增强 Koopman）** 与 **T4-1（参数变化 Koopman，PVKO）**，但**没有证据**表明其中任何一篇就是用户读到的那篇 → **如实留空，不指定**。
- 术语处理见 §0 提示：本阶段**不使用**「bilinear Koopman」名称（DEC-079）。

---

## 3. 旧稿参考文献的核对（done_when #4）

### 3.1 方法与两个信息源

1. **本会话的机械扫描**：遍历仓库内全部 `.tex` 与 `.bib`，抽取 ① `\cite*{...}` 使用的 key、② `.bib` 中的 `@type{key,` 定义、③ **`.tex` 内联 `thebibliography` 中的 `\bibitem{key}`**，做集合运算与**逐条题录文本比对**（脚本 `notes/literature/02_ref_scan.py`，原始输出 `notes/literature/03_ref_scan_output.txt`；检索说明见 `01_search_log.md` §3）。
2. **仓库内既有的 strict 审计（继承，不重做）**：`杂项/老版本/citation_audit_report.md`（任务 TASK-006，strict，决策 DEC-030，证据 `EV-PHASE2-CITATION-AUDIT-002`）曾对**更早一版** Main.tex 的参考文献区做对拍 —— 方法为程序化抽取 + 6 个并行 research 子代理与 **Crossref / OpenAlex / arXiv / 出版社页**逐条核对。其条目映射保存在 `杂项/老版本/_audit_bib.json`。本轮**不重做对拍**，而是用**题录文本一致性**判定其结论可继承的范围（§3.4）。

### 3.2 事实（本会话机械复算；不含判断）

**当前 `论文/老版本/Main.tex`** = 74273 B，sha256 `80fb881e6b78c79c35a2a6ea333b3e53f5092bdc15f1b49fa0b259618053c204`：

- 参考文献表**内联在正文**（`\begin{thebibliography}` 位于第 **824–982** 行），共 **52 条 `\bibitem`** —— **不在** `.bib` 文件里。
- 正文使用 **48 个 `\cite` key**；`48 ∩ 52 = 48` → **所有被引键都有题录**（`cited \ bibitem = ∅`）。
- **4 条题录未被引用**：`duran2025control`、`han2020deep`、`shi2022deep`、`strasser2026overview`。
- 仓库内 6 个 `.bib`（`论文/{新版本,老版本}/bibtex/`）**全部是 IEEEtran 模板**：`IEEEabrv.bib` 263 条、`IEEEfull.bib` 263 条（刊名缩写表）、`IEEEexample.bib` 72 条（示例条目，均为 `IEEEexample:xxx`）。**它们不含任何论文题录。**
- 草稿 `杂项/老版本/_new_related*.tex`（Related Work 系列）共用 **52** 个 key，其中 **11 个**不出现在 `Main.tex` 的引用中：`choromanski2021performer`、`duran2025control`、`forootani2026deepkoopformer`、`han2020deep`、`shi2022deep`、`strasser2026overview`、`wang2020linformer`、`wu2021autoformer`、`yuan2022variational`、`zhou2021informer`、`zhou2022fedformer`。
- **核对对象** = 52 条 `\bibitem` 槽 + 11 个草稿专用槽 = **63 个槽位**（两者有 4 个键重叠，故**不同键**为 **59**）。

> ### ⚠ 本文件第一版的错误与其更正
> 第一版曾写「48 个引用键**全部未定义**、旧稿在现有材料下**无法生成参考文献表**」。**该结论是错的**：旧稿的题录一直**内联在 `Main.tex` 的 `thebibliography` 中**（52 条）。根因是当时的扫描脚本只比对 `.bib` 文件，**没有读取 `.tex` 内联的 `\bibitem`**，是一个**方法错误**（结论错误，数据没错）。
> 该错误由 `TASK-035` 的**第一轮独立复核者**指出（复核项 `M1`），第二版已改正。该错误**未**影响 §1/§2 的文献清单与论证，也**未**被写入任何论文文件（本阶段未改动 `论文/`）。

### 3.3 既有 strict 审计的结论（**继承，不重做**）

`citation_audit_report.md` 对**更早一版** Main.tex 的对拍结果：**63 条 → 55 条**。

> **路径沿革**：审计报告 L4 记载的审计对象是当时的 `论文/新版本/Main.tex`；经 2026-10-10 的目录重构（TASK-033）后，该文件现位于 `论文/老版本/Main.tex`。本节的继承结论靠**题录文本一致性**桥接版本差异，不依赖路径。

- **删除 2 条不存在/伪造条目**
  - `yuan2022variational` — 判**伪造/拼合**：标题前缀取自 Wu et al., *J. Chem. Phys.* 146(15) 154104 (2017)，"uncertainty quantification" 概念取自 Morton et al.；其声称的作者与 IEEE TAC 67(11) 5905–5920 **均不存在**。该条当时在正文被引，已同时从引用簇移除。
  - `rank2019recurrent` — 无任何数据库记录，且从未被引用。
- **删除 6 条 dead entry**：`brunton2016sindy`、`zeng2023transformers`、`liu2024itransformer`、`forootani2026compact`、`forootani2025synthetic`、`katharopoulos2020transformers`。
- **元数据修正 10 条**：`morton2019deep`（页码 → 3173–3179）、`klus2018data`（作者补全为 7 人）、`forgione2021dynonet`（页码 → 612–626）、`nelles2020nonlinear`（副标题补全）、`kamb2020timedelay`（vol. 19, no. 2, pp. 886–917）、`han2020deep`（arXiv → Proc. IEEE CDC 2020, pp. 1890–1895）、`mezic2005spectral`（no. 1–3）、`otto2021koopman`（no. 1）、`das2019delay`（no. 6）、`ljung1999system`（imprint → Prentice Hall PTR）。
- **引用键年份修正**：`forootani2026deepkoopformer` → **`forootani2025deepkoopformer`**（正文与题录同步修改）。
- 审计后自述：55 条、全部被引用、重编译 **0 undefined citation**。

### 3.4 继承的**边界**（用题录文本一致性判定）

- 审计报告记录的产物指纹：`Main.tex` sha256 `0DA30C3EDC56…`、**80917 B**；**当前** `Main.tex` 为 **74273 B**、sha256 `80fb881e…` → **不是同一版**。
- `_audit_bib.json` 内含 **50** 条 key→题录文本。本会话把它的 50 条与当前 `Main.tex` 的 52 条**逐条做文本比对（空白归一化）**：
  - **50 条全部逐字一致**（`identical = 50`，`different = 0`）；
  - `审计集 \ 当前集 = ∅` → 审计中的条目没有任何一条被删掉；
  - `当前集 \ 审计集 = {han2024robust, shenoy2025temporal}` → **这 2 条在审计之后加入**，未被对拍过。

**因此**：审计对**这 50 条**的 Crossref/OpenAlex 核验（含 §3.3 的删除与修正）**可以继承** —— 因为被核验的题录文本在磁盘上**未变**；而 **`han2024robust`、`shenoy2025temporal` 以及全部草稿专用键不受该审计覆盖**。

**仍未解决、必须由论文阶段处理的点**：
1. 报告说审计后 **55 条**，`_audit_bib.json` 有 **50 条**，当前有 **52 条**（48 被引）—— **三个数字分属三个快照，本会话无法从现有材料判定其关系**。
2. 报告 §5 自述：44 条 PASS 的条目**未逐条留对拍快照** → 证据链不完整。
3. `han2024robust`、`shenoy2025temporal` 两条**从未被任何审计覆盖**。
4. 当前版本的**引用↔主张对应**（报告 §3 处理过的那类问题）在历次编辑后**未重新核对**。

### 3.5 分级与处置（口径 = §3.2 的 63 个 key）

| 类 | 定义 | 数量 | 处置 |
|---|---|---|---|
| **A** 本会话独立核实（多来源题录一致） | `korda2018linear`、`proctor2016dmdc`、`lusch2018deep` | 3 | 可直接复用；论文阶段补卷期页 |
| **A′** 既有 strict 审计已对拍，且**题录文本与当前字节一致**（§3.4） | §3.4 判定的 50 条 | 50 | **可复用**；但证据链缺口（报告未逐条留快照）须在论文阶段补足 |
| **B** 不在审计覆盖内、本会话也未能核实 | `han2024robust`、`shenoy2025temporal` | 2 | 论文阶段**首次**核对 |
| **C** 草稿专用**且无** `Main.tex` 的 `\bibitem` | `choromanski2021performer`、`wang2020linformer`、`wu2021autoformer`、`zhou2021informer`、`zhou2022fedformer`、`forootani2026deepkoopformer` | 6 | 论文阶段按需重建；注意 `forootani2026deepkoopformer`（草稿）与 `forootani2025deepkoopformer`（正文）**重名/笔误**问题 |
| **D** **已判伪造/不存在 → 禁止使用** | `yuan2022variational`（仅在 5 个 `_new_related*.tex` 草稿中；**已不在** `Main.tex`）；`rank2019recurrent`（已不在任何文件） | 2 | **禁止**重新引入。若确需覆盖该主题，改用 Wu et al., *J. Chem. Phys.* 146(15) 154104 (2017) 另建条目并配真实引用 |

**计数自洽性**（逐项可复算）：
- `50 (A′) + 2 (B) = 52 = Main.tex 的 \bibitem 数` ✓
- 11 个草稿专用键分解为 `11 = 6 (C) + 1 (`yuan2022variational` ∈ D) + 4`，其中这 4 个（`duran2025control`、`han2020deep`、`shi2022deep`、`strasser2026overview`）是 Main 的**未引 `\bibitem`**，已计入 A′ ✓
- `rank2019recurrent` 属 D 类但**不在任何草稿文件中**，故**不计入**这 11 个 ✓
- `A` 的 3 条与 A′ 重合（同属那 50 条），故**不另计数** ✓
- 核对对象 = `52 条 \bibitem 槽 + 11 个草稿专用槽 = 63`；两者有 4 个键重叠，故**不同键**为 **59** ✓

**处置建议（论文阶段）**：不要直接沿用旧稿 key。以 A′ 的 50 条为**起点**（其题录文本已在磁盘上验证未变），补做 B/C 类与 §3.4 的 4 个遗留点；`D` 类的两条**永不复用**。

---

## 4. 待核实清单（汇总，供论文阶段处理）

1. `T2-3`「Xie & Ren (2020)」的题录（旧稿未引，是 T2-1 正文提到的源头工作）。
2. `T2-4`（IEEE 稿件 `9154669`）、`T3-3`（ISA Transactions 2025，PII `S0019057825001880`，见 §1 T3-3）的**完整题录**。
3. **§3.4 的 4 个遗留点**：55/50/52 三个数字的关系；报告 44 条 PASS 缺逐条快照；`han2024robust` 与 `shenoy2025temporal` 从未被审计；引用↔主张对应关系未重核。
4. `forootani2026deepkoopformer`（草稿）与 `forootani2025deepkoopformer`（正文）的**重复/笔误**。
5. 计划书 §6.1 所指「双线性 Koopman 论文」的**具体身份** —— 需用户提供线索或原文。
6. §1 中仍标 `待核实` 的条目（T2-3、T2-4、T3-3、T3-5 的 5 个草稿键）。

## 5. 本文件**没有**做的事（避免误读）

- 没有下载并精读上述任何一篇原文（只读检索返回的摘要/正文片段）。
- 没有对任何一篇的**实验设置、结果数字或优先权**作出判断；§1 的「关系」列只描述**建模立场**的异同。
- 没有重做 Crossref/OpenAlex 对拍（§3.3 的结论是**继承**自既有 strict 审计，并按 §3.4 划定了继承边界）。
- 没有把本清单中的任何条目写进论文、摘要、Introduction 或标题（本阶段禁止，REQ-002 / DEC-079）。
- **没有修改** `论文/` 下的任何文件：未新增/修改 `.bib`，未改动 `Main.tex`（git 工作区对 `论文/` 零改动，见 TASK-041 的证据）。
