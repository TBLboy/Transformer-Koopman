# 基线文献核实清单（WP-M 用到的基线）

> **状态**：临时实验材料，**不是论文正文**。
> **规则**：只写核实过的元数据；未核实的**显式标注**；不因方法同名就宣称等价复现（计划书 §13）。

## 1. 元数据核实结果（2026-10-11 网络检索）

| # | 方法 | 文献 | 出版元数据 | 官方实现 | 本轮核实 |
|---|---|---|---|---|---|
| 1 | EDMD（固定字典） | Williams, Kevrekidis, Rowley (2015), *A data-driven approximation of the Koopman operator: extending dynamic mode decomposition* | *J. Nonlinear Sci.* **25**(6), 1307–1346, DOI `10.1007/s00332-015-9258-5` | — | ✅ 已核实（多个独立来源交叉一致） |
| 2 | DMDc（含控制） | Proctor, Brunton, Kutz (2016), *Dynamic mode decomposition with control* | *SIAM J. Appl. Dyn. Syst.* **15**(1), 142–161, DOI `10.1137/15M1013857` | — | ✅ 已核实 |
| 3 | EDMD-DL（可学习字典） | Li, Dietrich, Bollt, Kevrekidis (2017), *Extended dynamic mode decomposition with dictionary learning: A data-driven adaptive spectral decomposition of the Koopman operator* | *Chaos* **27**(10), 103111, DOI `10.1063/1.4993854`（PubMed PMID 29092410） | — | ✅ 已核实（计划书要求核对出版元数据，已核对一致） |
| 4 | Deep Koopman | Lusch, Kutz, Brunton (2018), *Deep learning for universal linear embeddings of nonlinear dynamics* | 计划书给出 DOI `10.1038/s41467-018-07210-0` | — | ⚠️ **待核实**（本轮未独立核实该 DOI 与卷期页） |
| 5 | PatchTST | Nie, Nguyen, Sinthong, Kalagnanam (ICLR 2023), *A Time Series is Worth 64 Words: Long-term Forecasting with Transformers* | arXiv `2211.14730`；ICLR 2023（OpenReview `Jbdc0vTOcol`）；会议论文，无 DOI | `https://github.com/yuqinie98/PatchTST` | ✅ 已核实 |
| 6 | DLinear | Zeng, Chen, Zhang, Xu (AAAI 2023), *Are Transformers Effective for Time Series Forecasting?* | arXiv `2205.13504`；AAAI 2023；会议论文，无 DOI | `https://github.com/honeywell21/DLinear` | ✅ 已核实 |

## 2. 本研究实际用了什么、改了什么（**不宣称等价复现**）

| 我们的 ID | 对应文献 | 我们实现的部分 | 我们的改造点 / 与原文的差异 |
|---|---|---|---|
| M0 | #2 DMDc | `x_{k+1} = A x_k + B u_k`，闭式最小二乘（可选延迟嵌入） | 原文面向高维快照；我们只用 2 维测量 + 2 维输入，且加入可选延迟嵌入作为 sanity baseline |
| M1 | #1 EDMD + #2 的控制扩展 | 固定字典 `ψ(x)=[x, poly2(x), (RBF)]`，岭回归求 `z⁺ = A z + B u` | **EDMD 本身不含控制**；"EDMD with control" 是把 DMDc 的思路接到 EDMD 字典上，属**我们的组合**，不是原 EDMD 论文的直接结论 |
| M2 | #3 EDMD-DL | 可学习字典 `ψ_θ(x)=[x; MLP(x)]` + 线性受控 latent 动力学；**交替最小二乘**（每 5 epoch 用当前字典重解 A,B）与 encoder 梯度步交替 | 原文 EDMD-DL 是**无控制**的（Duffing/KS 例子）；**受控版本是本项目自行定义的扩展**，不能冒称原文直接给出该实现（计划书 §3.2 明确要求这一点） |
| M3 | 通用 RNN 基线 | GRU/LSTM 在 `(x_t,u_t)` token 上编码历史，递推时逐步喂入已知未来 `u` | 原文无；属标准做法。注意：我们**每次递推都重新编码整段窗口**，与"carry hidden state"的常见写法不同，已在报告中注明 |
| M6 | #5 PatchTST 的**思路**（patch 编码） | 小规模因果 Transformer 在 `(x_t,u_t)` token 上；递推时把预测测量与已知未来 `u` 追加为 token | **不是** PatchTST 复现：无 channel-independence、无官方 patch 超参（patch=16/stride=8）、无自监督预训练、无长回看窗口，且必须**显式条件于未来控制输入**（原文是纯预测任务，无控制输入） |
| M4/M5/M7 | 本项目理论包 | `A(c)=A_0+U_A diag(γ_A(c))V_Aᵀ`，`B(χ)=B_0+U_B diag(γ_B(χ))V_Bᵀ` | 理论来源是 `Theory_Package/01`（本项目），**不是**上述任何文献的直接形式；低秩 + 有界调度是本研究的主模型 |
| M8/M9 | #5 / #4 | — | **未实现**（计划书列为可选）。因此本报告**不**给出与 PatchTST/Deep Koopman 的对比结论 |

## 3. 数据泄漏风险检查（计划书 §13 要求）

| 风险 | 我们的处理 |
|---|---|
| 用未来真实测量 | rollout 只读起点真实历史；`ScheduledKoopman.rollout` 采用 latent 递归传播（单测 T7 断言 encoder 一次 rollout 只调 1 次）；`X_i` 由传播后的 `C_x z_j` 构成 |
| 用未来控制输入 | 允许且**对全部模型一致**：`u_{k:k+H-1}` 作为已知外部输入（闭环控制中本来就已知）；这不是泄漏 |
| 训练/测试重叠 | 按**完整轨迹** 70/20/10 划分，滑动窗口不跨轨迹、不跨划分 |
| 归一化泄漏 | 归一化常数只在 train 拟合并冻结（`models/protocol.py`） |
| 用测试集选超参 | 选择只用 validation 多步 RMSE；test 在超参冻结后只评估一次（`run_gate1.py` 的 stage 划分） |
| 直接多步 vs 递推混淆 | 所有模型统一用**递推（autoregressive）**接口评估；teacher-forcing 误差（one-step）与自由 rollout 误差**分列**，不混报 |

## 4. 开源许可与引用准确性

- 我们**没有**复制 #5/#6 的官方代码，M6 是自写的小型因果 Transformer；因此不涉及它们的许可证条款。
- M0/M1/M2 为自行实现的标准最小二乘 / 岭回归 / MLP 字典，未复制第三方实现。
- 引用准确性：本报告**不**声称任何"复现了原文结果"；差异已在上表逐项列出。

## 5. 待办（本轮未完成，不掩盖）

1. **#4 Lusch et al. (2018) 的 DOI 待独立核实**（若论文需要引用该条目）。
2. 计划书 §13 要求的"阅读原论文的任务定义、输入信息、训练目标与预测方式"目前只做了**元数据核实与改造点对照**；
   **逐篇精读尚未完成**，因此本文件不给出"与原论文设定一致/不一致"的逐条判断。
3. M8（PatchTST-style 受控预测器）与 M9（Deep Koopman）未实现，故**没有**对应比较结论。
