# 05 有限时域预测误差界（Proposition 3 + Theorem 1）

> **状态**：前期材料，**不是论文正文**；不含实验数值。
> **对应计划书**：第三阶段第五章理论包（Prop 3「递归预测一致性，需要重新考虑 $B(x)$ 的影响」+ Thm 1「有限时域预测误差界」）。
> **依赖**：`01`（模型与共同历史）、`02`（S1–S5、A1、A3、A5）、`03`、`04`；固定网络无需额外A4，主界不使用A2。
> **本文件的两个结论都是开环、有限时域的**：不涉及闭环稳定性、不涉及递归可行性。

---

## 1. 设置

固定起始时刻 $k$，考察长度为 $H$ 的预测。两个序列：

**(a) 编码器序列**（用真实测量）：$z^{\mathrm{enc}}_{k+i} = g_\theta(X_{k+i})$，其中 $X_{k+i}$ 由**真实**测量构成。

**(b) 传播序列**（模型递推）：$\hat z_0 = z^{\mathrm{enc}}_k$，且

$$
\hat z_{i+1} = A(c^{\mathrm{prop}}_i)\, \hat z_i + B(\chi^{\mathrm{prop}}_i)\, u_{k+i},
\qquad
\chi^{\mathrm{prop}}_i = C_x \hat z_i,
$$

其中调度 $c^{\mathrm{prop}}_i = C_\phi(X^{\mathrm{prop}}_i, U^{\mathrm{in}}_{k+i})$ 由**传播窗口**生成。按`01`的共同历史契约，槽位下标 $j<0$ 取共享真实测量 $x_{k+j}$，$j\ge0$ 取 $C_x\hat z_j$，而非定义负时间的 $\hat z_j$。起点前的过去输入缓冲区也完全共享。注意：

- **输入序列相同**：两个序列使用同一组 $u_{k+i}$，故窗口的输入部分 $U^{\mathrm{in}}$ 一致，窗口之差**只来自 $x$ 槽位**；
- 这正对应计划书「同一输入序列下比较」的口径。

定义误差

$$
e_i \;:=\; z^{\mathrm{enc}}_{k+i} - \hat z_i \in \mathbb{R}^d, \qquad e_0 = 0 .
$$

## 2. 命题 3（一步误差递推）

在共同初始历史、A1、A3、A5及`03`/`04`给出的固定模型常数下，记

$$
M_A \;:=\; \|A_0\|_2 + g_A,
$$

则对每个 $i \ge 0$：

$$
\boxed{\;
\| e_{i+1} \|_2 \;\le\;
\delta \;+\; \big( M_A + L_B M_U \big)\, \| e_i \|_2
\;+\; L_A L_\phi \sqrt{P}\, M_Z \cdot \max_{i-P+1 \le j \le i} \| e_j \|_2
\;}
$$

（窗口中 $j<0$ 的测量误差为0，因此在最大值估计中用 $e_j=0$ 作记号约定；不定义负时间latent。$M_A$ 来自命题1，$\|\hat z_i\|_2\le M_Z$ 来自A1含传播序列的工作域条件。）

### 证明

**第 1 步：把误差拆成三项。** 由 $e_{i+1} = z^{\mathrm{enc}}_{k+i+1} - \hat z_{i+1}$，在中间加减 $A(c^{\mathrm{enc}}_{k+i}) z^{\mathrm{enc}}_{k+i} + B(\chi^{\mathrm{enc}}_{k+i}) u_{k+i}$（其中 $c^{\mathrm{enc}}_{k+i}$、$\chi^{\mathrm{enc}}_{k+i}$ 是**编码器序列**的调度）：

$$
e_{i+1} =
\underbrace{\big[ z^{\mathrm{enc}}_{k+i+1} - A(c^{\mathrm{enc}}_{k+i}) z^{\mathrm{enc}}_{k+i} - B(\chi^{\mathrm{enc}}_{k+i}) u_{k+i} \big]}_{(\mathrm{I}) \;=\; r_{k+i}}
+ \underbrace{\big[ A(c^{\mathrm{enc}}_{k+i}) z^{\mathrm{enc}}_{k+i} - A(c^{\mathrm{prop}}_i) \hat z_i \big]}_{(\mathrm{II})}
+ \underbrace{\big[ B(\chi^{\mathrm{enc}}_{k+i}) u_{k+i} - B(\chi^{\mathrm{prop}}_i) u_{k+i} \big]}_{(\mathrm{III})}.
$$

**(I)** 就是 A5 的一步潜在残差 $r_{k+i}$，故 $\|(\mathrm{I})\|_2 \le \delta$。

**第 2 步：项 (II)。** 加减 $A(c^{\mathrm{enc}}_{k+i}) \hat z_i$：

$$
(\mathrm{II}) = A(c^{\mathrm{enc}}_{k+i})\, \big( z^{\mathrm{enc}}_{k+i} - \hat z_i \big) + \big( A(c^{\mathrm{enc}}_{k+i}) - A(c^{\mathrm{prop}}_i) \big) \hat z_i ,
$$

于是

$$
\|(\mathrm{II})\|_2 \;\le\; M_A \| e_i \|_2 \;+\; L_A \, \big\| c^{\mathrm{enc}}_{k+i} - c^{\mathrm{prop}}_i \big\|_2 \cdot M_Z .
$$

**第 3 步：调度之差。** 两个窗口的输入部分相同，故由 A3 与 $\|C_x e\|_2 \le \|e\|_2$（$C_x$ 只取前 $n$ 个分量，见 S2）：

$$
\big\| c^{\mathrm{enc}}_{k+i} - c^{\mathrm{prop}}_i \big\|_2
\;\le\; L_\phi \, \big\| X^{\mathrm{enc}}_{k+i} - X^{\mathrm{prop}}_i \big\|_2
\;\le\; L_\phi \sqrt{\textstyle\sum_{j=0}^{P-1} \| C_x e_{i-P+1+j} \|_2^2}
\;\le\; L_\phi \sqrt{P} \max_{i-P+1 \le j \le i} \| e_j \|_2 .
$$

（**这是历史窗口带来的耦合**：一步误差不只依赖当前误差，还依赖最近 $P$ 步的误差。这正是计划书要求「重新考虑 $B(x)$ / 历史的影响」时要处理的地方。）

**第 4 步：项 (III)。** 两个 $B$ 的自变量之差就是 $\chi^{\mathrm{enc}}_{k+i} - \chi^{\mathrm{prop}}_i = C_x e_i$，故由命题 2 与 A1：

$$
\|(\mathrm{III})\|_2 = \big\| \big( B(\chi^{\mathrm{enc}}_{k+i}) - B(\chi^{\mathrm{prop}}_i) \big) u_{k+i} \big\|_2
\;\le\; L_B \| C_x e_i \|_2 \, M_U
\;\le\; L_B M_U \| e_i \|_2 .
$$

**第 5 步：合并。** 把 (I)、(II)、(III) 的界相加即得命题 3。 $\blacksquare$

## 3. 定理 1（有限时域预测误差界）

沿用命题 3 的记号，定义**单步传播因子**

$$
L \;:=\; M_A + L_B M_U + L_A L_\phi \sqrt{P} \, M_Z ,
$$

并记 $W_i := \max_{0 \le j \le i} \| e_j \|_2$。

**本定理的两个前提**（与 §1 与 A5 一致，缺一不可）：

- **(P1) 起始与历史对齐**：$e_0 = 0$，故 $W_0 = 0$；并且起点前完整测量/输入历史共享，负槽位误差为0；
- **(P2) 统一残差界**：A5 取 $\delta_t \equiv \delta$（不随时步变化）。

则对每个 $i \ge 0$：

$$
\boxed{\;
\| e_i \|_2 \;\le\; W_i \;\le\; \delta \sum_{t=0}^{i-1} L^{\,i-1-t}
\;}
$$

特别地，$L \ne 1$ 时 $\| e_H \|_2 \le \delta\,\dfrac{L^{H} - 1}{L - 1}$；$L = 1$ 时 $\| e_H \|_2 \le H \delta$。

**与计划书写法的差异（必须说明）**：计划书的 $L^H\|e_k\|+\sum_i L^{H-1-i}\delta_i$ 不能直接从本文件的延迟最大值递推推出。这里只保留零初值/统一残差版本；一般初值或变残差需要重新构造延迟比较界，不能直接套普通一步几何卷积：

- 命题 3 的第三项是窗口最大值 $\max_{i-P+1\le j\le i}\|e_j\|$，而窗口最大值**不随误差衰减**（它记住历史最大误差）。**下面的例子只用于说明「含初值项的一般形式为何不成立」；本设置本身有 $e_0 = 0$（见 §1）。** 手算例：$L = 1/2$、$\|e_0\| = 1$、$\delta = 0$ 时，$\|e_1\| \le 1/2$ 但 $W_1 = 1$，于是 $\|e_2\| \le L\,W_1 = 1/2$，而 $L^2\|e_0\| = 1/4$——含初值项的形式会给出**过小**的界。
- 变残差的一般式同样未被证明。反例：$L = 1/2$、$\delta_{k+0} = 100$、其后为 $0$、$P = 2$，则 $i = 3$ 时实际可达界为 $37.5$，而几何和 $\sum_t L^{i-1-t}\delta_{k+t}$ 只给 $25$。

本阶段不补一般化。额外假设（如窗口最大值等于当前误差）可能允许简化，但不是处理一般初值/变残差的唯一办法；不能由本例断言所有一般化都不可能。

### 证明（对 $W_i$ 归纳，用 (P1)(P2)）

由命题 3 与 $W_i$ 的定义，$\max_{i-P+1 \le j \le i}\|e_j\|_2 \le W_i$，故

$$
\| e_{i+1} \|_2 \;\le\; \delta + \big( M_A + L_B M_U \big) \|e_i\|_2 + L_A L_\phi \sqrt{P} M_Z \, W_i
\;\le\; \delta + L\, W_i .
$$

于是

$$
W_{i+1} = \max\big( W_i,\; \|e_{i+1}\|_2 \big) \;\le\; \max\big( W_i,\; \delta + L W_i \big). \tag{$\ast$}
$$

记 $S_i := \delta \sum_{t=0}^{i-1} L^{\,i-1-t}$（$S_0 = 0$），则 $S_{i+1} = \delta + L S_i$。

**归纳假设**：$W_i \le S_i$。**归纳基**：$W_0 = 0 = S_0$（用 (P1)）。

**关键引理（$S$ 的单调性）**：$S_{i+1} \ge S_i$。因为

- 若 $L \ge 1$：$S_{i+1} - S_i = \delta + (L-1) S_i \ge \delta \ge 0$；
- 若 $0 \le L < 1$：$S_i = \delta\,\frac{1 - L^{i}}{1-L} \le \frac{\delta}{1-L}$，故
  $$S_{i+1} - S_i = \delta - (1-L) S_i \;\ge\; \delta - (1-L)\frac{\delta}{1-L} = 0 .$$

> **注**：也可直接由 $S_i=\delta\sum_{q=0}^{i-1}L^q$ 得 $S_{i+1}-S_i=\delta L^i\ge0$（$L\ge0$），因此 $L<1$ 时单调性结论同样正确。这里给出的是比较序列的单调性，不是实际误差序列的单调性。

**归纳步**：由 $(\ast)$ 与 $W_i \le S_i$，

$$
W_{i+1} \;\le\; \max\big( S_i,\; \delta + L S_i \big) \;=\; \max\big( S_i,\; S_{i+1} \big) \;=\; S_{i+1},
$$

最后一步用单调性引理。故 $W_i \le S_i$ 对一切 $i$ 成立，即 $\| e_i \|_2 \le \delta \sum_{t=0}^{i-1} L^{\,i-1-t}$。 $\blacksquare$

## 4. 常数汇总（每个常数的来源）

| 常数 | 表达式 | 来源 | 类型 |
|---|---|---|---|
| $g_A, g_B$ | 参数化给定 | `03` 命题 1 | 由 S3 **推出** |
| $L_A, L_B$ | $g_A(\|W_A\|_2 + \tfrac{\sqrt{r_A}}{2}\|W_A^\pi\|_2)$，$B$ 对称 | `04` 命题 2 | 由 S3 + A4 **推出** |
| $M_A$ | $\|A_0\|_2 + g_A$ | 命题 1 | 由 S3 **推出** |
| $M_Z, M_U$ | 工作域界（**含传播序列**） | A1 | **假设** |
| $M_c$ | context 界 | A1 | **假设（目前未被任何结果使用，保留备用）** |
| $L_\phi$ | context 映射 Lipschitz 常数 | A3 | **假设** |
| $L_g$ | lifting Lipschitz 常数 | A2 | **假设（主界不使用；仅在显式拆分 lifting 残差时进入，见备注 4）** |
| $\delta$ | 一步潜在残差界 | A5 | **假设，需额外认证；不是S3自动给出的量** |
| $L$ | $M_A + L_B M_U + L_A L_\phi \sqrt{P} M_Z$ | 定理 1 | 合成量 |

## 5. 备注（诚实边界，必须与结论一起阅读）

1. **这是开环、有限时域的界。** 它不含任何反馈，因此**不**说明闭环稳定、**不**说明递归可行性、**不**说明误差会衰减。
2. **$L$ 不要求小于 1。** 定理 1 对任意 $L \ge 0$ 成立；$L < 1$ 时界有界并趋于 $\delta/(1-L)$ 量级（$L > 1$ 时随时域**指数**增长，$L = 1$ 时**线性**增长 $H\delta$）——这正是开环预测的固有性质，不是缺陷。**本文件不声称 $L < 1$**（那需要 $\|A_0\|$、$g_A$、$L_B M_U$ 等量的额外条件，属另一条命题）。
3. **历史窗口带来的 $P$ 因子与延迟耦合。** 命题3依赖最近 $P$ 步误差；保持其余常数不变时，显式窗口因子按 $\sqrt P$ 增长，而非按 $P$ 线性增长。若改变网络/工作域，其他常数也可能变化，不能据此作整体性能断言。
4. **三类残差的处理方式。** 计划书列 lifting / transition / input-modulation 三类。本文件的做法是：
   - **lifting 的一致性已被吸收进 $r_k$**：$r_k$ 衡量的是「编码器序列是否满足模型」，其中就包含「编码器每步重编码」与「递推传播」的差异；
   - 若用A2另行估计 $z^{\mathrm{enc}}_{k+i+1}-g_\theta(X^{\mathrm{prop}}_{i+1})$，有 $\le L_g\sqrt P W_{i+1}$。该项含未来比较量，不能仅以「改变 $L$」代入主递推；需要另行证明隐式递推闭合。本文件不采用、不证明这条支线，主界仍把编码一致性并入 $r_k$。
   - transition 与 input-modulation 两类残差**合并**为 $r_k$，理由见 `02` A5 的说明（无额外辨识假设时拆开是空记号）。
5. **常数不紧，且 $\delta$ 只能由数据界定。** $L$ 里每个因子都是上界；实际预测误差通常远小于该界。$\delta$ 是**模型误差**，本阶段没有任何数值（阶段七的临时验证才会给出量级）。
6. **不越级。** 本文件不声称：闭环稳定、递归可行、$L<1$、误差单调、或与实时性有关的任何结论。
