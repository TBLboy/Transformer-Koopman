# 06 冻结 LTV-MPC 与凸性（Proposition 4）

> **状态**：前期材料，**不是论文正文**；不含实验数值。
> **对应计划书**：第四阶段「第六章控制理论包」（完整 scheduled MPC 模型、名义 rollout、冻结 LTV 模型、凸性命题）。
> **依赖**：`01`的模型/共同历史；固定名义调度、半正定权重与凸输入集。仿射堆叠/凸性不需要A2–A5或调度Lipschitz常数。
>
> **修订说明（第二版）**：第一版的 $D$ 首行与图注在 $i=0$ 处自相矛盾，且 $J_{\mathrm{fr}}$ 的 $S$ 项含参考速率而 $J_{\mathrm{full}}$ 的不含，使「输入项作差抵消」不成立（并破坏 `08` 定理 3 的前提）。本版统一两侧的 $S$ 项并改记号为 $\hat D$；另补 $X_i, U^{\mathrm{in}}_i$ 的构造、显式 $f$、以及若干措辞。
>
> **本次对齐（DEC-093）**：控制跟踪测量输出 $C_xz$，不定义latent参考。full/frozen统一预测状态索引与终端项，和临时实现`cost_value`一致；训练联合$x+z$误差为DEC-091的另一个对象。

---

## 1. 完整 scheduled MPC 问题（**非线性**）

给定 $z_0:=z_k^{\mathrm{enc}}$、`01`的共同真实历史、测量参考 $\{x_i^{\mathrm{ref}}\}_{i=0}^{N}\subset\mathbb R^n$、输入参考 $\{u_i^{\mathrm{ref}}\}_{i=0}^{N-1}$、时域 $N\ge1$，以及上拍输入 $u_{-1}$。取对称权重 $Q_x,P_x\succeq0$（$n\times n$）、$R,S\succeq0$（$m\times m$）。$P_x$ 是终端权重，与历史长度 $P$ 区分。

$$
\begin{aligned}
\min_{U = (u_0,\dots,u_{N-1})} \quad
J_{\mathrm{full}}(U) \;=\;& \sum_{i=1}^{N-1}\|C_x z_i-x_i^{\mathrm{ref}}\|_{Q_x}^2
+\|C_xz_N-x_N^{\mathrm{ref}}\|_{P_x}^2
+\sum_{i=0}^{N-1}\|u_i-u_i^{\mathrm{ref}}\|_R^2 \\
& + \sum_{i=0}^{N-1} \| u_i - u_{i-1} \|_S^2
\end{aligned}
$$

$$
\text{s.t.}\quad
z_0 = z_k,\qquad
z_{i+1} = A(c_i)\, z_i + B(\chi_i)\, u_i,\qquad
u_i \in \mathcal{U} .
$$

其中预测窗口与调度按 `01`/`02` 的约定构造：

$$
\chi_i = C_x z_i,\qquad
X_i = [\,C_x z_{i-P+1};\ \dots;\ C_x z_i\,] \in \mathbb{R}^{Pn},\qquad
U^{\mathrm{in}}_i = [\,u_{i-P+1};\ \dots;\ u_{i-1}\,] \in \mathbb{R}^{(P-1)m},
$$

$$
c_i = C_\phi(X_i, U^{\mathrm{in}}_i),
$$

槽位下标 $j<0$ 时直接取起点前的真实测量/输入历史，不定义 $z_j$；$j\ge0$ 时用当前轨迹的 $C_xz_j,u_j$。按`01`共同历史与移位契约更新；**当前输入 $u_i$ 不进入 $c_i$**（`02` S1）。

两种控制成本均计 $i=1,\ldots,N-1$ 的状态项与 $i=N$ 的终端项，$N=1$时前者为空。若希望加入 $i=0$ 的固定初始跟踪成本，可在full/frozen两侧同时加同一常数，不改变argmin、Hessian或两者成本差。

**关键观察（这决定了整章的走向）**：$c_i$ 与 $\chi_i$ 都**依赖状态**，于是 $B(\chi_i) u_i$ 是**状态与输入的乘积**。因此 $J_{\mathrm{full}}$ 关于决策变量 $U$ 是**非线性**的，且**一般非凸**（"一般"：当 $r_A = r_B = 0$ 时退化为 LTI，此时问题凸）。

> 这正是引入「冻结调度」近似的动机：把「调度依赖状态」这一非线性来源，换成「调度在名义 rollout 上算好、之后冻结」的时变线性模型。

## 2. 名义 rollout 与冻结调度

给定**名义输入序列** $\bar U = (\bar u_0,\dots,\bar u_{N-1})$（warm start，例如上一拍的解或参考前馈），用**完整模型**滚动一遍：

$$
\bar z_0 = z_k,\qquad
\bar\chi_i = C_x \bar z_i,\qquad
\bar c_i = C_\phi(\bar X_i, \bar U^{\mathrm{in}}_i),\qquad
\bar z_{i+1} = A(\bar c_i)\, \bar z_i + B(\bar\chi_i)\, \bar u_i ,
$$

并**冻结**调度：

$$
\boxed{\; \bar A_i := A(\bar c_i), \qquad \bar B_i := B(\bar\chi_i) \;}
$$

- $\bar X_i$ 由 $\bar z$ 的 $x$ 槽位（即 $\bar\chi$）构成，$\bar U^{\mathrm{in}}_i$ 由 $\bar U$ 构成——与 `01` §4.3 的约定一致；
- **冻结的含义**：$\bar A_i, \bar B_i$ 是**已知的数值矩阵**，不再依赖后续的 $z$ 与 $u$。

> **注意**：名义 rollout $\bar z$ 的驱动输入是 $\bar U$，而冻结模型（§3）与完整模型（§1）的驱动输入都是决策变量 $U$。三者是**不同**的对象——这一区分在 `07` 里是核心。

## 3. 冻结 LTV 模型

$$
\boxed{\; z_{i+1} = \bar A_i\, z_i + \bar B_i\, u_i \;}
$$

关于 $(z_i, u_i)$ 是**仿射**的（时变矩阵已知）。这是整个「凸 QP」路线的基础。

## 4. 命题 4（冻结问题的凸性）

把状态与输入堆叠为

$$
Z = \begin{bmatrix} z_1 \\ \vdots \\ z_N \end{bmatrix} \in \mathbb{R}^{Nd},
\qquad
U = \begin{bmatrix} u_0 \\ \vdots \\ u_{N-1} \end{bmatrix} \in \mathbb{R}^{Nm}.
$$

则冻结模型给出**仿射关系**

$$
Z = F + G\,U,
$$

其中

$$
F_i = \Big( \prod_{j=0}^{i-1} \bar A_j \Big) z_0
\quad (i = 1,\dots,N),
\qquad
G_{i,t} =
\begin{cases}
\Big( \prod_{j=t+1}^{i-1} \bar A_j \Big) \bar B_t, & t < i, \\[2pt]
0, & t \ge i .
\end{cases}
$$

> **符号约定（重要）**：空乘积取单位矩阵；乘积次序为**时间递降**，即
> $$\prod_{j=a}^{b} \bar A_j \;:=\; \bar A_b \bar A_{b-1} \cdots \bar A_a \qquad (a \le b),$$
> $a > b$ 时为空乘积。因此 $F_i = \bar A_{i-1}\cdots \bar A_0\, z_0$、$G_{i,t} = \bar A_{i-1}\cdots \bar A_{t+1} \bar B_t$（$G_{i,i-1} = \bar B_{i-1}$）。矩阵不可交换，**次序是定义的一部分**：按通常「下标递增、从左到右」的读法会得到相反次序，那是错的。

**（验证）** $i=2$：$z_2 = \bar A_1\bar A_0 z_0 + \bar A_1 \bar B_0 u_0 + \bar B_1 u_1$，与 $F_2 = \bar A_1\bar A_0 z_0$、$G_{2,0} = \bar A_1\bar B_0$、$G_{2,1} = \bar B_1$ 一致。

冻结代价记为

$$
J_{\mathrm{fr}}(U; \bar U) \;=\; \|\bar C_x Z-Y^{\mathrm{ref}}\|_{\bar Q_x}^2 + \| U - U^{\mathrm{ref}} \|_{\bar R}^2 + \| \hat D U + \hat c \|_{\bar S}^2 ,
$$

其中 $\bar C_x=I_N\otimes C_x\in\mathbb R^{Nn\times Nd}$，$Y^{\mathrm{ref}}=[x_1^{\mathrm{ref}};\ldots;x_N^{\mathrm{ref}}]\in\mathbb R^{Nn}$，$\bar Q_x=\operatorname{blkdiag}(Q_x,\ldots,Q_x,P_x)\in\mathbb R^{Nn\times Nn}$（$N-1$个$Q_x$块）。$\bar R,\bar S$分别为$N$个$R,S$的分块对角，$U^{\mathrm{ref}}=[u_0^{\mathrm{ref}};\ldots;u_{N-1}^{\mathrm{ref}}]$，**与full代价逐项相同**。若使用提升坐标有效权重，则为 $Q_z=C_x^\top Q_xC_x$ 和 $P_z=C_x^\top P_xC_x$；允许半正定，不对隐藏坐标指定目标。

$\hat D$ 是差分算子，$\hat c$ 是把上一拍输入折入的已知常数向量：

$$
\hat D = \begin{bmatrix}
I & 0 & \cdots & 0 \\
-I & I & \ddots & \vdots \\
0 & \ddots & \ddots & 0 \\
\vdots & & -I & I
\end{bmatrix} \in \mathbb{R}^{Nm \times Nm},
\qquad
(\hat D U)_0 = u_0,\quad (\hat D U)_i = u_i - u_{i-1}\ (i \ge 1),
$$

$$
\hat c = \begin{bmatrix} -u_{-1} \\ 0 \\ \vdots \\ 0 \end{bmatrix} \in \mathbb{R}^{Nm},
\qquad\text{于是}\qquad
(\hat D U + \hat c)_i = u_i - u_{i-1} \qquad (i = 0,\dots,N-1).
$$

> **两侧的 $S$ 项现在逐项相同**：$J_{\mathrm{full}}$ 的 $\sum_{i=0}^{N-1}\|u_i - u_{i-1}\|_S^2$ 与 $J_{\mathrm{fr}}$ 的 $\|\hat D U + \hat c\|_{\bar S}^2$ 是同一个函数（$u_{-1}$ 为已知常数）。这一点是 `08` 定理 3 的前提（输入项作差抵消），第一版曾经不成立。

### 结论

代入 $Z = F + GU$ 后，$J_{\mathrm{fr}}$ 是 $U$ 的**二次型**

$$
J_{\mathrm{fr}}(U) = \tfrac{1}{2} U^{\top} H\, U + 2 f^{\top} U + \text{const},
$$

$$
\boxed{\;
H = 2\big( G^{\top}\bar C_x^\top \bar Q_x\bar C_x G + \bar R + \hat D^{\top} \bar S\, \hat D \big),
\qquad
f = G^{\top}\bar C_x^\top \bar Q_x\big(\bar C_x F-Y^{\mathrm{ref}}\big) - \bar R\, U^{\mathrm{ref}} + \hat D^{\top} \bar S\, \hat c
\;}
$$

> **模板系数**：$H=\nabla^2J_{\mathrm{fr}}$ 是Hessian，二次项系数为 $M=H/2$，线性项为 $2f$。对应实现`cost_matrices`返回 $M,f,\mathrm{const}$，OSQP使用 $H=2M,q=2f$，不能混用两种模板。

且

$$
H \;\succeq\; 0 .
$$

若进一步 $G^{\top}\bar C_x^\top\bar Q_x\bar C_xG+\bar R+\hat D^\top\bar S\hat D\succ0$（例如 $\bar R\succ0$），则 $H\succ0$，目标严格凸；非空凸可行集上若最优解存在，则唯一。

### 证明

**第 1 步：三项各自的半正定性。**

- $G^{\top}\bar C_x^\top\bar Q_x\bar C_xG\succeq0$：任意 $v$ 的二次型等于 $(\bar C_xGv)^\top\bar Q_x(\bar C_xGv)\ge0$；
- $\bar R \succeq 0$（由 $R \succeq 0$ 的分块对角）；
- $\hat D^{\top} \bar S \hat D \succeq 0$：同理 $v^{\top} \hat D^{\top} \bar S \hat D v = (\hat D v)^{\top} \bar S (\hat D v) \ge 0$。

**第2步：相加。** 三个半正定矩阵之和为 $M\succeq0$，故 $H=2M\succeq0$，冻结目标为凸函数。

**第3步：严格凸。** 若 $M\succ0$，则目标严格凸；非空凸可行集上最优点至多一个。$\blacksquare$

**第4步（$f$的来源）**：令 $W:=\bar C_xF-Y^{\mathrm{ref}}$、$G_x:=\bar C_xG$，则

$$
(W + G_xU)^{\top}\bar Q_x(W+G_xU) = U^{\top} G_x^{\top}\bar Q_x G_x\, U + 2 (G_x^{\top}\bar Q_x W)^{\top} U + \text{const},
$$

$$
\|U - U^{\mathrm{ref}}\|_{\bar R}^2 = U^{\top}\bar R\, U - 2 (\bar R U^{\mathrm{ref}})^{\top} U + \text{const}
\quad(\bar R \text{ 对称}),
$$

$$
\|\hat D U + \hat c\|_{\bar S}^2 = U^{\top}\hat D^{\top}\bar S \hat D\, U + 2 (\hat D^{\top}\bar S \hat c)^{\top} U + \text{const} .
$$

三项相加得 $M=G_x^\top\bar Q_xG_x+\bar R+\hat D^\top\bar S\hat D$ 与上述 $f$，因此 $H=2M$。常数为 $W^\top\bar Q_xW+(U^{\mathrm{ref}})^\top\bar R U^{\mathrm{ref}}+\hat c^\top\bar S\hat c$。

### 约束集的凸性

- 输入约束 $u_i \in \mathcal{U}$（$\mathcal{U}$ 紧凸，`01` §1）→ $\{U : u_i \in \mathcal{U},\ \forall i\}$ 是凸集的笛卡尔积，**凸**；
- 若另有状态约束 $z_i \in \mathcal{Z}$，**需额外假设 $\mathcal{Z}$ 凸**（`02` A1 只保证紧），此时由 $Z = F + GU$ 它是 $U$ 的**仿射原像**（凸集在仿射映射下的原像凸），仍**凸**；
- 线性等式约束（若有）同样是仿射集。

因此可行集凸、目标为凸二次函数；任意凸约束下属于凸优化问题，**只有约束是线性/多面体形式时才是本文所指标准QP**。本阶段用输入盒约束，不加状态约束。非空紧输入集与连续目标保证最优解存在。

## 5. 与实现的对应（**不越级**）

- 命题4给出凸二次目标的 $H,f$；输入盒约束下为标准凸QP；
- 求解器属于实现选择；临时`controllers/ltv_mpc.py`使用OSQP，但数值状态不自动证明精确argmin。本文件不声称求解时间、迭代次数或实时性；
- $H$ 的块结构（由 $G$ 的三角块结构决定）提示可用结构化/稀疏求解，但这属于实现细节，不在此处声称。

## 6. 诚实边界（必须与结论一起阅读）

1. **凸性是「冻结问题」的性质，不是完整 scheduled MPC 的性质。** 完整问题是**非线性**的（§1），本文件**不**声称它凸、也不声称其全局最优可求。
2. **$H \succeq 0$ 只给凸性，不给唯一性。** 唯一性需要 $H \succ 0$（额外条件，如 $\bar R \succ 0$）。
3. **冻结解不是完整解。** 二者的状态差由 `07`（冻结误差）刻画，代价差由 `08`（条件次优性）刻画。
4. **不声称闭环稳定、不声称递归可行性、不声称实时性。** 命题 4 是单次求解问题的凸性，与闭环性质无关。
5. **名义 rollout 的取法影响 $\bar A_i, \bar B_i$，从而影响解的质量。** 本阶段不规定 warm-start 策略，也不声称任何取法的最优性。
6. **$\mathcal{U}$ 的凸性是假设**（`01` §1）；若实际输入约束非凸，本命题不适用。若含状态约束，还需 $\mathcal{Z}$ 凸（见 §4）。
7. **符号说明**：本文件的堆叠状态记为 $Z$，对应计划书第四阶段写的 $X = F + GU$；改名是为了避免与 `01` 的历史窗口 $X_k$ 冲突，二者是同一个对象。
8. **输出参考与成本索引**：$Y^{\mathrm{ref}}$ 从 $x_1^{\mathrm{ref}}$ 起，full/frozen都不计 $i=0$ 固定状态成本，没有旧版单侧常数差 $c_0$。若两侧同时加入该初始常数，它在成本差中抵消；$\hat c$始终是输入增量的向量偏移。
