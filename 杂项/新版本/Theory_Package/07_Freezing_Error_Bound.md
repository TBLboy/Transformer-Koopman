# 07 冻结调度误差界（Theorem 2）

> **状态**：前期材料，**不是论文正文**；不含实验数值。
> **对应计划书**：第五阶段「冻结调度误差理论」（Thm 2 有限时域冻结误差界）。
> **依赖**：`01`共同历史、`02`的A1(full轨迹界)/A3、`03`/`04`固定模型常数、`06`；不需A2/A5，参数族统一常数才用A4。`05`仅提供归纳模板，不依赖其真实预测定理。
> **本文件是开环、有限时域的**：不涉及闭环稳定性、不涉及递归可行性。
>
> **修订说明（第二版）**：第一版把「名义 rollout $\bar z$」当成了「冻结模型轨迹 $z^{\mathrm{fr}}$」，漏掉了第三个对象，导致 $A$ 通道低估、$B$ 通道漏掉驱动项，**引理作为陈述为假**（复核者给出反例：真值 $0.76$，第一版界 $0.097$）。本版把三个对象显式区分，并重推常数。

---

## 1. 三个必须区分的轨迹

固定当前提升状态 $z_k := z^{\mathrm{enc}}_k$、一条**待评估的输入序列** $U = (u_0,\dots,u_{N-1})$，以及 `06` §2 的**名义输入** $\bar U = (\bar u_0,\dots,\bar u_{N-1})$（用来冻结调度）。

三条轨迹还共享`01`定义的起点前真实测量/过去输入缓冲区。负槽位直接读共享历史，不定义负时间传播latent。full/nominal起点后的测量和输入槽位分别按自身轨迹与自身输入移位；frozen使用名义矩阵而不重算调度。所有使用的窗口对属于A3的共同正则域。

**(a) 名义 rollout** $\bar z$（驱动输入为 $\bar U$，**调度由它自己生成**）

$$
\bar z_0 = z_k,\qquad
\bar\chi_i = C_x \bar z_i,\qquad
\bar c_i = C_\phi(\bar X_i, \bar U^{\mathrm{in}}_i),\qquad
\bar z_{i+1} = A(\bar c_i)\,\bar z_i + B(\bar\chi_i)\,\bar u_i .
$$

冻结的调度矩阵（`06` §2）：$\; \bar A_i := A(\bar c_i), \quad \bar B_i := B(\bar\chi_i)$。

**(b) 完整模型轨迹** $z^{\mathrm{full}}$（驱动输入为 $U$，**调度由它自己生成**）

$$
z^{\mathrm{full}}_0 = z_k,\qquad
z^{\mathrm{full}}_{i+1} = A(c^{\mathrm{full}}_i)\, z^{\mathrm{full}}_i + B(\chi^{\mathrm{full}}_i)\, u_i,
$$

$$
\chi^{\mathrm{full}}_i = C_x z^{\mathrm{full}}_i, \qquad
c^{\mathrm{full}}_i = C_\phi(X^{\mathrm{full}}_i, U^{\mathrm{in}}_i).
$$

**(c) 冻结模型轨迹** $z^{\mathrm{fr}}$（驱动输入为 $U$，**调度矩阵固定为** $\bar A_i, \bar B_i$）

$$
z^{\mathrm{fr}}_0 = z_k,\qquad
z^{\mathrm{fr}}_{i+1} = \bar A_i\, z^{\mathrm{fr}}_i + \bar B_i\, u_i .
$$

**(a) 与 (c) 的区别**：$\bar z$ 用 $\bar u_i$、$z^{\mathrm{fr}}$ 用 $u_i$；**(b) 与 (c) 的区别**：调度分别是「自己生成的」与「冻结的」。本文件的目标量是

$$
\boxed{\; e_i \;:=\; z^{\mathrm{full}}_i - z^{\mathrm{fr}}_i \;}
$$

即**冻结模型的预测误差**——这正是「同一输入序列下，完整模型 vs 冻结模型」（计划书 Q2）的对象，**不是**两个优化器的比较。

**同时定义名义漂移**

$$
\boxed{\; g_i \;:=\; z^{\mathrm{fr}}_i - \bar z_i \;}
$$

它衡量「冻结轨迹」与「算调度用的名义 rollout」之间的偏离。

## 2. 两个驱动量（都是**已知量**，不是假设）

$$
\boxed{\;
\delta_u \;:=\; \max_{0 \le i \le N-1} \| u_i - \bar u_i \|_2 \;\ge\; 0,
\qquad
\Delta_u \;:=\; \max_{0 \le i \le N-1} \big\| U^{\mathrm{in}}_i - \bar U^{\mathrm{in}}_i \big\|_2 \;\ge\; 0
\;}
$$

两者都可从「待评估输入」与「名义输入」直接算出。起点前的过去输入完全共享，未来每个槽位之差不超过 $\delta_u$，由窗口构成（$P-1$ 个过去输入）得：

$$
\Delta_u \;\le\; \sqrt{P-1}\;\delta_u .
$$

> 在 `08`（次优性）中需要 (CA) 对**整个可行集**一致成立，那里的 $\delta_u, \Delta_u$ 取成 $\mathcal{U}_{\mathrm{feas}}$ 上的上确界（由 $\mathcal{U}$ 紧得有限）。

## 3. 名义漂移的先验界（**不需要**误差递推）

由 (c) 与 (a)：$g_0 = 0$，且

$$
g_{i+1} = \bar A_i\, g_i + \bar B_i\, (u_i - \bar u_i).
$$

记 $M_A := \|A_0\|_2 + g_A$（命题 1）、$M_B := \|B_0\|_2 + g_B$（命题 1），则

$$
\| g_{i+1} \|_2 \;\le\; M_A\, \|g_i\|_2 + M_B\, \delta_u
\;\Longrightarrow\;
\boxed{\; \| g_i \|_2 \;\le\; G_i \;:=\; M_B\, \delta_u \sum_{t=0}^{i-1} M_A^{\,i-1-t} \;}
$$

**注意 $G_i$ 不含 $e$**：它完全由输入不匹配与参数化的范数决定，故可以**先算出来**，再进入下一步。

## 4. 误差递推

**引理 1（误差递推）**

$$
\boxed{\;
e_{i+1} \;=\; \bar A_i\, e_i \;+\; \big( A(c^{\mathrm{full}}_i) - \bar A_i \big) z^{\mathrm{full}}_i \;+\; \big( B(\chi^{\mathrm{full}}_i) - \bar B_i \big) u_i
\;}
$$

**证明**：在 $z^{\mathrm{fr}}_{i+1} = \bar A_i z^{\mathrm{fr}}_i + \bar B_i u_i$ 中加减 $\bar A_i z^{\mathrm{full}}_i + \bar B_i u_i$ 即得。 $\blacksquare$

（与计划书给的递推形式逐字一致。）

## 5. 定理 2（有限时域冻结误差界）

沿用 `05` 的记号

对固定 $U,\bar U$ 要求full轨迹的统一状态界与full/nominal窗口的A3条件。在`08`对全可行集使用此界时，按`02`A1的统一量词对每个可行 $U$ 使用同一 $M_Z,M_U,L_\phi$。

$$
L \;:=\; M_A + L_B M_U + L_A L_\phi \sqrt{P}\, M_Z ,
$$

并定义**冻结驱动量**

$$
\boxed{\;
\delta_{\mathrm{frz}} \;:=\; L_A L_\phi M_Z\, \Delta_u
\;+\; \big( L_A L_\phi \sqrt{P}\, M_Z + L_B M_U \big)\, G_N
\;}
$$

其中 $G_N = M_B \delta_u \sum_{t=0}^{N-1} M_A^{\,t}$ 是 §3 的**名义漂移上界**在时域末端处的值。记 $W_i := \max_{0 \le j \le i}\|e_j\|_2$。则对每个 $0 \le i \le N$：

$$
\boxed{\;
\| e_i \|_2 \;\le\; W_i \;\le\; \delta_{\mathrm{frz}} \sum_{t=0}^{i-1} L^{\,i-1-t}
\;}
$$

特别地 $L \ne 1$ 时 $\|e_N\|_2 \le \delta_{\mathrm{frz}}\dfrac{L^{N}-1}{L-1}$；$L=1$ 时 $\|e_N\|_2 \le N\,\delta_{\mathrm{frz}}$。

### 证明

**第 1 步：$A$ 通道。** 由命题 2 与 A3，

$$
\big\| A(c^{\mathrm{full}}_i) - \bar A_i \big\|_2 \le L_A \big\| c^{\mathrm{full}}_i - \bar c_i \big\|_2
\le L_A L_\phi \big\| (X^{\mathrm{full}}_i, U^{\mathrm{in}}_i) - (\bar X_i, \bar U^{\mathrm{in}}_i) \big\|_2 .
$$

窗口的**输入部分**相差 $\le \Delta_u$；**$x$ 槽位**相差

$$
\| X^{\mathrm{full}}_i - \bar X_i \|_2 \;\le\; \sqrt{P}\; \max_{i-P+1 \le j \le i} \big\| z^{\mathrm{full}}_j - \bar z_j \big\|_2
\;\le\; \sqrt{P}\; H_i,
$$

其中 $H_i$ 表示该窗口内差的最大值；$j<0$部分是共享测量缓冲区之差，取0，不定义该下标的latent。对 $j\ge0$ 用 $z^{\mathrm{full}}_j-\bar z_j=e_j+g_j$ 得

$$
H_i \;\le\; \max_{j \le i} \|e_j\|_2 + \max_{j \le i}\|g_j\|_2 \;\le\; W_i + G_i
\;\le\; W_i + G_N .
$$

（拼接向量的范数不超过两部分之和：$\sqrt{a^2+b^2} \le a+b$。）因此

$$
\big\| A(c^{\mathrm{full}}_i) - \bar A_i \big\|_2 \;\le\; L_A L_\phi \big( \sqrt{P}\,(W_i + G_N) + \Delta_u \big),
$$

贡献 $\le L_A L_\phi M_Z\big( \sqrt{P}(W_i+G_N) + \Delta_u \big)$（用 $\|z^{\mathrm{full}}_i\| \le M_Z$，A1）。

**第 2 步：$B$ 通道。** $B$ 的调度变量是**当前** $x$ 槽位（`01` §4.3、`02` S4），但注意它比的是**名义 rollout**：

$$
\big\| B(\chi^{\mathrm{full}}_i) - \bar B_i \big\|_2 \le L_B \big\| \chi^{\mathrm{full}}_i - \bar\chi_i \big\|_2
= L_B \big\| C_x (z^{\mathrm{full}}_i - \bar z_i) \big\|_2
\le L_B \big\| z^{\mathrm{full}}_i - \bar z_i \big\|_2
\le L_B \big( \|e_i\|_2 + G_i \big).
$$

贡献 $\le L_B M_U(\|e_i\|_2 + G_N)$。

> **这是第二版的核心更正**：$\bar B_i = B(C_x \bar z_i)$ 用的是**名义** rollout 的状态，所以 $\chi^{\mathrm{full}}_i - \bar\chi_i = C_x(e_i + g_i)$，**不是** $C_x e_i$。第一版漏掉 $g_i$，导致 $B$ 通道漏掉一个随 $\delta_u$ 增长的驱动项（复核者的反例正是攻击这一点）。

**第 3 步：合并。** 由引理 1 取范数，用 $\|\bar A_i\| \le M_A$（命题 1）与第 1、2 步：

$$
\| e_{i+1} \|_2 \;\le\; \big( M_A + L_B M_U \big)\|e_i\|_2 + L_A L_\phi \sqrt{P} M_Z\, W_i
\;+\; \underbrace{\Big[ L_A L_\phi \sqrt{P} M_Z + L_B M_U \Big] G_N + L_A L_\phi M_Z \Delta_u}_{\delta_{\mathrm{frz}}}
$$

即 $\|e_{i+1}\|_2 \le \delta_{\mathrm{frz}} + L\, W_i$（用 $\|e_i\| \le W_i$ 合并前两项）。

**第 4 步：归纳。** 与 `05` 定理 1 **逐字相同**：$W_0 = 0$（$e_0 = 0$）、$S_{i+1} = \delta_{\mathrm{frz}} + L S_i$、$S$ 的单调性引理（分 $L \ge 1$ 与 $0 \le L < 1$ 两情形，后者用 $S_i \le \delta_{\mathrm{frz}}/(1-L)$）、以及 $\max(S_i, S_{i+1}) = S_{i+1}$。 $\blacksquare$

## 6. 常数汇总（每个常数的来源）

| 常数 | 表达式 | 来源 | 类型 |
|---|---|---|---|
| $g_A, g_B$ | 参数化给定 | `03` 命题 1 | 由 S3 **推出** |
| $M_A$ | $\|A_0\|_2 + g_A$ | 命题 1 | 由 S3 **推出** |
| $M_B$ | $\|B_0\|_2 + g_B$ | 命题 1 | 由 S3 **推出** |
| $L_A, L_B$ | $g_A(\|W_A\|_2 + \tfrac{\sqrt{r_A}}{2}\|W_A^\pi\|_2)$，$B$ 对称 | `04` 命题 2 | 由 S3 + A4 **推出** |
| $M_Z, M_U$ | full轨迹与输入工作域界；用于08时对全部可行U统一 | `02` A1 | **假设** |
| $L_\phi$ | context 映射 Lipschitz 常数 | `02` A3 | **假设** |
| $P$ | 历史窗口长度（$P$ 个测量） | `01` §2 | 结构 |
| $\delta_u, \Delta_u$ | 输入不匹配（§2） | 由 $U, \bar U$ 直接算出 | **已知量，非假设** |
| $G_i$ | $M_B \delta_u \sum_{t=0}^{i-1} M_A^{i-1-t}$（§3） | 名义漂移引理 | 由上面**推出** |
| $\delta_{\mathrm{frz}}$ | $L_A L_\phi M_Z \Delta_u + (L_A L_\phi\sqrt P M_Z + L_B M_U) G_N$ | 定理 2 | 合成量 |
| $L$ | $M_A + L_B M_U + L_A L_\phi \sqrt{P} M_Z$ | 定理 2 | 合成量 |

## 7. 备注（诚实边界）

1. **与 `05` 的关系**：结构相同，但驱动量从「模型残差 $\delta$」换成「调度冻结的驱动量」$\delta_{\mathrm{frz}}$。因此两个定理共用同一套归纳论证——这是把「模型误差」与「冻结误差」分开处理的好处。
2. **两个驱动量，两个通道。** $\Delta_u$（窗口级输入不匹配）驱动**调度之差**（$A$ 通道）；$\delta_u$（逐步输入不匹配）驱动**名义漂移** $g$，而 $g$ 又同时进入 $A$ 通道（通过 $\bar c_i$）与 $B$ 通道（通过 $\bar\chi_i$）。**第一版错误地说「$B$ 通道不含 $\Delta_u$」，现已纠正。**
3. **自检（两条）**：
   - 若 $\bar U = U$：则 $\delta_u = \Delta_u = 0$，于是 $g \equiv 0$ 且 $\delta_{\mathrm{frz}} = 0$，定理给出 $\|e_i\| \equiv 0$。事实上此时 $\bar z$、$z^{\mathrm{fr}}$、$z^{\mathrm{full}}$ 三条轨迹**逐点重合**（$\bar z$ 的调度就是它自己生成的，冻结后仍复现它），故 $e \equiv 0$——**界与事实一致**。
   - 若 $B$ 通道不计（例如 $M_U = 0$），$\delta_{\mathrm{frz}}$ 退化为 $L_A L_\phi M_Z(\Delta_u + \sqrt{P}G_N)$，仍含漂移项——这与「$A$ 的调度窗口含历史状态」一致。
4. **界是保守的，但（第二版）是正确的。** 复核者第一版的反例（标量、$P=2$、$A(c)=\tanh(c)$、$B\equiv 100$、$\delta_u = \Delta_u = 0.01$、$N=2$）真值 $\|e_2\| = 0.7616$；第一版界 $0.0966$（**违反**），第二版界 $\approx 27.4$（**满足**，见 `validation/` 的复算）。保守性主要来自 $H_i \le W_i + G_N$ 这一步。
5. **$\Delta_u, \delta_u$ 是已知量，$\delta$ 是假设量**（`05` A5）。这是冻结误差与模型误差最重要的区别：前者可由输入序列直接算出，后者只能由数据或辨识实验界定。
6. **开环、有限时域。** 不含反馈，故**不**说明闭环稳定、**不**说明递归可行、**不**说明误差衰减；$L$ 不要求小于 1。
7. **不继承 `05` 的一般化陷阱。** 与 `05` 一样，只按 $e_0 = 0$ 与统一驱动量陈述；**不**声称含非零初值项或变驱动项的一般形式。
8. **不比较优化器。** 「冻结 QP 的解 vs 完整 MPC 的解」属于 `08`，不是本定理。
