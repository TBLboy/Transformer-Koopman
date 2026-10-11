# 05 有限时域预测误差界（Proposition 3 + Theorem 1）

> **状态**：前期材料，**不是论文正文**；不含实验数值。
> **对应计划书**：第三阶段第五章理论包（Prop 3「递归预测一致性，需要重新考虑 $B(x)$ 的影响」+ Thm 1「有限时域预测误差界」）。
> **依赖**：`01`（模型）、`02`（S1–S5、A1–A5）、`03`（命题 1）、`04`（命题 2）。
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

其中调度 $c^{\mathrm{prop}}_i = C_\phi(X^{\mathrm{prop}}_i, U^{\mathrm{in}}_{k+i})$ 由**传播窗口** $X^{\mathrm{prop}}_i$ 生成（$X^{\mathrm{prop}}_i$ 的 $x$ 槽位来自 $C_x \hat z_{i-P+1},\dots,C_x \hat z_i$）。注意：

- **输入序列相同**：两个序列使用同一组 $u_{k+i}$，故窗口的输入部分 $U^{\mathrm{in}}$ 一致，窗口之差**只来自 $x$ 槽位**；
- 这正对应计划书「同一输入序列下比较」的口径。

定义误差

$$
e_i \;:=\; z^{\mathrm{enc}}_{k+i} - \hat z_i \in \mathbb{R}^d, \qquad e_0 = 0 .
$$

## 2. 命题 3（一步误差递推）

在 A1–A5 下，记

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

（$\max$ 的下标超出 $0$ 的部分按 $e_j = 0$ 处理；$M_A$ 来自命题 1：$\|A(c)\|_2 \le \|A_0\|_2 + \|A(c)-A_0\|_2 \le M_A$；$\|\hat z_i\|_2 \le M_Z$ 由 A1 给出——A1 已**显式包含**「传播序列留在工作域内」这一条。）

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

- **(P1) 起始对齐**：$e_0 = 0$，故 $W_0 = 0$；
- **(P2) 统一残差界**：A5 取 $\delta_t \equiv \delta$（不随时步变化）。

则对每个 $i \ge 0$：

$$
\boxed{\;
\| e_i \|_2 \;\le\; W_i \;\le\; \delta \sum_{t=0}^{i-1} L^{\,i-1-t}
\;}
$$

特别地，$L \ne 1$ 时 $\| e_H \|_2 \le \delta\,\dfrac{L^{H} - 1}{L - 1}$；$L = 1$ 时 $\| e_H \|_2 \le H \delta$。

**与计划书写法的差异（必须说明）**：计划书写的是 $\|e_{k+H}\| \le L^H\|e_k\| + \sum_i L^{H-1-i}\delta_i$，含一个**非零初值误差**项与**变残差**项。本文件**不声称**这两个更一般的形式，因为在本设置下它们**不成立**：

- 命题 3 的第三项是窗口最大值 $\max_{i-P+1\le j\le i}\|e_j\|$，而窗口最大值**不随误差衰减**（它记住历史最大误差）。**下面的例子只用于说明「含初值项的一般形式为何不成立」；本设置本身有 $e_0 = 0$（见 §1）。** 手算例：$L = 1/2$、$\|e_0\| = 1$、$\delta = 0$ 时，$\|e_1\| \le 1/2$ 但 $W_1 = 1$，于是 $\|e_2\| \le L\,W_1 = 1/2$，而 $L^2\|e_0\| = 1/4$——含初值项的形式会给出**过小**的界。
- 变残差的一般式同样未被证明。反例：$L = 1/2$、$\delta_{k+0} = 100$、其后为 $0$、$P = 2$，则 $i = 3$ 时实际可达界为 $37.5$，而几何和 $\sum_t L^{i-1-t}\delta_{k+t}$ 只给 $25$。

要把一般形式补回来需要**额外假设**（例如要求 $P = 1$，或要求误差序列单调，从而把窗口最大值替换为当前误差）。本阶段**不做**这个假设，也不声称该形式。

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

> **注**：这一步正是上一版论证的漏洞。上一版写「$S_{i+1} \ge S_i$（各项非负）」，这对 $L < 1$ 为**假**；而 $W_{i+1} = W_i$ 的分支恰恰只在 $L < 1$ 时可能出现。正确的依据是上面的界 $\delta/(1-L)$。

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
| $\delta$ | 一步潜在残差界 | A5 | **假设（唯一无法由参数化推出者）** |
| $L$ | $M_A + L_B M_U + L_A L_\phi \sqrt{P} M_Z$ | 定理 1 | 合成量 |

## 5. 备注（诚实边界，必须与结论一起阅读）

1. **这是开环、有限时域的界。** 它不含任何反馈，因此**不**说明闭环稳定、**不**说明递归可行性、**不**说明误差会衰减。
2. **$L$ 不要求小于 1。** 定理 1 对任意 $L \ge 0$ 成立；$L < 1$ 时界有界并趋于 $\delta/(1-L)$ 量级（$L > 1$ 时随时域**指数**增长，$L = 1$ 时**线性**增长 $H\delta$）——这正是开环预测的固有性质，不是缺陷。**本文件不声称 $L < 1$**（那需要 $\|A_0\|$、$g_A$、$L_B M_U$ 等量的额外条件，属另一条命题）。
3. **历史窗口带来的 $P$ 因子与延迟耦合。** 命题 3 的第三项依赖最近 $P$ 步误差的最大值，不是当前误差的纯函数。把它压成 $\sqrt{P}$ 是保守的；若窗口长度 $P$ 增大，$L$ 线性增长（$\sqrt{P}$ 在 $L$ 内）。
4. **三类残差的处理方式。** 计划书列 lifting / transition / input-modulation 三类。本文件的做法是：
   - **lifting 的一致性已被吸收进 $r_k$**：$r_k$ 衡量的是「编码器序列是否满足模型」，其中就包含「编码器每步重编码」与「递推传播」的差异；
   - 若要用 A2 单独显式地写出 lifting 残差（例如 $z^{\mathrm{enc}}_{k+i+1}$ 与 $g_\theta(X^{\mathrm{prop}}_{i+1})$ 之差），可把它写成 $\le L_g \|X^{\mathrm{enc}}_{k+i+1} - X^{\mathrm{prop}}_{i+1}\|_2 \le L_g \sqrt{P} W_{i+1}$，**这会改变 $L$**，需要在两种写法之间明确选一种（本文件选前者，理由：$r_k$ 是可从数据估计的量，而 $L_g$ 只是假设的常数）。
   - transition 与 input-modulation 两类残差**合并**为 $r_k$，理由见 `02` A5 的说明（无额外辨识假设时拆开是空记号）。
5. **常数不紧，且 $\delta$ 只能由数据界定。** $L$ 里每个因子都是上界；实际预测误差通常远小于该界。$\delta$ 是**模型误差**，本阶段没有任何数值（阶段七的临时验证才会给出量级）。
6. **不越级。** 本文件不声称：闭环稳定、递归可行、$L<1$、误差单调、或与实时性有关的任何结论。
