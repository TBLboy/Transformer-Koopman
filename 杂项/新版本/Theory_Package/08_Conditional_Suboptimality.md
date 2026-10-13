# 08 条件次优性（Theorem 3）

> **状态**：前期材料，**不是论文正文**；不含实验数值。
> **对应计划书**：第六阶段「次优性条件」（计划书 Q3：用 $0 \le J_{\mathrm{full}}(u^{\mathrm{fr}}) - J_{\mathrm{full}}(u^\star) \le 2\varepsilon_J$ 的**条件形式**，**不假设** $CN(\delta_A + \delta_B)$）。
> **依赖**：显式成本界用`02`A1的全可行集统一量词、A3、`03`/`04`、`06`/`07`，不需A2/A5；抽象定理只用共同可行集、两个全局argmin和(CA)。控制测量空间口径按DEC-093。

---

## 1. 两个代价函数

固定当前提升状态 $z_k$、共同初始历史、测量参考 $\{x_i^{\mathrm{ref}}\}$、合法名义输入 $\bar U\in\mathcal U_{\mathrm{feas}}$、时域 $N$、权重与上一拍输入；沿用`06`的输出成本与索引，不定义latent参考。

**(a) 完整代价** $J_{\mathrm{full}}(U)$：按 `06` §1，轨迹用**完整模型**（调度由自己的轨迹生成）。

**(b) 冻结代价** $J_{\mathrm{fr}}(U; \bar U)$：按`06`§4，轨迹用冻结LTV模型；输出权重 $\bar Q_x$、输入/增量权重 $\bar R,\bar S$ 与full代价相同。

**关键结构性事实**：两个代价的**输入项完全相同**，故在作差时**自动抵消**。具体地（`06` §4 已统一记号）：

- $R$ 项：两侧都是 $\|U - U^{\mathrm{ref}}\|_{\bar R}^2$，**逐项相同**；
- $S$ 项：两侧都是 $\sum_{i=0}^{N-1}\|u_i - u_{i-1}\|_S^2$（$u_{-1}$ 为已知常数），**逐项相同**——`06` 第一版曾把它写成含参考速率的 $\|DU - DU^{\mathrm{ref}}\|^2$，那会破坏抵消，现已修正；
- 唯一差异来自输出状态项 $Q_x$ 与终端项 $P_x$。

因此只有预测输出项产生差异。两侧均从 $i=1$ 计状态成本，$i=N$仅计终端项，不再存在旧版单侧初始常数 $c_0$。若两侧同时加入相同 $i=0$ 成本，该常数在成本差中抵消；$N=1$时仅终端输出项产生差异。

## 2. 一致代价近似（**假设**，且给出可计算的显式上界）

### 假设 (CA)

$$
\sup_{U \in \mathcal{U}_{\mathrm{feas}}} \big| J_{\mathrm{full}}(U) - J_{\mathrm{fr}}(U; \bar U) \big| \;\le\; \varepsilon_J .
$$

> 抽象次优性定理以(CA)为条件。下面在统一工作域与`07`条件下构造显式上界；若这些常数未经认证，不能将经验估计当作(CA)对全可行集的证明。计划书禁止直接假设 $CN(\delta_A+\delta_B)$，不禁止从明确条件推导成本界。

### $\varepsilon_J$ 的显式上界（**可推导**）

由 `07` 定理 2，两条轨迹之差满足 $\|e_i\|_2 \le K_i$，其中

$$
K_i \;:=\; \delta_{\mathrm{frz}} \sum_{t=0}^{i-1} L^{\,i-1-t},
\qquad
\delta_{\mathrm{frz}} = L_A L_\phi M_Z\, \Delta_u \;+\; \big( L_A L_\phi \sqrt{P}\, M_Z + L_B M_U \big)\, M_B\, \delta_u \sum_{t=0}^{N-1} M_A^{\,t},
$$

其中 $\delta_{\mathrm{frz}}$ 取自`07`第二版。固定 $\bar U$ 后，$\Delta_u,\delta_u$ 取全可行集上的上确界（紧输入集下有限）。**还必须按`02`A1统一量词，对每个可行 $U$ 使用同一个 $M_Z,M_U$ 和full/nominal窗口正则域、$L_\phi$**。这些前提一起保证 $K_i$ 对全部可行 $U$ 一致成立；只对输入偏差取supremum并不足够。A1工作域是适用条件，不是额外加入QP的状态约束。

**常量来源**：$M_A,M_B$来自`03`；$L_A,L_B$来自`04`；$L_\phi,M_Z,M_U$来自`02`；$P$仅为历史长度；$\delta_u,\Delta_u,L,\delta_{\mathrm{frz}}$来自`07`。定义 $M_Y:=\|C_x\|_2M_Z$、$M_{\mathrm{ref}}:=\max_{1\le i\le N}\|x_i^{\mathrm{ref}}\|_2$ 和 $K_i^x:=\|C_x\|_2K_i$；本模型 $\|C_x\|_2=1$。

记 $y_i^{\mathrm{full}}=C_xz_i^{\mathrm{full}}$、$y_i^{\mathrm{fr}}=C_xz_i^{\mathrm{fr}}$，则输出差 $d_i=C_xe_i$ 满足 $\|d_i\|_2\le K_i^x$。状态项差为：

$$
\big|\|y_i^{\mathrm{full}}-x_i^{\mathrm{ref}}\|_{Q_x}^2-\|y_i^{\mathrm{fr}}-x_i^{\mathrm{ref}}\|_{Q_x}^2\big|
=\big|d_i^\top Q_x(y_i^{\mathrm{full}}+y_i^{\mathrm{fr}}-2x_i^{\mathrm{ref}})\big|
\le\|Q_x\|_2\|d_i\|_2\big(\|y_i^{\mathrm{full}}\|_2+\|y_i^{\mathrm{fr}}\|_2+2M_{\mathrm{ref}}\big).
$$

由统一full状态界，$\|y_i^{\mathrm{full}}\|_2\le M_Y$；又 $y_i^{\mathrm{fr}}=y_i^{\mathrm{full}}-d_i$，故 $\|y_i^{\mathrm{fr}}\|_2\le M_Y+K_i^x$。因此

$$
\big|\Delta J_i\big|\le\|Q_x\|_2 K_i^x\big(2M_Y+K_i^x+2M_{\mathrm{ref}}\big).
$$

于是可取

$$
\boxed{\;
\varepsilon_J:=2(M_Y+M_{\mathrm{ref}})\Big[\|Q_x\|_2\sum_{i=1}^{N-1}K_i^x+\|P_x\|_2 K_N^x\Big]
+\|Q_x\|_2\sum_{i=1}^{N-1}(K_i^x)^2+\|P_x\|_2(K_N^x)^2
\;}
$$

第一部分来自线性因子 $2(M_Y+M_{\mathrm{ref}})$，第二部分来自 $(K_i^x)^2$；终端项用 $P_x$。$N=1$时求和为空；名义输入恰等于候选输入时`07`给出零冻结误差。全可行集的上界仍取统一supremum，不能只在名义输入处验证(CA)。

**意义**：在统一适用条件下，$\varepsilon_J$由输出权重、参考/状态界及`07`的常数构造。经验估计可以显示量级，但有限采样不替代全可行集的常数认证。

## 3. 定理 3（条件次优性）

设

- $U^{\mathrm{fr}} \in \arg\min_{U \in \mathcal{U}_{\mathrm{feas}}} J_{\mathrm{fr}}(U; \bar U)$（冻结问题的**全局**最优点；`06`在输入盒约束下给凸QP）；
- $U^{\star} \in \arg\min_{U \in \mathcal{U}_{\mathrm{feas}}} J_{\mathrm{full}}(U)$（完整问题的**全局**极小点）；
- 二者**可行集相同、非空，且以上两个argmin存在**，记为 $\mathcal{U}_{\mathrm{feas}}$。

则在 (CA) 下，

$$
\boxed{\;
0 \;\le\; J_{\mathrm{full}}(U^{\mathrm{fr}}) - J_{\mathrm{full}}(U^{\star}) \;\le\; 2\,\varepsilon_J
\;}
$$

### 证明（三步不等式）

$$
\begin{aligned}
J_{\mathrm{full}}(U^{\mathrm{fr}})
&\;\le\; J_{\mathrm{fr}}(U^{\mathrm{fr}}; \bar U) + \varepsilon_J
&& \text{（(CA) 的上界一侧）} \\[2pt]
&\;\le\; J_{\mathrm{fr}}(U^{\star}; \bar U) + \varepsilon_J
&& \text{（} U^{\mathrm{fr}} \text{ 是 } J_{\mathrm{fr}} \text{ 的极小点，且 } U^\star \in \mathcal{U}_{\mathrm{feas}} \text{）} \\[2pt]
&\;\le\; J_{\mathrm{full}}(U^{\star}) + 2\varepsilon_J
&& \text{（(CA) 的下界一侧）}
\end{aligned}
$$

左边的不等式 $J_{\mathrm{full}}(U^{\mathrm{fr}}) \ge J_{\mathrm{full}}(U^{\star})$ 由 $U^\star$ 的最优性直接给出。 $\blacksquare$

**注意证明中每一处的可行性依赖**：第二步用到 $U^\star \in \mathcal{U}_{\mathrm{feas}}$（即完整问题的最优点对冻结问题是**可行**的）；第三步用到 (CA) 对 $U^\star$ 成立。这正是「二者可行集相同」这一条件的作用。

## 4. 与计划书 Q3 的关系

| 计划书要求 | 本文件的处理 |
|---|---|
| 用 $0 \le J_{\mathrm{full}}(u^{\mathrm{fr}}) - J_{\mathrm{full}}(u^\star) \le 2\varepsilon_J$ 的**条件形式** | ✅ 定理 3 逐字对应 |
| **不假设** $CN(\delta_A + \delta_B)$ | 不把该指定形式作为假设；仅在本节对比计划书要求 |
| 推导 $CN(\delta_A+\delta_B)$ 是「阶段六可争取项」 | 未采用该特定形式；本文件构造输入偏差到冻结误差再到输出成本的显式界，不声称所有矩阵偏差形式都不可能 |

**所选形式**：采用 $\delta_u,\Delta_u\to\delta_{\mathrm{frz}}\to\varepsilon_J$，使名义输入偏差与历史调度差之间的依赖可追溯。若另有对整个可行集一致的矩阵调度偏差界，也可以从误差递推推导成本界；本文件不增加这条支线，也不将未采用解释为无法证明。

## 5. 诚实边界（必须与结论一起阅读）

1. **结论是条件性的。** 需要(CA)；显式上界要求统一工作域/正则性、状态/参考与权重等常数，不将经验估计等同于认证。本文件不提供真实设备上的统一常数。
2. **全局参考与数值解分开。** $U^\star$为完整问题全局最优。若冻结解仍精确最优，对任何可行full局部参考 $U^{\mathrm{loc}}$，有 $J_{\mathrm{full}}(U^{\mathrm{fr}})-J_{\mathrm{full}}(U^{\mathrm{loc}})\le J_{\mathrm{full}}(U^{\mathrm{fr}})-J_{\mathrm{full}}(U^\star)\le2\varepsilon_J$；前一个差可为负，不能当作全局次优差。局部full求解影响能否测到全局差距，不会仅因此使上界失效。若冻结求解本身近似，需另有目标误差证书；`solved inaccurate`不是精确argmin证明。本阶段不增加求解器误差定理。
3. **可行集必须一致。** 若完整问题含**状态约束** $z_i \in \mathcal{Z}$，则冻结问题的可行集（仿射原像）与完整问题的可行集**不同**，证明第二步失效，需要额外假设（例如「$U^\star$ 恰好对冻结问题可行」，或对两个可行集分别给出包含关系并修正常数）。本阶段只考虑**输入约束**（$u_i \in \mathcal{U}$），二者可行集相同。
4. **不声称闭环稳定、不声称递归可行性、不声称实时性。** 定理 3 是单次求解的次优性，与闭环性质无关。
5. **$\varepsilon_J$ 的表达式是保守上界。** 其中每个因子均取上界，$\|Q_x\|_2,\|P_x\|_2$为谱范数；不由此断言真实设备上成本差的具体量级。
6. **$\Delta_u$ 依赖名义输入 $\bar U$ 的取法**，而 $\bar U$ 是设计选择（warm start）。本文件不规定取法，也不声称任何取法的最优性。
