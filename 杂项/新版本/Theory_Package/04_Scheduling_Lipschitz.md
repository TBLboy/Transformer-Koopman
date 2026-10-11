# 04 调度 Lipschitz 连续性（Proposition 2）

> **状态**：前期材料，**不是论文正文**；不含实验数值。
> **对应计划书**：第三阶段第五章理论包（Prop 2：调度 Lipschitz 连续性）。
> **依赖**：`01` §4（参数化）、`02` 的 S3（softmax + tanh + 列归一化）与 A4（权重矩阵有界）。

---

## 引理 1（softmax 的 Lipschitz 界）

设 $\pi = \operatorname{softmax}(z)$、$\pi' = \operatorname{softmax}(z') \in \mathbb{R}^{r}$。则

$$
\big\| \pi - \pi' \big\|_2 \;\le\; \tfrac{1}{2}\, \big\| z - z' \big\|_2 .
$$

### 证明

**(i) Jacobian。** softmax 的 Jacobian 为

$$
J(\pi) = \operatorname{diag}(\pi) - \pi \pi^{\top} \in \mathbb{R}^{r \times r},
$$

它**对称且半正定**（$\operatorname{diag}(\pi)$ 与 $\pi\pi^{\top}$ 都对称，故 $J$ 对称；半正定性见下）：对任意 $v$，

$$
v^{\top} J(\pi) v = \sum_{j} \pi_j v_j^2 - \Big(\sum_j \pi_j v_j\Big)^2 = \operatorname{Var}_\pi(v) \;\ge\; 0 .
$$

**(ii) Popoviciu 不等式。** 记 $M = \max_j v_j$、$m = \min_j v_j$、$\mu = \sum_j \pi_j v_j$。因为对每个 $j$ 有 $(v_j - m)(M - v_j) \ge 0$，即

$$
v_j^2 \;\le\; v_j (M + m) - m M ,
$$

两边取 $\pi$-加权平均（$\sum_j \pi_j = 1$）得 $\mathbb{E}[v^2] \le \mu (M+m) - mM$，于是

$$
\operatorname{Var}_\pi(v) = \mathbb{E}[v^2] - \mu^2 \;\le\; (M - \mu)(\mu - m) \;\le\; \frac{(M-m)^2}{4} .
$$

**(iii) 极差与范数。** 取 $j$ 达到 $M$、$k$ 达到 $m$，则

$$
(M - m)^2 = (v_j - v_k)^2 \;\le\; 2\,(v_j^2 + v_k^2) \;\le\; 2\,\|v\|_2^2 .
$$

**(iv) 合并。** 由 (i)–(iii)，对一切 $v$ 有 $v^{\top} J(\pi) v \le \tfrac{1}{2}\|v\|_2^2$。因 $J$ 对称半正定，其谱范数等于最大特征值，故

$$
\big\| J(\pi) \big\|_2 \;\le\; \tfrac{1}{2} .
$$

**(v) 沿路径积分。** 令 $z(t) = z + t(z' - z)$，$\pi(t) = \operatorname{softmax}(z(t))$。由 $\frac{d}{dt}\pi(t) = J(\pi(t))\,\dot z(t)$ 得

$$
\big\| \pi - \pi' \big\|_2
= \Big\| \int_0^1 J(\pi(t))\,(z' - z)\, dt \Big\|_2
\;\le\; \int_0^1 \big\| J(\pi(t)) \big\|_2 \, dt \; \big\| z - z' \big\|_2
\;\le\; \tfrac{1}{2} \big\| z - z' \big\|_2 . \qquad \blacksquare
$$

**备注（不紧）**：常数 $1/2$ 不是最优。取 $r = 2$、$z = (a,b)$、$z' = (b,a)$、$d = a - b$，两侧分别为 $\sqrt{2}\,|\tanh(d/2)|$ 与 $\tfrac{1}{2}\sqrt{2}\,|d|$，而 $\tanh(d/2) < |d|/2$ 对 $d \ne 0$ 严格成立。

---

## 命题 2（调度 Lipschitz 连续性）

沿用 `01` §4 的参数化。则对任意 $c, c' \in \mathbb{R}^{d_c}$ 与任意 $\chi, \chi' \in \mathbb{R}^{n}$：

$$
\big\| A(c) - A(c') \big\|_2 \;\le\; L_A \, \big\| c - c' \big\|_2 ,
\qquad
L_A = g_A\Big( \|W_A\|_2 + \tfrac{\sqrt{r_A}}{2}\,\|W_A^{\pi}\|_2 \Big),
$$

$$
\big\| B(\chi) - B(\chi') \big\|_2 \;\le\; L_B \, \big\| \chi - \chi' \big\|_2 ,
\qquad
L_B = g_B\Big( \|W_B\|_2 + \tfrac{\sqrt{r_B}}{2}\,\|W_B^{\pi}\|_2 \Big).
$$

两个常数都**只依赖参数化本身**（S3）与 A4，**不依赖** $c$ 的取值，也**不需要** A1 的有界性。

### 证明（以 $A$ 为例；$B$ 把 $c \to \chi$、$g_A \to g_B$、$r_A \to r_B$ 即可，逐字相同）

记 $\gamma_j := \gamma_{A,j}$、$\pi_j := \pi_{A,j}$、$\tau_j(c) := \tanh([W_A c + b_A]_j)$。

**第 1 步：秩一和。** 由 `01` §4.1，

$$
A(c) - A(c') = \sum_{j=1}^{r_A} \big( \gamma_j(c) - \gamma_j(c') \big) \, u_{A,j} v_{A,j}^{\top}
\;\Longrightarrow\;
\big\| A(c) - A(c') \big\|_2 \le \sum_{j=1}^{r_A} \big| \gamma_j(c) - \gamma_j(c') \big| ,
$$

最后一步用 $\|u_{A,j} v_{A,j}^{\top}\|_2 = \|u_{A,j}\|_2 \|v_{A,j}\|_2 \le 1$（`03` 第 3 步）。

**第 2 步：乘积的差。** $\gamma_j = g_A \pi_j \tau_j$，故

$$
\big| \gamma_j(c) - \gamma_j(c') \big|
\;\le\; g_A \Big( \big| \pi_j(c) - \pi_j(c') \big| \, \underbrace{|\tau_j(c)|}_{\le 1}
\;+\; \pi_j(c') \, \big| \tau_j(c) - \tau_j(c') \big| \Big).
$$

**第 3 步：$\tanh$ 的 Lipschitz 性。** $\tanh$ 的导数 $\operatorname{sech}^2 \le 1$，故

$$
\big| \tau_j(c) - \tau_j(c') \big| \;\le\; \big| [W_A (c - c')]_j \big| .
$$

**第 4 步：求和。**

$$
\sum_{j=1}^{r_A} \big| \gamma_j(c) - \gamma_j(c') \big|
\;\le\; g_A \Big( \underbrace{\big\| \pi_A(c) - \pi_A(c') \big\|_1}_{T_1}
\;+\; \underbrace{\sum_{j} \pi_j(c') \, \big| [W_A(c-c')]_j \big|}_{T_2} \Big).
$$

**第 5 步：$T_1$。** 由 $\|\cdot\|_1 \le \sqrt{r}\,\|\cdot\|_2$ 与引理 1（注意 softmax 的自变量是 $z(c) = W_A^{\pi} c + b_A^{\pi}$）：

$$
T_1 \;\le\; \sqrt{r_A} \cdot \tfrac{1}{2} \big\| W_A^{\pi} (c - c') \big\|_2
\;\le\; \tfrac{\sqrt{r_A}}{2} \big\| W_A^{\pi} \big\|_2 \big\| c - c' \big\|_2 .
$$

**第 6 步：$T_2$。** 因为 $\sum_j \pi_j(c') = 1$，$T_2$ 是 $\big|[W_A(c-c')]_j\big|$ 的加权平均，故不超过其最大值，也不超过该向量的 2 范数：

$$
T_2 \;\le\; \max_j \big| [W_A(c-c')]_j \big| \;\le\; \big\| W_A (c - c') \big\|_2 \;\le\; \|W_A\|_2 \big\| c - c' \big\|_2 .
$$

**第 7 步：合并。** 把第 5、6 步代回第 4 步，再代回第 1 步，得

$$
\big\| A(c) - A(c') \big\|_2 \;\le\; g_A\Big( \tfrac{\sqrt{r_A}}{2}\|W_A^{\pi}\|_2 + \|W_A\|_2 \Big) \big\| c - c' \big\|_2 = L_A \big\| c - c' \big\|_2 . \qquad \blacksquare
$$

---

## 备注（诚实边界）

1. **常数是全局的。** 命题 2 对**一切** $c, c'$ 成立，不需要局部线性化、不需要 A1 的工作域有界性。
2. **常数不紧。** $\sqrt{r_A}/2$ 来自 $\|\cdot\|_1 \le \sqrt{r}\|\cdot\|_2$ 与引理 1 的 $1/2$，两者都是保守因子；实际敏感度通常远小于 $L_A$。这不影响结论的正确性，但在用 $L_A$ 估计数值大小时应记住它是上界。
3. **与 `01` §7 第 1 项的耦合。** 若 $\tanh$ 的输入含归一化层（该项标注为**待核实**），则 $[W_A c + b_A]_j$ 需替换为含 Norm 的形式，第 3 步改为「$\tanh \circ \mathrm{Norm}$ 的 Lipschitz 常数」，$L_A$ 的表达式随之改变；**引理 1 与其余步骤不变**。
4. **与命题 1 的分工。** `03` 给的是「偏离名义矩阵的**幅度**」（$g_A$），本文件给的是「对调度变量的**敏感度**」（$L_A$）。二者不可互相推出：$g_A$ 小不代表 $L_A$ 小（$W$ 可以很大而 $\gamma$ 仍被 $\tanh$ 压住），反之亦然。
5. **不含 $L_\phi$。** 命题 2 是关于 $c$ 的 Lipschitz。当需要把 $\|c_k - \bar c_k\|$ 界成「历史窗口之差」时，要再乘 A3 的 $L_\phi$ —— 那一步在 `05`、`07` 里使用，不在此处。
6. **交叉文件注记。** `03` 的接口表在写时就 $L_A$ 给的是一个**形状性**描述（"$L_A = g_A\|W_A\|_2 L_{\gamma_A'} L_\phi$ 形式的常数"），那是前向计划而非精确表达式；精确形式以本文件为准。`03` 已被 `TASK-034` 的证据与复核绑定，故**不回改**（改字节会使已复核的证据失效），此处显式记录该漂移。
