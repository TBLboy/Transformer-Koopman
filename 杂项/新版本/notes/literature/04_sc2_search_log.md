# 计划书第二阶段（§2.1–§2.4）文献检索日志

> **用途**：为 `Theory_Package/10_Reference_List_Supplement.md` 提供**可追溯的检索出处**。
> **口径**：`DEC-081` —— 文献调研降级为**尽力而为、不作为前置**；检索不到的不编造。
> **时间**：2026-10-11（`TASK-042` 的 `RUN-042`）。
> **工具**：本会话的网页检索工具（返回聚合的搜索摘要与片段）。

---

## 检索 1 — 计划书 §2.1 Koopman controlled systems

**查询串**：`input-affine Koopman operator control finite-dimensional approximation lifting`

**可见输出**：
- `arXiv:2201.05098` —— 摘要：用 learner/falsifier 同时学习**双线性 Koopman 嵌入**与控制 Lyapunov 函数（CLF），对未知控制仿射非线性系统给出可证明的渐近稳定性；摘要提到「控制系统的双线性控制模型」与「可稳定的提升双线性控制系统的辨识仍是开放问题」。
- 其余结果在传输中被截断（未见内容），故**未采信**。

**采信**：`10_Reference_List_Supplement.md` §1.11（等级 **A**，本轮直接检索命中；题名未在可见片段中显示）。

---

## 检索 2 — 计划书 §2.2 LPV / scheduling MPC（第一次）

**查询串**：`quasi-LPV model predictive control scheduling variable frozen parameter approximation`

**可见输出**：
- `arXiv:2309.07375`（2023-09-14）—— "Convergence Properties of Fast quasi-LPV Model Predictive Control"：固定 qLPV 系统的参数轨迹、从而暂时忽略参数对状态/输入的依赖，系统变为 LTV，MPC 可写成 QP；该过程迭代进行。主贡献：给出迭代收敛的条件，并**证明迭代不动点是原 NLP 的次优解**。
- 其余结果在传输中被截断（未见内容），故**未采信**。

**采信**：§2.6（等级 A）。

---

## 检索 3 — 计划书 §2.2 LPV / scheduling MPC（第二次，补充）

**查询串**：`quasi-LPV MPC frozen scheduling parameter QP iteration LPV-MPC survey nonlinear MPC`

**可见输出**（本次输出完整，是 §2 的主要来源）：
- `arXiv:2309.07375` 全文片段 —— 明确 qLMPC 与 SQP 的等价性（Gauss–Newton 近似）、「次优但可行」、以及「用虚构 LPV 系统（附加扰动 $d_k$）可恢复最优性」。
- **"NMPC Through qLPV Embedding: A Tutorial Review of Different Approaches"**（2021）—— 三步通用结构（状态相关调度参数 → 沿时域外推 → 线性预测）；参考文献表可见完整题录：
  - Cisneros & Werner (2019), *IFAC-PapersOnLine* 52(28):164–169, DOI `10.1016/j.ifacol.2019.12.367`
  - Morato, Normey-Rico, Sename (2019), *IFAC-PapersOnLine* 52(28):158–163, DOI `10.1016/j.ifacol.2019.12.366`
  - Cisneros & Werner (2020), *Int. J. Robust Nonlinear Control* 30(10):3945–3959, DOI `10.1002/rnc.4973`
  - Morato, Normey-Rico, Sename (2020), *Annual Reviews in Control* 49:64–80, DOI `10.1016/j.arcontrol.2020.04.016`
- **Springer (2026)**，DOI `10.1007/s40313-026-01281-x` —— 点名 **frozen/gain-scheduled approach**：$\hat P_k=\mathrm{col}(\rho(k),\dots,\rho(k))$；指出其预测不确定性可能很大但因简单而被广泛使用（引 Morato et al. 2020b；Alcalá et al. 2020）。
- **Morato et al. (2020) 综述**（Scribd 版本）—— LPV-MPC 综述全文片段：明确把方法按保守性排序，从 robust/tube/参数变化率有界，到 **sub-optimal, simplified, yet QP algorithms**，再到 NP 方法。
- `arXiv:2403.19195`（2024）—— "Efficient Nonlinear Model Predictive Control by Leveraging LPV Embedding and SQP"：**调度参数沿时域未知的三类处理方式**（冻结在测量值 / 由上一时刻解外推 / Taylor 展开），并给出引用（Gidon et al. 2021；Nezami et al. 2023；Alcalá et al. 2020a；Karachalios & Abbas 2024；Morato et al.）；参考文献表可见 `Cisneros, P.S.G., Voss, S., and Werner, H. (2016)`。
- **"A qLPV Nonlinear Model Predictive Control with Moving Horizon Estimation"**（2021，oaepublish）—— 三个 QP（MPC + MHE 预测调度序列）；指出 qLPV 嵌入可**精确描述**非线性系统、无需在线线性化或 Jacobian。
- `rolandtoth.eu` CDC2017 "Stabilizing Non-Linear MPC Using Linear Parameter-Varying Representations" —— LPV 预测模型 + 终端成分的稳定性。
- **本检索输出中另外可见的二级引用名**（用于 `10` 的 A′ 条目出处）：
  - **Tóth (2010)** —— `arXiv:2403.19195` 原文「parameter-varying (LPV) framework (Tóth, 2010)」。
  - **Hespe & Werner (2021)** —— Springer (2026) 原文「In Hespe and Werner (2021), it is shown that such iterative strategy indeed converges」。
  - **Morato et al. (2022b)；Morato (2023)；Abbas et al. (2021)；Cisneros et al. (2016)** —— Springer (2026) 原文引用「cf. (Cisneros et al., 2016; Abbas et al., 2021; Morato et al., 2022b, a)」「cf. (Morato et al., 2020a; Morato, 2023)」「(Cisneros et al., 2016; Morato et al., 2022b)」。
  - **Mayne et al. (2000)** —— Springer (2026) 原文「the standard terminal ingredient synthesis argument from (Mayne et al., 2000)」。
  - **Gidon et al. (2021)；Nezami et al. (2023)；Alcalá et al. (2020a)；Karachalios & Abbas (2024)；Morato et al.** —— `arXiv:2403.19195` 原文列出的调度参数三类处理方式的引用。
  - **Alcalá et al. (2020)；Morato et al. (2020b)** —— Springer (2026) 原文（frozen/gain-scheduled 的实践引用）。

**采信**：§2.1（2.1–2.4）、§2.2（2.5–2.13）。

---

## 检索 4 — 计划书 §2.3 Prediction error bounds

**查询串 1**：`Koopman approximation error bound finite horizon prediction Lipschitz propagation control`
**查询串 2**：`Koopman MPC prediction error bound Lipschitz constant truncation error guarantee`

**可见输出**：
- **Nüske, Peitz, Philipp, Schaller, Worthmann (2023)**, *J. Nonlinear Sci.* 33:14, DOI `10.1007/s00332-022-09862-1` —— 摘要与正文片段：概率性的近似误差界与多步预测误差界（依赖数据量 $m$）；扩展到控制仿射系统；明确「既有方法都给出 $Ax+Bu$ 的线性代理，而对一般控制仿射系统数值研究表明双线性代理更合适」；并给出大量相关工作引用（Proctor et al. 2016；Korda & Mezić 2018a/2018b；Kaiser et al. 2021；Mamakoukas et al. 2021；Lu et al. 2020；Peitz & Klus 2019；Peitz et al. 2020；Goswami & Paley 2017；Bruder et al. 2021；Peitz & Bieker 2021；Schaller et al. 2022；Kurdila & Bobade 2018；Zhang & Zuazua 2021）。
- **Mamakoukas, Di Cairano, Vinod (2022)**，ACC 2022，MERL TR2022-054 —— 全文片段：假设未知动力学 Lipschitz 连续，用训练误差近似**状态-控制相关模型误差的 Lipschitz 常数**，沿预测时域给出预测误差上界，构造凸鲁棒有限时域 OCP；命题 1：$L = L_f + \|C[A\ B]\|$；并如实说明主要局限是依赖 Lipschitz 常数的精确值/上界。
- **Philipp, Schaller, Worthmann, Peitz, Nüske (2024)**, *Appl. Comput. Harmon. Anal.* 71:101657, DOI `10.1016/j.acha.2024.101657` —— 核方法下的有限数据估计误差与 RKHS 预测误差界（Mercer 截断）。
- **SIAM DOI `10.1137/24M1650120`** —— kEDMD 逐点近似误差界（Wendland 核 RKHS 不变性 + 插值估计）。
- **Worthmann et al., arXiv:2501.08709** —— 由 kEDMD 的逐点**比例**误差界推出 kEDMD-MPC 的实用渐近稳定（PAS），强调避免不变性条件。
- **DOI `10.1016/j.automatica.2026.113069`**, *Automatica* (2026) —— "Robust tracking MPC for nonlinear constrained systems via online-updated Koopman operators"：Lipschitz 建模误差 + 沿时域预测误差界 + ISS。
- **TU Ilmenau（Worthmann）讲稿** "Koopman operator in dynamics & control: From error bounds to closed-loop guarantees" —— 概括「比例误差界 + 成本可控性 ⟹ 松弛 Lyapunov 不等式」的闭环保证链条；提及 SIAM J. Control Optim. 63(...):4044–4077（卷期页在片段中不完整）。
- **"An overview of Koopman-based control: From error bounds to closed-loop guarantees"**（Review article，ScienceDirect）—— 摘要：把「数据驱动代理模型 → 近似误差 → 控制器设计 → 闭环保证」系统化，覆盖线性与双线性 EDMD 控制方案。

**采信**：§3.1–3.8。

---

## 检索 5 — 计划书 §2.4 Approximate MPC theory

**查询串 1**：`model mismatch MPC suboptimality bound approximate optimization frozen model`
**查询串 2**：`real-time iteration RTI suboptimality bound approximate MPC optimization error`

**可见输出**：
- **Diehl, Bock, Schlöder et al. (2005)**，*SIAM J. Control Optim.*，DOI `10.1137/S0363012902400713` —— 摘要：「该实时迭代格式的压缩性被证明，并给出相对理论最优解的**次优性损失的一个界**」。
- **Diehl, Bock, Schlöder et al. (2005)**，"Nominal stability of real-time iteration scheme for nonlinear model predictive control" —— 全文片段：近似反馈相对理想 NMPC 的**误差界**（对 Newton 步长二次，定理 4.2）；明确指出闭环稳定性**不能**由标准 NMPC 理论直接推出，需要分析「系统 + 优化器」联合动力学；并给出两阶段（先允许目标值上升、误差缩小后再保证下降）的分析。
- **Nurkanović, Frey et al. (2024)**，`arXiv:2403.07101` —— AS-RTI 四级 MLI 的误差界（反馈相位误差界 (12)/(13)）与**相对次优性（%）**实测表（SQP-100 0.05%、RTI 3.55%、AS-RTI-A 0.54% 等）。
- **Nurkanović et al. (2019)**，"The Advanced Step Real Time Iteration for NMPC"；**(2020)**，"Contraction Properties of the Advanced Step Real-Time Iteration for NMPC" —— 压缩性与数值误差有界性的充分条件。
- **Zanelli et al. (2017)**，"A Partially Tightened Real-Time Iteration Scheme for NMPC" —— 部分收紧的 RTI；如实声明严格稳定性分析超出范围、仍在进行中。
- **`arXiv:2405.15552`**，"Stability and Performance Analysis of Model Predictive Control of Uncertain Linear Systems" —— 参数失配（Frobenius 范数）下的 MPC；用松弛动态规划给出**次优性间隙**的界，并说明预测时域与建模误差的影响。
- **本检索输出中另外可见的二级引用名**（用于 `10` 的 A′ 条目出处）：**Zavala & Anitescu (2010)**、**Ohtsuka (2004)（C/GMRES）**、**Bock et al. (2007)（MLI）**、**Zavala & Biegler (2009)（ASC）** —— 见 `arXiv:2403.07101` 与 syscop AS-RTI 压缩性论文原文「(Zavala and Anitescu, 2010; Zanelli et al., 2019)」「(Zavala and Biegler, 2009)」「(Ohtsuka, 2004)」「(Bock et al., 2007)」。

**采信**：§4.1–4.9。

---

## 汇总

| 检索 | 计划书主题 | 采信条目数（本件编号） |
|---|---|---|
| 1 | §2.1 Koopman controlled systems | 1（1.11） |
| 2 | §2.2 LPV / scheduling MPC（第一次） | 1（2.6） |
| 3 | §2.2 LPV / scheduling MPC（第二次） | 13（2.1–2.13） |
| 4 | §2.3 Prediction error bounds | 8（3.1–3.8）＋**§1 的 A′ 群**（1.1–1.10，来自 Nüske et al. 2023 的相关工作段）＋1.12（等级 A，来自综述本身） |
| 5 | §2.4 Approximate MPC theory | 9（4.1–4.9；其中 **4.9 的出处为检索 3**） |

**共 5 次检索**。计划书 §2.1 的条目主要来自**检索 1**（部分截断，仅采信 1 条）与**检索 4** 中 Nüske et al. 2023 的相关工作段（等级 A′，供给 1.1–1.10）；**1.12**（等级 A）来自综述本身（检索 4）；§2.2 的条目主要来自**检索 3**（完整可见，含其二级引用名）；§2.3 的条目来自**检索 4**；§2.4 的条目来自**检索 5**（其中 **4.9 的出处为检索 3**）。

**检索 4 的两条内容性补记**（供 `10` 的 A′ 出处追溯）：
- Nüske et al. 2023 §1 原文：「The technique proposed in Peitz and Klus (2019); Peitz et al. (2020) constructs its surrogate model from $n_c+1$ autonomous Koopman operators, where $n_c$ is the control dimension.」（对应 `10` §1.7）
- 同段原文列出「All approaches mentioned until now yield linear surrogate models of the form $Ax+Bu$, i.e., the control enters linearly. For general control-affine systems, numerical simulation studies indicate that bilinear surrogate models are better suited」（对应 `10` §1.8）。

**等级标注的追溯规则**：`10` 中每个 **A** 级条目都能在本日志找到题名/DOI/arXiv ID/卷期页；每个 **A′** 级条目都能在本日志找到「由哪一篇 A 级文献的哪一句引用」。**标「待核实」者不得用作论文引用键。**

**未采信的部分**：检索 1、2 的输出在传输中被截断，除已列出的条目外**一律未采信**（不编造未见内容）。
