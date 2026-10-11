# 08 条件次优性（Theorem 3）

> **状态**：前期材料，**不是论文正文**；不含实验数值。
> **对应计划书**：第六阶段「次优性条件」（计划书 Q3：用 $0 \le J_{\mathrm{full}}(u^{\mathrm{fr}}) - J_{\mathrm{full}}(u^\star) \le 2\varepsilon_J$ 的**条件形式**，**不假设** $CN(\delta_A + \delta_B)$）。
> **依赖**：`01`、`02`（A1、A3、A5）、`04`（命题 2）、`06`（冻结问题）、`07`（定理 2）。

---

## 1. 两个代价函数

固定当前提升状态 $z_k$、参考轨迹 $\{z^{\mathrm{ref}}_i\}$、名义输入 $\bar U$、时域 $N$。

**(a) 完整代价** $J_{\mathrm{full}}(U)$：按 `06` §1，轨迹用**完整模型**（调度由自己的轨迹生成）。

**(b) 冻结代价** $J_{\mathrm{fr}}(U; \bar U)$：按 `06` §4，轨迹用**冻结 LTV 模型**，权重分块 $(\bar Q, \bar R, \bar S)$ 与 $J_{\mathrm{full}}$ 相同。

**关键结构性事实**：两个代价的**输入项完全相同**，故在作差时**自动抵消**。具体地（`06` §4 已统一记号）：

- $R$ 项：两侧都是 $\|U - U^{\mathrm{ref}}\|_{\bar R}^2$，**逐项相同**；
- $S$ 项：两侧都是 $\sum_{i=0}^{N-1}\|u_i - u_{i-1}\|_S^2$（$u_{-1}$ 为已知常数），**逐项相同**——`06` 第一版曾把它写成含参考速率的 $\|DU - DU^{\mathrm{ref}}\|^2$，那会破坏抵消，现已修正；
- 唯一差异来自状态项 $Q$ 与终端项 $P$。

因此只有**状态项**会产生差异——这是下面 $\varepsilon_J$ 显式化的基础。**但要小心一处下标**：$J_{\mathrm{fr}}$ 的堆叠状态 $Z$ 从 $z_1$ 起（`06` §4），不含 $i=0$ 的状态项，而 $J_{\mathrm{full}}$ 含 $\|z_0 - z^{\mathrm{ref}}_0\|_Q^2$。因此二者还相差一个**与 $U$ 无关的常数**

$$
c_0 \;:=\; \big\| z_k - z^{\mathrm{ref}}_0 \big\|_Q^2 \qquad (z_0 = z_k \text{ 固定}),
$$

它必须计入 $\varepsilon_J$（§2 已计入；否则 $\varepsilon_J$ 不是 $\sup_U|J_{\mathrm{full}}-J_{\mathrm{fr}}|$ 的上界——$N=1$ 时可直接验证）。

## 2. 一致代价近似（**假设**，且给出可计算的显式上界）

### 假设 (CA)

$$
\sup_{U \in \mathcal{U}_{\mathrm{feas}}} \big| J_{\mathrm{full}}(U) - J_{\mathrm{fr}}(U; \bar U) \big| \;\le\; \varepsilon_J .
$$

> 这是本文件**唯一的额外假设**（`02` §3 的越级防护表里没有它，因为它是本文件新引入的）。计划书 Q3 明确允许这种条件形式，并**禁止**直接假设 $CN(\delta_A+\delta_B)$。下面把 $\varepsilon_J$ **显式化**，使它从「抽象假设」变成「可计算的量」。

### $\varepsilon_J$ 的显式上界（**可推导**）

由 `07` 定理 2，两条轨迹之差满足 $\|e_i\|_2 \le K_i$，其中

$$
K_i \;:=\; \delta_{\mathrm{frz}} \sum_{t=0}^{i-1} L^{\,i-1-t},
\qquad
\delta_{\mathrm{frz}} = L_A L_\phi M_Z\, \Delta_u \;+\; \big( L_A L_\phi \sqrt{P}\, M_Z + L_B M_U \big)\, M_B\, \delta_u \sum_{t=0}^{N-1} M_A^{\,t},
$$

其中 $\delta_{\mathrm{frz}}$ 取自 `07` 定理 2（**第二版**：第一版漏掉了名义漂移项，已被复核者的反例推翻）。由于 (CA) 要求对**整个可行集**一致成立，**这里的 $\Delta_u, \delta_u$ 取成 $\mathcal{U}_{\mathrm{feas}}$ 上的上确界**（由 $\mathcal{U}$ 紧得有限），从而 $K_i$ 对 $\mathcal{U}_{\mathrm{feas}}$ 中一切 $U$ 一致成立。

**常量来源**：$M_A := \|A_0\|_2 + g_A$、$M_B := \|B_0\|_2 + g_B$（`03` 命题 1 / `07` §3）；$L_A, L_B$（`04` 命题 2）；$L_\phi, M_Z, M_U$（`02` A1、A3）；$P$（`01` §2）；$\delta_u, \Delta_u$（`07` §2）；$L, \delta_{\mathrm{frz}}$（`07` 定理 2）；$M_{\mathrm{ref}} := \max_i\|z^{\mathrm{ref}}_i\|_2$ 与 $c_0$ 在本文件就地定义。

状态项的差（用 $e_i = z^{\mathrm{full}}_i - z^{\mathrm{fr}}_i$ 与 $z^{\mathrm{full}}_i + z^{\mathrm{fr}}_i - 2z^{\mathrm{ref}}_i$ 的恒等式）：

$$
\big| \|z^{\mathrm{full}}_i - z^{\mathrm{ref}}_i\|_Q^2 - \|z^{\mathrm{fr}}_i - z^{\mathrm{ref}}_i\|_Q^2 \big|
= \big| e_i^{\top} Q \big( z^{\mathrm{full}}_i + z^{\mathrm{fr}}_i - 2 z^{\mathrm{ref}}_i \big) \big|
\;\le\; \|Q\|_2 \, \|e_i\|_2 \, \big( \|z^{\mathrm{full}}_i\|_2 + \|z^{\mathrm{fr}}_i\|_2 + 2 M_{\mathrm{ref}} \big),
$$

其中 $M_{\mathrm{ref}} := \max_i \|z^{\mathrm{ref}}_i\|_2$。由 A1，$\|z^{\mathrm{full}}_i\|_2 \le M_Z$；由 $z^{\mathrm{fr}}_i = z^{\mathrm{full}}_i - e_i$ 得 $\|z^{\mathrm{fr}}_i\|_2 \le M_Z + K_i$。因此

$$
\big| \Delta J_i \big| \;\le\; \|Q\|_2 \, K_i \, \big( 2M_Z + K_i + 2M_{\mathrm{ref}} \big) .
$$

于是可取

$$
\boxed{\;
\varepsilon_J \;:=\; \underbrace{\big\| z_k - z^{\mathrm{ref}}_0 \big\|_{Q}^2}_{c_0\ (\text{与 } U \text{ 无关})}
\;+\; 2\big( M_Z + M_{\mathrm{ref}} \big) \Big[ \|Q\|_2 \sum_{i=1}^{N-1} K_i + \|P\|_2\, K_N \Big]
\;+\; \|Q\|_2 \sum_{i=1}^{N-1} K_i^2 + \|P\|_2\, K_N^2
\;}
$$

（第一项 $c_0$ 就是 §1 指出的 $i=0$ 常数项；第二、三项是状态项逐项差的上界。若取 $z^{\mathrm{ref}}_0 := z_k$，则 $c_0 = 0$。）

（第一项来自 $2M_Z + 2M_{\mathrm{ref}}$，第二项来自 $K_i$ 的二次余项；这里对 $K_i$ 采用保守的上界 $K_i \le K_N$ 亦可，不改变结论形式。）

**这一步的意义**：$\varepsilon_J$ **不是凭空假设的常数**，它由 $(\|Q\|_2, \|P\|_2, M_Z, M_{\mathrm{ref}}, N)$ 与 `07` 的 $(\delta_{\mathrm{frz}}, L)$ 完全决定。因此 (CA) 可以退化为一个**可数值估计**的量（量级由阶段七的临时验证给出）。

## 3. 定理 3（条件次优性）

设

- $U^{\mathrm{fr}} \in \arg\min_{U \in \mathcal{U}_{\mathrm{feas}}} J_{\mathrm{fr}}(U; \bar U)$（冻结问题的极小点，`06` 命题 4 保证它是凸 QP）；
- $U^{\star} \in \arg\min_{U \in \mathcal{U}_{\mathrm{feas}}} J_{\mathrm{full}}(U)$（完整问题的**全局**极小点）；
- 二者**可行集相同**，记为 $\mathcal{U}_{\mathrm{feas}}$。

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
| **不假设** $CN(\delta_A + \delta_B)$ | ✅ 全文没有出现该形式，也没有引入 $C, N$ 之外的调度偏差常数 |
| 推导 $CN(\delta_A+\delta_B)$ 是「阶段六可争取项」 | ⚠️ **未给出 $CN(\delta_A+\delta_B)$ 形式**（理由见下段）；**代之以** $\Delta_u, \delta_u \to \delta_{\mathrm{frz}} \to \varepsilon_J$ 这条可追溯链条的**显式上界**（§2）。按契约第 2 条，这属于「**如实报告**：该形式在不额外假设下不成立，故不采用」，而不是声称已完成 |

**为什么不走 $CN(\delta_A+\delta_B)$ 那条路**：那个形式把误差归因到 $A$、$B$ 两个**调度偏差** $\delta_A, \delta_B$。但按 `07` §2 的关键观察，本路线中冻结误差的真正驱动量是**输入不匹配** $\Delta_u$（不是 $\delta_A, \delta_B$ 本身）；硬写成 $\delta_A/\delta_B$ 不但需要额外假设（如何把窗口不匹配归到两个矩阵上），还会**掩盖真正的物理来源**。因此本文件选择用 $\Delta_u \to \delta_{\mathrm{frz}} \to \varepsilon_J$ 这条**可追溯**的链条。

## 5. 诚实边界（必须与结论一起阅读）

1. **结论是条件性的。** 它依赖 (CA)；本文件虽把 $\varepsilon_J$ 显式化，但那仍是**上界**，需要 $M_Z, M_{\mathrm{ref}}, \|Q\|, \|P\|, \delta_{\mathrm{frz}}, L$ 的数值才能给出具体大小——**本阶段没有任何数值**（阶段七的临时验证才给量级）。
2. **$U^\star$ 是完整问题的全局极小点，而完整问题是非凸的**（`06` §1）。定理 3 的界是相对于**真实全局最优**而言的；实际能算到的往往是局部解，故实际次优性可能**大于**该界所描述的量级（或需要把 $U^\star$ 换成「实际使用的参考解」并相应修改 (CA) 的适用范围）。本文件**不**声称能求出 $U^\star$。
3. **可行集必须一致。** 若完整问题含**状态约束** $z_i \in \mathcal{Z}$，则冻结问题的可行集（仿射原像）与完整问题的可行集**不同**，证明第二步失效，需要额外假设（例如「$U^\star$ 恰好对冻结问题可行」，或对两个可行集分别给出包含关系并修正常数）。本阶段只考虑**输入约束**（$u_i \in \mathcal{U}$），二者可行集相同。
4. **不声称闭环稳定、不声称递归可行性、不声称实时性。** 定理 3 是单次求解的次优性，与闭环性质无关。
5. **$\varepsilon_J$ 的表达式是保守的。** 其中每个因子都是上界（$K_i \le K_N$ 可进一步放大；$\|Q\|_2$ 用的是谱范数）。实际差距通常远小于 $2\varepsilon_J$。
6. **$\Delta_u$ 依赖名义输入 $\bar U$ 的取法**，而 $\bar U$ 是设计选择（warm start）。本文件不规定取法，也不声称任何取法的最优性。
