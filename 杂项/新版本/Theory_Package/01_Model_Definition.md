# 01 模型定义（阶段一：模型数学结构确认）

> **状态**：前期材料，位于 `杂项/新版本/Theory_Package/`，**不是论文正文**。
> **术语**：本阶段统一使用 *scheduled Koopman predictor* 与 *measurement-dependent input modulation*；按计划书「当前禁止修改事项」，本阶段**不作 bilinear Koopman 声称**（理由与裁决见 `DEC-079`）。
> **本文件不含任何实验数值。**
> **对应计划书**：第一阶段「模型数学结构确认」。

---

## 1. 数据、坐标与符号

离散时间 $k \in \mathbb{Z}$。

| 符号 | 含义 | 类型/维数 |
|---|---|---|
| $s_k$ | 物理状态（真实构型），**不作观测量使用** | $\mathcal{S}$ |
| $x_k = h(s_k)$ | 测量状态（传感器读数） | $\mathbb{R}^n$ |
| $h$ | 测量映射（$s_k \mapsto x_k$） | $\mathcal{S} \to \mathbb{R}^n$ |
| $n_\psi$ | 提升特征维数 | 整数；$d = n + n_\psi$ |
| $u_k$ | 控制输入 | $\mathcal{U} \subseteq \mathbb{R}^m$，$\mathcal{U}$ 紧凸 |
| $P \ge 2$ | 历史长度（整数） | — |
| $X_k$ | 历史测量窗口 | $\mathbb{R}^{P n}$ |
| $U_k^{\mathrm{in}}$ | 过去输入窗口 | $\mathbb{R}^{(P-1)m}$ |
| $z_k$ | 提升状态 | $\mathbb{R}^{d}$，$d = n + n_\psi$ |
| $c_k$ | scheduling context | $\mathbb{R}^{d_c}$ |
| $\chi_k$ | $B$ 的调度变量 | $\mathbb{R}^{n}$ |
| $r_A, r_B$ | 低秩修正的秩上界 | 整数 |
| $g_A, g_B$ | 低秩修正的幅度界常数 | $>0$ |

**坐标约定（重要）**：本预测模型定义在**测量坐标**上。它**不**声称是定义在 $s$ 上的无限维 Koopman 算子的有限维截断；$A, B$ 是选定提升坐标下的**受控预测参数化**。这一区分对应项目规则「物理状态、测量状态与提升状态严格区分」，同时避免把 $A, B$ 直接等同于 Koopman 算子。

## 2. 历史窗口与 context（计划书第一阶段第 1 条）

$$
X_k = \begin{bmatrix} x_{k-P+1} \\ \vdots \\ x_k \end{bmatrix} \in \mathbb{R}^{P n},
\qquad
U_k^{\mathrm{in}} = \begin{bmatrix} u_{k-P+1} \\ \vdots \\ u_{k-1} \end{bmatrix} \in \mathbb{R}^{(P-1)m}.
$$

- $X_k$ 含 $P$ 个**测量状态**；$U_k^{\mathrm{in}}$ 含 $P-1$ 个**过去输入**。
- **当前输入 $u_k$ 不进入 context。** context 只描述「截至 $k$ 已发生的轨迹」；$u_k$ 通过 §4 的输入项独立进入一步预测。计划书第一阶段把这一条单独列出，故在此显式声明，并在后续所有推导中保持一致。
- context 映射的输入维度为 $P n + (P-1) m$。

$$
c_k = C_\phi\!\left(X_k, U_k^{\mathrm{in}}\right) \in \mathbb{R}^{d_c}.
$$

$C_\phi$ 的解析形式与参数在本阶段不固定；后续推导只要求它满足 `02_Assumptions.md` 中列出的正则性（Lipschitz、可微），**不要求它是单射**。

## 3. 提升（lifting）

$$
z_k = g_\theta(X_k) = \begin{bmatrix} x_k \\ \psi_\theta(X_k) \end{bmatrix} \in \mathbb{R}^{d},
\qquad d = n + n_\psi .
$$

- **state-preserving**：当前测量在提升后仍然可见，即
  $$
  C_x z_k = x_k, \qquad C_x = \begin{bmatrix} I_n & 0 \end{bmatrix}.
  $$
  这条结构在论文旧版中已成立，属于可复用的资产（`DEC-076` 选项 (a)）。
- **两种 $z$ 必须区分**（项目规则「同一符号同一含义」）：
  - $z_k^{\mathrm{enc}} = g_\theta(X_k)$：每步用真实测量窗口**重新编码**得到；
  - $z_k^{\mathrm{prop}}$：由 §4 的递推**传播**得到，其「$x$ 槽位」会与真实测量漂移。
  后续 `05_Prediction_Error_Bound.md` 显式处理二者的差。

## 4. 调度转移与测量条件输入矩阵（计划书第一阶段第 2、3 条）

$$
\boxed{\; z_{k+1} = A(c_k)\, z_k + B(\chi_k)\, u_k \;}
\qquad\text{其中}\qquad \chi_k = C_x z_k .
$$

### 4.1 低秩调度转移

$$
A(c) = A_0 + U_A \operatorname{diag}\!\big(\gamma_A(c)\big) V_A^{\top},
\qquad
U_A = \begin{bmatrix} u_{A,1} & \cdots & u_{A,r_A} \end{bmatrix},\;
V_A = \begin{bmatrix} v_{A,1} & \cdots & v_{A,r_A} \end{bmatrix} \in \mathbb{R}^{d \times r_A},
$$

$$
\gamma_{A,j}(c) = g_A\, \pi_{A,j}(c)\, \tanh\!\big( [W_A c + b_A]_j \big),
\qquad
\pi_A(c) = \operatorname{softmax}\!\big( W_A^{\pi} c + b_A^{\pi} \big).
$$

- $A_0 \in \mathbb{R}^{d \times d}$：**共享名义转移**。
- 低秩修正的秩满足
  $$
  \operatorname{rank}\!\big(A(c) - A_0\big) \le r_A ,
  $$
  因为它至多是 $r_A$ 个秩一矩阵的和。
- **因子归一化（本文件定死一种）**：$\|u_{A,j}\|_2 \le 1$ 且 $\|v_{A,j}\|_2 \le 1$（$j = 1,\dots,r_A$）。取 $\le 1$ 而不是 $=1$，使结论对训练后的实际范数仍然成立，且不改变界的形式。
- **调制函数形式（明确）**：$\pi_A$ 是 softmax ⇒ 非负且 $\sum_j \pi_{A,j}(c) = 1$；$\tanh$ 饱和 ⇒ $|\tanh(\cdot)| < 1$。二者合起来使 $|\gamma_{A,j}(c)| \le g_A \pi_{A,j}(c)$，这是 `03_Low_rank_Boundedness.md` 证明的**唯一**依据。

### 4.2 测量条件输入矩阵

$$
B(\chi) = B_0 + U_B \operatorname{diag}\!\big(\gamma_B(\chi)\big) V_B^{\top},
\qquad
\gamma_{B,j}(\chi) = g_B\, \pi_{B,j}(\chi)\, \tanh\!\big( [W_B \chi + b_B]_j \big),
$$

$$
U_B = \begin{bmatrix} u_{B,1} & \cdots & u_{B,r_B} \end{bmatrix} \in \mathbb{R}^{d \times r_B},
\qquad
V_B = \begin{bmatrix} v_{B,1} & \cdots & v_{B,r_B} \end{bmatrix} \in \mathbb{R}^{m \times r_B},
\qquad
B_0 \in \mathbb{R}^{d \times m},
$$

$$
\pi_B(\chi) = \operatorname{softmax}\!\big( W_B^{\pi} \chi + b_B^{\pi} \big),
\qquad
W_B \in \mathbb{R}^{r_B \times n},\; b_B \in \mathbb{R}^{r_B},
\qquad
W_B^{\pi} \in \mathbb{R}^{r_B \times n},\; b_B^{\pi} \in \mathbb{R}^{r_B}.
$$

同样的归一化约定（$\|u_{B,j}\|_2 \le 1$、$\|v_{B,j}\|_2 \le 1$）与同样的 softmax 结构，$\operatorname{rank}(B(\chi) - B_0) \le r_B$。

**注意维数**：$V_B$ 的第二维是 $m$（输入维数）而**不是** $d$，因为 $B(\chi)$ 把输入映到提升状态；这与 $A$ 的因子（$U_A, V_A \in \mathbb{R}^{d \times r_A}$）不同。

### 4.3 关于 $\chi_k$ 的精确含义（防符号歧义）

计划书 Q1 的推荐是「$x_k = C z_k$，保持 measurement-dependent」。本文件把它写成 $\chi_k = C_x z_k$ 并说明其两种读法：

- 当 $z_k = z_k^{\mathrm{enc}}$ 时，$\chi_k = C_x z_k^{\mathrm{enc}} = x_k$：**恰好是当前测量**。
- 当 $z_k = z_k^{\mathrm{prop}}$（预测/rollout 中）时，$\chi_k = C_x z_k^{\mathrm{prop}}$：是模型**自带的 $x$ 槽位**，会与真实测量漂移。

这样选择的原因是**自洽**：预测时不可能拿到未来真实测量，所以 $B$ 的调度变量必须由模型自身的状态给出。冻结 LTV 构造（`06_Frozen_LTV_QP_Proof.md`）里用的是名义 rollout 的 $\bar{x}_i = C_x \bar{z}_i$，与这里一致。

## 5. 为什么 $A$ 用历史、$B$ 用当前测量（双调度变量）

- **$A$ 依赖历史 context**：多步动力学模式随工况切换（软体对象、变工况），需要一段轨迹才能判别当前处于哪种模式。
- **$B$ 依赖当前测量**：输入效力随当前构型变化（软体机器人弯曲/充气状态下同一输入的响应不同），这是**当前几何**的函数，与历史无关。
- **为什么必须分开**：若 $A$ 与 $B$ 共用同一个 context，则「动力学模式」与「输入效力」两个因素被压进同一向量，参数不可辨识（同一 context 需同时解释两者）。分成 $c_k$ 与 $\chi_k$ 两个调度变量后，二者各自由最直接的证据驱动（历史 / 当前测量）。该论证来自旧路线文件（`论文/新版本.txt` §2.4），**在新路线中仍然成立**，故保留。

## 6. 与「严格双线性 Koopman」的关系（本阶段**不声称**）

把 $(c_k, \chi_k)$ 视为**外部调度信号**时，本模型是**调度线性（scheduled linear）**的：给定调度，$z \mapsto z_{k+1}$ 关于 $(z_k, u_k)$ 是仿射的。只有当把 $u$ 与 $z$ 的乘积项显式展开书写时，它才呈双线性外形。

计划书明确要求本阶段**不使用**严格 bilinear Koopman 术语，并把它列入禁止清单（连同「不改摘要/Introduction/实验/标题」）。因此：

- 本阶段所有材料一律用 *scheduled Koopman predictor* + *measurement-dependent input modulation*；
- 旧路线文件中的 bilinear 框架**推迟**到论文阶段由用户裁决，**不是**被判为错误（`DEC-079`）。

## 7. 本文件的决定与未决项

> 本表同时列出**已决**（本文件定死，后续文件须沿用）与**未决/待核实**（不得被当作已定事实使用）两类。

| # | 事项 | 状态 |
|---|---|---|
| 1 | $\gamma$ 的 tanh 输入是否含归一化层（LayerNorm 等） | **待核实**：需与用户确认（本文件 §4.1/§4.2 已按「不含归一化层」的 $[W c + b]$ 形式写定，属工作定义）；若含，则 $W_A c + b_A$ 需换成 $\tilde{W}_A \,\mathrm{Norm}(c) + \tilde{b}_A$，`03` 的结论不变，但 $L_A$ 的表达式要改 |
| 2 | 列归一化取 $=1$ 还是 $\le 1$ | **已决**：取 $\le 1$（更保守，界的形式不变；紧性的确界不超过 $g_A$，见 `03` 备注 2/3） |
| 3 | $d, n_\psi, d_c, r_A, r_B$ 的具体数值 | 未定；属实验阶段 |
| 4 | $P$ 的取值 | 未定；属实验阶段 |
| 5 | $A_0, B_0$ 是学习得到还是固定 | **待核实**：旧实现中 $B$ 固定；新路线要求 $B$ 可调度，$B_0$ 的取法需与用户确认 |

## 8. 交接

- `03_Low_rank_Boundedness.md`：由 §4 的参数化证明 $\|A(c)-A_0\|_2 \le g_A$、$\|B(\chi)-B_0\|_2 \le g_B$。
- `02_Assumptions.md`：列出后续所有推导共用的正则性假设（含 $C_\phi$、$g_\theta$、$\psi_\theta$）。
- `04_Scheduling_Lipschitz.md`：给出 $L_A, L_B$ 的显式表达式（依赖 $\|W_A\|_2$、$\|W_B\|_2$ 与 $C_\phi$ 的 Lipschitz 常数）。
- `06_Frozen_LTV_QP_Proof.md`：使用 §4.3 的 $\bar{x}_i = C_x \bar{z}_i$ 约定构造冻结调度。
