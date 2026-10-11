# 10 — Reference_List 补充件：计划书第二阶段四主题

> **本文件的性质**：前期工作的**文献补充件**，用于补齐 `GOAL-002` 的 `SC-2`。它与 `09_Reference_List.md` **并列**、不改动 `09` 的任何一个字节。
>
> **状态**：前期材料，**不是论文正文**，**不进论文**（REQ-002 / BA-003）。本阶段禁止事项同 `00_Index.md`：不使用「bilinear Koopman」名称；不声称实时性、闭环稳定性、递归可行性；不编造引用键。
>
> **为什么有这份补充**：`GOAL-002` 的 `SC-2` 原文要求文献调研覆盖「the plan's four topics (controlled/input-affine Koopman surrogates, LPV and scheduling MPC with frozen parameters, prediction-error bounds, approximate/frozen-model MPC theory)」。计划书《第二阶段：文献调研任务》的 §1–§4 正是这四个主题。而 `TASK-035` 实际调研的是**论文 Related Work 的四个主题**（延迟坐标 / LSTM-GRU / Transformer / 上下文相关调度，见 `AGENTS.md` 论文写作规则 §B.12）——两组主题不同，故 `SC-2` 原先**只部分满足**。本件补做计划书四主题。
>
> **检索口径**：`DEC-081` 已把文献调研降级为**尽力而为、不作为前置**。本轮共 5 次检索（见 `../notes/literature/04_sc2_search_log.md`），检索到的条目按下面的核验等级逐条标注；**检索不到的不编造**。

---

## 0. 核验等级（本件使用的口径）

| 等级 | 含义 |
|---|---|
| **A** | 本轮检索中**直接读到**题名 / DOI / arXiv ID / 卷期页（可核验）。 |
| **A′** | 在**已核验文献（等级 A）的正文或参考文献表**中被引用，题名或作者-年份可见；本件**未**独立打开原文。 |
| **B** | 仅以「作者 + 年份」形式被二级提及，题名与出处不明 → **一律标「待核实」**，不得进入论文引用键。 |
| **D** | 已判伪造或不存在（沿用 `09` §3.5 的判定），**禁止复用**。 |

> 本件**不含** D 级条目。任何未标等级的表述都视为**未核验**。

---

## 1. 计划书 §2.1 — Koopman controlled systems

**计划书要求**：Koopman with control；input-affine Koopman；finite-dimensional Koopman approximation。**目标**：回答「为什么 $A(c)z+B(\chi)u$ 是合理的 controlled Koopman surrogate？」（该问题的正面回答已在 `09` §2 给出，本件只补文献面。）

| # | 条目 | 等级 | 与本文的关系 |
|---|---|---|---|
| 1.1 | **Proctor, Brunton, Kutz (2016)**，DMD with control（DMDc） | A′ | 受控 Koopman 代理的起点；「控制进入线性」的最常见形式。`09` §1（T4-2）已把它与 Korda–Mezić 并列。 |
| 1.2 | **Korda & Mezić (2018a)**，DMDc 用于 MPC | A′ | 与 `09` §1（T1-1）的 Korda–Mezić 2018（Automatica 93，DOI `10.1016/j.automatica.2018.03.046`）对应（**Automatica 93** 这一卷号出自 `09`，不在 `04`）。 |
| 1.3 | **Korda & Mezić (2018b)**，EDMD 收敛性 | A′ | 有限维近似的收敛依据（`09` §2 已用）。 |
| 1.4 | **Kaiser, Kutz, Brunton (2021)**，坐标变换到 Koopman 特征函数 | A′ | 另一条受控提升路线（非本文所用）。**作者全名不在 `04`**（`04` 仅记「Kaiser et al. 2021」），故作者归属待核实。 |
| 1.5 | **Mamakoukas et al. (2021)**，逐分量 Taylor 展开 | A′ | 与「状态相关输入矩阵」的**另一种构造**（属 §1 的主题，**非** §3.3 的核方法误差界）。 |
| 1.6 | **Lu et al. (2020)**，用 Korda–Mezić 收敛结果估计 DMDc 的预测误差 | A′ | 明确指出该结果是**渐近**的、**不给数据量收敛率** → 支撑本件 §3 的动机。 |
| 1.7 | **Peitz & Klus (2019)；Peitz et al. (2020)**，由 $n_c+1$ 个自主 Koopman 算子构造**双线性**代理 | A′ | 关键对照：该路线**不把控制增广进状态**，从而回避维数灾难；与本文「$u_k$ 不进 context」的设计取向一致（**注：术语仍按 `DEC-079` 不使用 bilinear Koopman**）。出处：Nüske et al. 2023 §1 相关工作段原文「constructs its surrogate model from $n_c+1$ autonomous Koopman operators, where $n_c$ is the control dimension」（该引句已镜像进 `04` 检索 4）。 |
| 1.8 | **Goswami & Paley (2017)；Bruder et al. (2021)；Peitz & Bieker (2021)** | A′ | 被引作「对一般控制仿射系统，数值上双线性代理更合适」的证据。 |
| 1.9 | **Schaller et al. (2022)** | A′ | 控制设定下的投影误差估计（有限字典尺寸）→ 与 §3 直接相关。 |
| 1.10 | **Kurdila & Bobade (2018)；Zhang & Zuazua (2021)** | A′ | 自主情形下的投影误差。 |
| 1.11 | **arXiv:2201.05098**（题名未在可见片段中显示） | A | 本轮**直接检索命中**（arXiv ID 与摘要直接可见）。内容为「由数据构造可稳定的双线性 Koopman 提升 + 控制 Lyapunov 函数，可证明渐近稳定」。**仅作领域活跃度证据**；不引用其结论。 |
| 1.12 | **"An overview of Koopman-based control: From error bounds to closed-loop guarantees"**（Review article） | A | 综述，摘要明确把「有限维近似误差 → 控制器设计 → 闭环保证」串成一条线，并覆盖线性与双线性 EDMD 控制方案。**注意**：旧稿参考文献中有一条未引条目 `strasser2026overview`（`09` §3 已登记），本件**不声称**二者同一；如需对应须独立核对。 |

**小结（§1）**：计划书 §2.1 的三个方面均有真实文献覆盖 ✓。

> **重要边界（与 `09` §2.3 保持一致）**：本文 $B(\chi)$（$\chi_k=C_x z_k$，即输入矩阵依赖当前**测量**）在文献中**没有直接对应物**——`09` §2.3 的原登记范围是「在（甲）（乙）中**没有直接对应物**」，本件按该范围引用。本件 §2（LPV 重写）与 §3（误差界）提供的是**邻近**支撑：§2 说明「受控提升 + 状态相关调度」是既有框架，§3 说明「Lipschitz 型误差传播 + 有限时域界」是既有工具；但本文 $B(\chi)$ 的**测量依赖输入调制**这一具体形式，仍只能由 `02` 的 A3/A4 与命题 1/2 支撑。**本件不作「$B(\chi)$ 有文献直接对应物」的声称。**

---

## 2. 计划书 §2.2 — LPV / scheduling MPC

**计划书要求**：scheduling variable；**frozen parameter approximation**；LPV-MPC；quasi-LPV systems。**目标**：支撑冻结调度控制思想。**这是本文控制层设计（`06`–`08`）的直接文献基础。**

### 2.1 冻结/固定调度轨迹是既有做法（三条主流处理方式）

| # | 条目 | 等级 | 与本文的关系 |
|---|---|---|---|
| 2.1 | **arXiv:2403.19195**（2024），"Efficient Nonlinear Model Predictive Control by Leveraging LPV Embedding and SQP" | A | 明确把「调度参数在预测时域上未知」的处理方式分为三类：**(1) 冻结在当前测量值**（即 gain-scheduling predictive control，引 Gidon et al. 2021）；(2) 由上一时刻解外推（引 Nezami et al. 2023；Alcalá et al. 2020a；Karachalios & Abbas 2024）；(3) 对调度函数做局部 Taylor 展开（引 Morato et al.）。**本文 `06` 的冻结 LTV 问题正是 (1)** ✓。 |
| 2.2 | **Springer (2026)**，DOI `10.1007/s40313-026-01281-x`，"Nonlinear MPC Design using the qLPV Approach and IQC-based Terminal Ingredients" | A | 原文点名「**frozen/gain-scheduled approach** 是最简单的一种：在每个采样时刻把系统当作 LTI 处理，即 $\hat P_k = \mathrm{col}(\rho(k),\dots,\rho(k))$」，并指出尽管预测不确定性可能很大，该做法因简单而在实践中被广泛使用（引 Morato et al. 2020b；Alcalá et al. 2020）。**直接支撑 `06`–`08` 的冻结口径** ✓。 |
| 2.3 | **Morato, Normey-Rico, Sename (2020)**，"Model predictive control design for linear parameter varying systems: A survey"，*Annual Reviews in Control* 49:64–80，DOI `10.1016/j.arcontrol.2020.04.016` | A | LPV-MPC 综述；明确区分「**sub-optimal, simplified, yet QP algorithms**」与 tube/NP/robust 路线，并把 qLPV 调度代理 $\rho(k+j)=f_\rho(x(k+j))$ 的处理作为独立议题。**本文控制层属其中的「次优但 QP」分支** ✓。 |
| 2.4 | **Tóth (2010)**，LPV 框架（教科书） | A′ | qLPV/LPV 的标准记号来源。出处：`04` 检索 3 中 `arXiv:2403.19195` 原文「parameter-varying (LPV) framework (Tóth, 2010)」。 |

### 2.2 迭代式 qLPV MPC（qLMPC）与其次优性

| # | 条目 | 等级 | 与本文的关系 |
|---|---|---|---|
| 2.5 | **Cisneros, Voss, Werner (2016)**，qLMPC 原始提出 | A′ | 冻结参数轨迹 → LTV → QP，然后**迭代**更新调度轨迹。`06` 的单次冻结 QP 是其一次迭代。 |
| 2.6 | **arXiv:2309.07375**（2023），"Convergence Properties of Fast quasi-LPV Model Predictive Control" | A | **关键**：证明 qLMPC 的迭代不动点是**次优但可行**的解（满足一个线性扰动后问题的 FONC），并给出「用修正的虚构 LPV 系统（附加扰动项 $d_k$）可恢复最优性」的结论。**这正是本文 `08` 的条件次优性 $0\le J_{\text{full}}(u^{\text{fr}})-J_{\text{full}}(u^\*)\le 2\varepsilon_J$ 在文献中的对应物** ✓ —— 差别是：文献给的是「收敛到次优解」的定性结论，本文给的是**带显式 $\varepsilon_J$ 的两侧界**。 |
| 2.7 | **Hespe & Werner (2021)**，迭代 qLMPC 的收敛性 | A′ | 被 2.1/2.6 引用为「该迭代策略确实收敛」的依据。出处：`04` 检索 3 中 Springer (2026) 原文「In Hespe and Werner (2021), it is shown that such iterative strategy indeed converges」。 |
| 2.8 | **Cisneros & Werner (2020)**，"Nonlinear model predictive control for models in quasi-linear parameter varying form"，*Int. J. Robust Nonlinear Control* 30(10):3945–3959，DOI `10.1002/rnc.4973` | A | qLPV-NMPC 的系统化处理。 |
| 2.9 | **Cisneros & Werner (2019)**，"Wide Range Stabilization of a Pendubot using quasi-LPV Predictive Control"，*IFAC-PapersOnLine* 52(28):164–169，DOI `10.1016/j.ifacol.2019.12.367` | A | qLPV MPC 的应用实例。 |
| 2.10 | **Morato, Normey-Rico, Sename (2019)**，"Novel qLPV MPC Design with Least-Squares Scheduling Prediction"，*IFAC-PapersOnLine* 52(28):158–163，DOI `10.1016/j.ifacol.2019.12.366` | A | 调度序列的预测方式（最小二乘）。 |
| 2.11 | **"A qLPV Nonlinear Model Predictive Control with Moving Horizon Estimation"**（2021，oaepublish） | A | 用 MHE 估计调度序列；明确说三个 QP、可实时；并指出「qLPV 方法能对非线性系统给出**精确描述**，无需在线线性化或 Jacobian」——与本文的调度形式取向相关。 |
| 2.12 | **"NMPC Through qLPV Embedding: A Tutorial Review of Different Approaches"**（2021） | A | 教程式综述，给出 qLPV-NMPC 的三步通用结构：状态相关调度参数 → 沿时域的外推/估计 → 用估计值做线性预测。**本文 `06`–`07` 的「名义 rollout 驱动调度 + 冻结调度做 QP」与之一致** ✓。 |
| 2.13 | **Morato et al. (2022b)；Morato (2023)；Abbas et al. (2021)** | A′ | qLPV-MPC 的稳定性/终端成分相关工作。出处：`04` 检索 3 中 Springer (2026) 原文引用「cf. (Cisneros et al., 2016; Abbas et al., 2021; Morato et al., 2022b, a)」「cf. (Morato et al., 2020a; Morato, 2023)」「(Cisneros et al., 2016; Morato et al., 2022b)」。 |

**小结（§2）**：计划书 §2.2 的四个方面（调度变量 / 冻结参数近似 / LPV-MPC / quasi-LPV）**全部有真实文献覆盖** ✓，且**冻结调度是公认的既有做法**（2.1–2.3），其**次优性**在文献中有对应结论（2.6）。这是本文控制层最需要、也最扎实的一块。

---

## 3. 计划书 §2.3 — Prediction error bounds

**计划书要求**：Koopman approximation error；finite horizon prediction bound；Lipschitz error propagation。

| # | 条目 | 等级 | 与本文的关系 |
|---|---|---|---|
| 3.1 | **Nüske, Peitz, Philipp, Schaller, Worthmann (2023)**，"Finite-Data Error Bounds for Koopman-Based Prediction and Control"，*J. Nonlinear Sci.* 33:14，DOI `10.1007/s00332-022-09862-1` | A | **核心**：给出**依赖数据量**的概率性近似误差界与**多步预测误差界**（含控制仿射系统）。原文明确指出：既有方法给出的都是 $Ax+Bu$ 的**线性**代理，而「对一般控制仿射系统，数值研究表明**双线性**代理更合适」；并指出该文是「随机/控制设定下的**首个**有限数据误差分析」。**本文 `05`（定理 1）与 `07`（定理 2）属于「有限时域预测误差界」这一族** ✓。 |
| 3.2 | **Mamakoukas, Di Cairano, Vinod (2022)**，"Robust Model Predictive Control with Data-Driven Koopman Operators"（ACC 2022；MERL TR2022-054） | A | **与本文最接近的一条**：假设未知动力学 **Lipschitz 连续**，用训练误差近似**状态-控制相关模型误差的 Lipschitz 常数**，再**沿预测时域给出预测误差上界**，并据此构造凸的鲁棒有限时域 OCP。其命题 1（"$f$ 是 $L_f$-Lipschitz ⟹ 建模误差 Lipschitz，常数 $L=L_f+\|C[A\ B]\|$"）在结构上与本文 `05`/`07` 的常数构造同族 ✓。原文也如实指出**主要局限**：结论依赖 Lipschitz 常数的**精确值或上界**，而后者通常难以获得。 |
| 3.3 | **Philipp, Schaller, Worthmann, Peitz, Nüske (2024)**，"Error bounds for kernel-based approximations of the Koopman operator"，*Appl. Comput. Harmon. Anal.* 71:101657，DOI `10.1016/j.acha.2024.101657` | A | 核方法下的**有限数据估计误差**与 **RKHS 预测误差界**（Mercer 截断）。与 3.1 同一课题组，构成「数据量 → 误差」的完整链。 |
| 3.4 | **Worthmann et al.**，arXiv:2501.08709 | A | 由 kEDMD 的**逐点比例误差界**（proportional in the state）推出 kEDMD-MPC 的**实用渐近稳定**（PAS），并强调**避免不变性条件**。**这是「误差界 → 闭环保证」的桥**，也说明本文若想走到闭环结论需要哪一类额外假设（本文**未**走到那一步 ✓）。 |
| 3.5 | **DOI `10.1016/j.automatica.2026.113069`**，"Robust tracking MPC for nonlinear constrained systems via online-updated Koopman operators"，*Automatica* (2026) | A | 同样假设建模误差 Lipschitz、由训练误差估计常数、**给出沿时域的预测误差界**，并建立 ISS。与 3.2 一脉。 |
| 3.6 | **SIAM DOI `10.1137/24M1650120`**，"Error Bounds for Approximations of the Koopman Operator"（kEDMD 逐点界） | A | 借助 Wendland 核的 RKHS 不变性 + 插值估计给出**逐点**近似误差界。 |
| 3.7 | **Köhler 等 (2025)**（作者归属**待核实**：可见片段中作者名残缺），SIAM J. Control Optim.（卷期页在可见片段中不完整） | A′ | 「Kernel-based Koopman surrogates for control」一系。**作者、卷期页均待核实**。 |
| 3.8 | **Zhang & Zuazua (2021)；Kurdila & Bobade (2018)；Schaller et al. (2022)** | A′ | 投影误差（有限字典尺寸）与数据误差的分工。 |

**小结（§3）**：计划书 §2.3 的三个方面（Koopman 近似误差 / 有限时域预测界 / Lipschitz 误差传播）**全部有真实文献覆盖** ✓。要点：文献中的预测误差界**普遍依赖 Lipschitz 型假设 + 训练/投影误差的已知上界**（3.2 明确说这是其主要局限）；本文 `05`/`07` 采取的是**同族但自足**的做法——把 $\delta_u$、$\delta_{\mathrm{frz}}$ 作为**假设量**显式引入，而不假装能从数据估出（`05` A5、`07` 的 $\Delta_u,\delta_u$ 说明）。

---

## 4. 计划书 §2.4 — Approximate MPC theory

**计划书要求**：model mismatch MPC；**frozen model MPC**；**suboptimality bound**；approximate optimization MPC。

| # | 条目 | 等级 | 与本文的关系 |
|---|---|---|---|
| 4.1 | **Diehl, Bock, Schlöder et al. (2005)**，"A Real-Time Iteration Scheme for Nonlinear Optimization in Optimal Feedback Control"，*SIAM J. Control Optim.*（**卷期页待核实**），DOI `10.1137/S0363012902400713` | A | **近似优化 MPC 的奠基文献**：每采样时刻只做一次 SQP；原文明确「证明了该实时迭代格式的压缩性，并给出**相对理论最优解的次优性损失的一个界**」。**这是 `08` 的「条件次优性」在算法层面的对应物** ✓（注意：是**算法层面**的对应物，不是「冻结调度」这一失配来源的对应物，见 §7 第 2 条）。 |
| 4.2 | **Diehl, Bock, Schlöder et al. (2005)**，"Nominal stability of real-time iteration scheme for nonlinear model predictive control" | A | RTI 的名义稳定性：给出**近似反馈相对理想 NMPC 的误差界**（误差对 Newton 步长**二次**），并说明闭环稳定性**不能**由标准 NMPC 理论直接推出（需把「系统动力学 + 优化器动力学」联合分析）。**本文 `08` 明确不声称闭环稳定，正是这一点的体现** ✓。 |
| 4.3 | **Nurkanović, Frey et al. (2024)**，arXiv:2403.07101，"Advanced-Step Real-Time Iterations with Four Levels — New Error Bounds and Fast Implementation in acados" | A | 给出各级 MLI 的**误差界**与**相对次优性（relative suboptimality, %）**的实测对照表（RTI 3.55% vs AS-RTI-A 0.54% 等）。**「近似优化 → 次优性界 + 实测次优性」这一评价范式与 `08` 一致** ✓。 |
| 4.4 | **Nurkanović et al. (2019)**，"The Advanced Step Real Time Iteration for NMPC"；**(2020)**，"Contraction Properties of the Advanced Step Real-Time Iteration for NMPC" | A | AS-RTI 的压缩性与**数值误差有界性**。 |
| 4.5 | **Zanelli et al. (2017)**，"A Partially Tightened Real-Time Iteration Scheme for NMPC" | A | 近似 RTI 的下降性/稳定性讨论，并如实说明「严格稳定性分析超出本文范围、仍在进行中」——**与本文对未完成结论的克制表述一致** ✓。 |
| 4.6 | **arXiv:2405.15552**，"Stability and Performance Analysis of Model Predictive Control of Uncertain Linear Systems" | A | **model mismatch MPC**：真模型与估计模型之间有 Frobenius 范数意义下的参数失配；用松弛动态规划给出**次优性间隙**的界，并说明预测时域与建模误差如何影响该间隙。**与本文 `08` 的 $\varepsilon_J$ 思路同族**（差别：本文的失配来自**冻结调度**而非参数辨识误差）。 |
| 4.7 | **arXiv:2309.07375**（同 2.6） | A | 既是「冻结参数 MPC」也是「次优性界」的文献；**一个条目同时覆盖计划书 §2.2 与 §2.4** ✓。 |
| 4.8 | **Zavala & Anitescu (2010)；Ohtsuka (2004)（C/GMRES）；Bock et al. (2007)（MLI）；Zavala & Biegler (2009)（ASC）** | A′ | 近似优化/实时 NMPC 的其它主线。出处：`04` 检索 5 中 `arXiv:2403.07101` 与 syscop AS-RTI 压缩性论文原文引用「(Zavala and Anitescu, 2010; Zanelli et al., 2019)」「(Zavala and Biegler, 2009)」「(Ohtsuka, 2004)」「(Bock et al., 2007)」。 |
| 4.9 | **Mayne et al. (2000)**，终端成分 | A′ | 稳定性分析的终端成分标准结果。出处：`04` 检索 3 中 Springer (2026) 原文「the standard terminal ingredient synthesis argument from (Mayne et al., 2000)」。 |

**小结（§4）**：计划书 §2.4 的四个方面**全部有真实文献覆盖** ✓。要点：文献中的次优性结论主要来自**算法层**（RTI/AS-RTI：数值误差与次优性损失）与**模型失配层**（4.6）；**「冻结调度」这一特定失配来源的显式两侧界，本轮检索未见直接对应物** → 这正是本文 `08` 的定位（见 §7 第 2 条）。

---

## 5. 与理论包 `01`–`08` 的对应关系（本件只做定位，不改任何一件）

| 理论包结果 | 本件的文献支撑 | 是否已有直接对应物 |
|---|---|---|
| `01`/`03` 模型与低秩有界性（命题 1） | §1（受控 Koopman 代理的合理性）；§2.2（调度变量与 qLPV 嵌入） | **部分**：$A(c)$ 的「受控提升 + 状态相关调度」是既有框架 ✓；但 $B(\chi)$ 的**测量依赖输入调制**在文献中**没有直接对应物**（见 §1 的边界框与 `09` §2.3），只能由 `02` 的 A3/A4 与命题 1/2 支撑 |
| `04` 调度 Lipschitz（命题 2） | §1.8、§2.2（调度函数的光滑性假设在 qLPV 文献中常见） | **部分**：文献通常**假设**光滑性，本文给出**显式常数** |
| `05` 预测误差界（命题 3 + 定理 1） | §3.1、§3.3、§3.8（有限时域预测界、投影/数据误差） | **是**（同族）；本文的差别是**不假装能从数据估出残差上界**，而把 $\delta_u$ 作为假设量 |
| `06` 冻结 LTV-QP（命题 4） | §2.1–2.3（冻结调度是公认做法）；§2.4（近似优化） | **是**：冻结调度 → LTV → QP 是标准路线 |
| `07` 冻结误差界（定理 2） | §3.2（Lipschitz 模型误差 → 沿时域预测误差界） | **部分**：结构同族；本文针对的是**同一输入序列下 full vs frozen** 的差，而非「真模型 vs 代理模型」的差 |
| `08` 条件次优性（定理 3） | §2.6（qLMPC 收敛到次优解）、§4.1（RTI 的次优性损失界）、§4.6（模型失配次优性间隙） | **部分**：次优性有文献对应物，但**本文的 $\varepsilon_J$ 是显式的、且针对冻结调度** |

---

## 6. 检索方法与诚实边界

- 本轮共 **5 次**检索，查询串与结果要点见 `../notes/literature/04_sc2_search_log.md`（本件所有等级 A 条目均可在该日志中找到出处）。
- **等级 A 的含义有限**：表示本轮**检索输出中可见**题名/DOI/arXiv ID，**不等于**已核对原文全部元数据（作者顺序、卷期页、年份）。凡本件标注「待核实」或「卷期页不完整」者，**不得**直接用作论文引用键。
- **未做的事**（避免误读）：
  - 没有打开任何一篇原文的全文（除检索输出中的摘要/片段）；
  - 没有核对任何 DOI 是否可解析（本会话检索工具不提供解析验证）；
  - 没有对文献的**实验设置、结果数字或优先权**作独立判断（§4.3 转述的 3.55% / 0.54% 等数字是**该文自身的实测表**，本件只是引用，未作评估，也未据此作任何本文性能声称）；
  - 没有把本件的任何条目写进 `09`（`09` 字节保持不变）；
  - 没有在本件中引入「bilinear Koopman」术语（`DEC-079`），也没有声称实时性/闭环稳定/递归可行。

---

## 7. 未解决问题（登记）

1. **计划书 §6.1 所指「双线性 Koopman 论文」的具体身份**仍未定（`09` §2.4、`09` §4 第 5 条、`00_Index.md` §6 第 2 条）。本件 §1.11 与 §1.12 **不是**对该问题的回答。
2. **「冻结调度」这一特定失配来源的显式两侧次优性界，本轮未见直接对应物**。最接近的是 2.6（qLMPC 收敛到次优解，定性）与 4.1/4.6（算法误差/参数失配的次优性界，不同失配来源）。→ 论文写作时，`08` 的贡献表述应写成「针对冻结调度给出显式 $\varepsilon_J$ 的条件次优性」，而**不是**「首次给出次优性界」。
3. **§3.7 的作者与卷期页待核实**；§1.12 与旧稿未引条目 `strasser2026overview` 是否同一篇**未核实**；§4.1 的卷期页待核实。
4. 本件是**尽力而为**检索的产物（`DEC-081`）；若用户提供计划书 §6.1 所指论文，§1/§3 可能需要重做。
