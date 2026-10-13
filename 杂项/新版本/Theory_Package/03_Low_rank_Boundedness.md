# 03 低秩有界性（Proposition 1）

> **状态**：前期材料，**不是论文正文**；不含实验数值。
> **对应计划书**：第一阶段「需要证明 $\|A(c)-A_0\| \le g_A$」；也是阶段三第五章理论包的第一个结果。
> **依赖**：`01_Model_Definition.md` §4 的参数化。

---

## 命题 1（低秩修正的一致有界性）

沿用 `01_Model_Definition.md` §4 的参数化：

$$
A(c) = A_0 + U_A \operatorname{diag}(\gamma_A(c)) V_A^{\top},
\qquad
\gamma_{A,j}(c) = g_A\, \pi_{A,j}(c)\, \tanh\!\big([W_A c + b_A]_j\big),
\qquad
\pi_A(c) = \operatorname{softmax}(W_A^\pi c + b_A^\pi),
$$

且因子按列归一化 $\|u_{A,j}\|_2 \le 1$、$\|v_{A,j}\|_2 \le 1$。则

$$
\forall c \in \mathbb{R}^{d_c}:\qquad
\big\| A(c) - A_0 \big\|_2 \;\le\; g_A ,
$$

且完全对称地

$$
\forall \chi \in \mathbb{R}^{n}:\qquad
\big\| B(\chi) - B_0 \big\|_2 \;\le\; g_B .
$$

两个界都**不需要对 $c$（或 $\chi$）作任何假设**——包括不需要 $c$ 有界。

## 证明（以 $A$ 为例，$B$ 逐字相同）

**第一步：把修正写成秩一矩阵之和。**

$$
A(c) - A_0
= U_A \operatorname{diag}(\gamma_A(c)) V_A^{\top}
= \sum_{j=1}^{r_A} \gamma_{A,j}(c)\, u_{A,j} v_{A,j}^{\top}.
$$

**第二步：三角不等式。**

$$
\big\| A(c) - A_0 \big\|_2
\;\le\; \sum_{j=1}^{r_A} \big| \gamma_{A,j}(c) \big| \,
\big\| u_{A,j} v_{A,j}^{\top} \big\|_2 .
$$

**第三步：外积的谱范数。** 对任意非零 $y$，
$\|u v^{\top} y\|_2 = \|u\|_2\,|v^{\top} y| \le \|u\|_2 \|v\|_2 \|y\|_2$，且当 $v \ne 0$ 时取 $y = v$ 等号可达（$v = 0$ 时外积为零矩阵，结论平凡成立），故

$$
\big\| u v^{\top} \big\|_2 = \|u\|_2 \, \|v\|_2 \;\le\; 1 .
$$

**第四步：调制函数逐项有界。** 由 softmax 的性质，$\pi_{A,j}(c) \ge 0$ 且 $\sum_{j=1}^{r_A} \pi_{A,j}(c) = 1$；由 $\tanh$ 的饱和性，$|\tanh(\cdot)| < 1$。因此

$$
\big| \gamma_{A,j}(c) \big| = g_A\, \pi_{A,j}(c)\, \big|\tanh(\cdot)\big| \;\le\; g_A\, \pi_{A,j}(c).
$$

**第五步：合并。**

$$
\big\| A(c) - A_0 \big\|_2
\;\le\; \sum_{j=1}^{r_A} g_A\, \pi_{A,j}(c) \cdot 1
\;=\; g_A \underbrace{\sum_{j=1}^{r_A} \pi_{A,j}(c)}_{=\,1}
\;=\; g_A .
$$

$B$ 的证明把 $c$ 换成 $\chi$、$g_A$ 换成 $g_B$、$r_A$ 换成 $r_B$ 即可，逐字相同。$\blacksquare$

## 备注（诚实边界，务必与结论一起阅读）

1. **这是有界性，不是稳定性。** $\|A(c)-A_0\|_2 \le g_A$ 只说明 $A(c)$ 落在以 $A_0$ 为心、半径 $g_A$ 的谱范数球内。它与 $\rho(A(c)) < 1$ **没有**蕴含关系：
   - $A_0$ 本身可以有任意谱（本命题对 $A_0$ 不作假设）；
   - 即使 $A_0$ 稳定，$\|A(c)-A_0\| \le g_A$ 也不能推出 $\rho(A(c)) < 1$，除非另加条件（例如 $\|A_0\|_2 + g_A < 1$，这是一条**额外假设**，本阶段不采用、不声称）。
   - 项目规则「数学性质不越级」直接对应这一条：对 $A(c)-A_0$ 的范数约束不等于 $A(c)$ 稳定；逐步谱半径小于 1 也不保证时变矩阵乘积收缩。
2. **参数化族上的紧界，不是固定网络的精确上确界。** 在允许的参数族内，可选单位范数因子、让softmax权重趋于单个顶点且相应tanh趋于1，从而任意逼近 $g_A$。但固定训练后网络未必能实现这些极限；例如tanh的仿射输入恒为0时，修正恒为0。因此只能对任意固定网络给出上界，不能断言其 $\sup_c\|A(c)-A_0\|_2=g_A$，也不能将一般因子范数上界写成必然等式。
3. **若列未归一化**：结论变为 $\|A(c)-A_0\|_2 \le g_A \max_j \|u_{A,j}\|_2 \|v_{A,j}\|_2$。§4 取 $\le 1$ 正是为了消掉这一项。
4. **所需假设是「参数化自带」的**：非负且和为 1 的权重（softmax）、饱和的 $\tanh$、列归一化。这三条**不是额外假设**，而是 `01_Model_Definition.md` §4 定义的组成部分。因此命题 1 是**无条件**成立的（在参数化之内）。
5. **不涉及 $C_\phi$**：命题 1 对 $c$ 均匀成立。`04`给出关于 $c,\chi$ 的Lipschitz常数，context映射正则性在`05`/`07`比较历史窗口时才需要。

## 与后续结果的接口

> 下表区分本命题的结构界与后续另行证明的量；低秩修正幅度界不等于真实系统一步残差界。

| 下游结果 | 用到的量 |
|---|---|
| `04_Scheduling_Lipschitz.md` | 由S3推出 $L_A=g_A(\|W_A\|_2+\sqrt{r_A}\|W_A^\pi\|_2/2)$；不含 $L_\phi$ |
| `05_Prediction_Error_Bound.md` | $M_A=\|A_0\|_2+g_A$；真实一步残差另用A5的 $\delta$ |
| `06_Frozen_LTV_QP_Proof.md` | 固定调度的仿射堆叠与凸性不需要低秩修正幅度界 |
| `07_Freezing_Error_Bound.md` | 误差递推中的 $(A(c_i)-\bar{A}_i)$ 与 $(B(\chi_i)-\bar{B}_i)$ 两项的幅度（$\chi_i = C_x z_i$，$\bar{B}_i = B(\bar{\chi}_i)$，$\bar{\chi}_i = C_x \bar{z}_i$，与 `01` §4.3 的约定一致） |
