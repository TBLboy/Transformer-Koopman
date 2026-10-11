# 控制实验报告（WP-C）：Gate 3 / Gate 4 / Gate 5

> **状态**：临时实验材料，**不是论文正文**；本文件由 `scripts/report_control.py`
> 从 `results/control/*.json`、`results/theory_diagnostics/*.json` 与单测原始输出自动生成，
> 数值无手工填写。
>
> **诚实边界（先读）**：本报告只包含**离线闭环仿真**（控制器输出驱动一个仿真 plant 的下一步状态），
> **没有**任何真实硬件实验。所有控制结论只对所用 plant 成立。
> 离线 QP 求解耗时**不等于**闭环控制周期。

## 1. 实验框架与不声称清单

| 类别 | 定义 | 本报告是否包含 |
|---|---|---|
| 离线预测回放 | 用真实记录的控制序列评价模型 | ✅（Gate 1/2，见 `modeling_comparison.md`） |
| 闭环仿真 | 控制器输出影响仿真 plant 的下一步状态 | ✅（§3 Gate 4） |
| 真实硬件闭环 | 控制器驱动真实执行器并实时获取反馈 | ❌ **未做**，无独立安全审核 |

不声称：闭环稳定性、递归可行性、实时性/截止时间、真实硬件控制、非凸完整问题的全局最优性。

**plant 独立性**：plant A = M3（GRU 受控预测器），plant B = M6（Controlled Transformer），
与三个控制器的内部模型（`A0/B0`、M4、M5）**属于不同模型族**。计划书禁止的
「用被测试控制器自身的同一个学习模型当唯一 plant」因此被避免。

> M5 的**非冻结**完整模型在 `configs/control_protocol.yaml` 中被登记为
> `plant_C_reference_only`（`executed: false`）：它**本轮没有运行**，
> 只是一条明写的禁止项（M5 是 C2 的内部模型，单独当 plant 会构成循环论证）。

## 2. Gate 3 — 控制器单元测试

**命令**

```powershell
D:\conda\envs\edmddl2\python.exe -u tests\test_ltv_qp.py   # cwd = 杂项/新版本/Temporary_Experiments
```

**结果：31/31 通过。** 原始输出 `results/control/gate3_unit_tests.txt`，
文件哈希见 `results/control/gate3_hashes.txt`；证据 `EV-GATE3-QP-001`。

| 测试组 | 验证内容 |
|---|---|
| T1 / T1b / T1c / T1d | 冻结预测矩阵 `Z = F + G U` 与显式冻结 rollout 逐位一致；`F` 为零输入响应；`G[r,r]=B_r`；`G[r,t>r]=0` |
| T2 / T2b / T2c | 目标函数 `UᵀMU + 2fᵀU + const` 与直接求和一致；解析梯度对有限差分；`M` 对称 |
| T3 / T3b / T3c / T3d / T3e | OSQP 求解状态；与 **cvxpy 独立参考**目标值/解一致；盒约束满足；紧盒饱和 |
| T4 / T4b / T4c / T4d | `nominal_rollout` 调度与状态自洽；冻结仿射映射复现冻结 rollout；`B(χ)` 依赖测量状态；`U/V` 列范数 ≤ 1 |
| T5 / T5b | `A0B0` 调度时域恒定；**LTI 情形冻结模型与完整 rollout 完全一致** |
| T6 / T6b…T6g | 控制器端到端：首输入有限、QP 求解、代价自洽、盒约束、确定性、warm-start 移位与尾填充、warm-start 确实改变冻结调度 |
| T7 / T7b / T7c | **latent 递归传播**：一次 rollout 内 encoder 恰好调用 1 次；首步等于 one-step 预测；rollout 依赖未来控制输入 |

### 2.1 单测发现的真实缺陷（已修正并记录）

首轮 19 项中 7 项失败，其中 **2 项是实现缺陷**：

1. **目标函数缺与 `U` 无关的常数项** → `UᵀMU + 2fᵀU` 与直接求和不一致。已让 `cost_matrices`
   返回 `const`；控制器内 `J_quad` 与 `J_direct` 现逐位一致。
2. **rollout 语义错误**：原实现对每个预测步重新调用 encoder（re-encoding），使 `z_{i+1}` 不再是
   `A(c_i)z_i + B(χ_i)u_i` 的结果。`Theory_Package/01` §4.3 与 `06` §2 明确规定 `z` **递归传播**、
   `X̄_i` 由 `z̄` 的 x 槽位构成；`06` §4 的 `F/G` 推导亦以此为前提。项目论文规则 E 节要求
   「latent 递归传播与每步重新编码是不同策略，不能混写」。已改为 latent 传播（DEC-085），
   并新增 T7 断言防回归；**该修正使 Gate 1 全部训练作废重跑**。

### 2.2 与理论的一处已登记差异

计划书 §7.1 把状态代价写成**测量空间** `‖C z_i − x_i^ref‖_Q²`，`Theory_Package/06` §1 写成
**latent 空间** `‖z_i − z_i^ref‖_Q²`。数据不提供 latent 参考，故实现采用计划书口径；
已在 `controllers/ltv_mpc.py` 文件头与本报告登记（`ALIGN-001`）。若论文采用 latent 空间形式，
必须先定义 `z^ref`。

## 3. Gate 4 — 控制场景评估（离线闭环仿真）

**命令**：`python scripts/run_gate4.py --split val --search` → `python scripts/run_gate4.py --split test`

**控制器**：C0 = 固定线性模型（`A0,B0`）+ LTI-MPC；C1 = M4 `A(c)+B0` + 冻结调度 LTV-MPC；
C2 = M5 `A(c)+B(x)` + 冻结调度 LTV-MPC。三者使用**相同代价权重、相同约束、相同求解器**。

### 3.1 plant 保真度（**实际使用的 plant**，test 冻结起点）

| plant | one-step | roll H=5 | roll H=25 | roll H=100 | 来源 |
|---|---|---|---|---|---|
| plant_A_M3_GRU (M3) | 0.0164 | 0.0238 | 0.0375 | 0.0711 | checkpoint M3_seed0.pt |
| plant_B_M6_Transformer (M6) | 0.0241 | 0.0352 | 0.0668 | 0.1503 | checkpoint M6_seed0.pt |

### 3.1b 模型复现一致性检查（本进程模型 vs Gate-1 ledger 的 seed 0）

| 模型 | 本进程 one-step | ledger seed0 one-step | 绝对差 | 判定 |
|---|---|---|---|---|
| M3 | 0.016351 | 0.016351 | 0.00e+00 | 一致（<=1e-3） |
| M4 | 0.009565 | 0.009445 | 1.20e-04 | 一致（<=1e-3） |
| M5 | 0.009795 | 0.009645 | 1.50e-04 | 一致（<=1e-3） |
| M6 | 0.024095 | 0.041539 | 1.74e-02 | **不一致：种子 0 训练不可复现** |

> 若某模型不一致，说明其**训练过程本身不可复现**（同种子重跑得到不同模型）。
> 此时控制结论只对**本进程实际使用的那个模型**成立，不得用 ledger 的数值充当该 plant 的保真度。

### 3.2 定点调节（setpoint，3 个目标，100 步 = 20 s）

| plant | 控制器 | 稳态误差 | 调节步数 | 超调 % | 控制能量 | 约束违反 | 求解失败 | 中位求解 ms |
|---|---|---|---|---|---|---|---|---|
| plant_A_M3_GRU | C0 | 0.4732 | -1.0 | 429.2 | 1.36e+03 | 0.0 | 0.0 | 0.06 |
| plant_A_M3_GRU | C1 | 0.4086 | -1.0 | 374.8 | 1.1e+03 | 0.0 | 0.0 | 0.12 |
| plant_A_M3_GRU | C2 | 0.4119 | -1.0 | 374.6 | 1.1e+03 | 0.0 | 0.0 | 0.11 |
| plant_B_M6_Transformer | C0 | 0.2847 | -1.0 | 602.0 | 1.75e+03 | 0.0 | 0.0 | 0.10 |
| plant_B_M6_Transformer | C1 | 0.2589 | 8.0 | 582.4 | 909 | 0.0 | 0.0 | 0.12 |
| plant_B_M6_Transformer | C2 | 0.3553 | 1.0 | 611.4 | 1.05e+03 | 0.0 | 0.0 | 0.12 |

### 3.3 轨迹跟踪（tracking，3 条轨迹，200 步 = 40 s）

| plant | 控制器 | RMSE | MAE | 最大误差 | 相位滞后(步) | 输入变化 | 约束违反 | 求解失败 | p95 求解 ms |
|---|---|---|---|---|---|---|---|---|---|
| plant_A_M3_GRU | C0 | 0.4131 | 0.3264 | 1.3880 | 5.7 | 178 | 0.0 | 0.0 | 0.20 |
| plant_A_M3_GRU | C1 | 0.2101 | 0.1295 | 1.2706 | 4.0 | 1.93e+03 | 0.0 | 0.0 | 0.23 |
| plant_A_M3_GRU | C2 | 0.2121 | 0.1334 | 1.2405 | 3.0 | 2.02e+03 | 0.0 | 0.0 | 0.22 |
| plant_B_M6_Transformer | C0 | 0.3388 | 0.2866 | 1.2190 | 0.3 | 337 | 0.0 | 0.0 | 0.21 |
| plant_B_M6_Transformer | C1 | 0.2791 | 0.2259 | 1.2146 | 0.7 | 4.59e+03 | 0.0 | 0.0 | 0.23 |
| plant_B_M6_Transformer | C2 | 0.3194 | 0.2605 | 1.1954 | 0.7 | 5.13e+03 | 0.0 | 0.0 | 0.23 |

### 3.4 plant 外推诚实指标（超出 train 数据范围的比例）

学习到的 plant 只在训练数据分布内可信；控制器把 plant 推出该范围时，结果属于外推。

> **重要警告**：若下表输入越界比例很高，说明闭环结果**大部分是外推**。
> 此时这些数字只能作为「在所学 plant 上的相对比较」，**不能**当作真实平台性能或闭环可行性证据。

| plant | 控制器 | 状态越界比例 | 输入越界比例 |
|---|---|---|---|
| plant_A_M3_GRU | C0 | 0.000 | 0.790 |
| plant_A_M3_GRU | C1 | 0.000 | 0.417 |
| plant_A_M3_GRU | C2 | 0.000 | 0.440 |
| plant_B_M6_Transformer | C0 | 0.000 | 0.902 |
| plant_B_M6_Transformer | C1 | 0.000 | 0.733 |
| plant_B_M6_Transformer | C2 | 0.000 | 0.780 |

u 限幅（归一化）：`[[-3.584351, -3.552817], [3.567328, 3.559557]]`（冻结 ±100 物理量）与 `[[-2.0255242872797545, -2.3175170024228513], [2.036966502415223, 2.1928336905934054]]`（train 经验范围，敏感性设置 `data_range_u`）。

### 3.5 敏感性分析（validation 场景，权重对三个控制器**同时**改变）

| 设置 | plant | C0 RMSE | C1 RMSE | C2 RMSE | 排序 |
|---|---|---|---|---|---|
| default | plant_A_M3_GRU | 0.4218 | 0.2258 | 0.2157 | C2 < C1 < C0 |
| default | plant_B_M6_Transformer | 0.3472 | 0.2676 | 0.3089 | C1 < C2 < C0 |
| data_range_u | plant_A_M3_GRU | 0.2312 | 0.1507 | 0.1566 | C1 < C2 < C0 |
| data_range_u | plant_B_M6_Transformer | 0.2142 | 0.1488 | 0.1490 | C1 < C2 < C0 |
| loose_R | plant_A_M3_GRU | 0.4171 | 0.2495 | 0.2609 | C1 < C2 < C0 |
| loose_R | plant_B_M6_Transformer | 0.3697 | 0.2951 | 0.3493 | C1 < C2 < C0 |
| tight_R | plant_A_M3_GRU | 0.1812 | 0.1966 | 0.1946 | C0 < C2 < C1 |
| tight_R | plant_B_M6_Transformer | 0.1515 | 0.1777 | 0.1733 | C0 < C2 < C1 |
| more_rate | plant_A_M3_GRU | 0.3759 | 0.2098 | 0.2149 | C1 < C2 < C0 |
| more_rate | plant_B_M6_Transformer | 0.3914 | 0.1461 | 0.1422 | C2 < C1 < C0 |
| N5 | plant_A_M3_GRU | 0.4009 | 0.2774 | 0.2839 | C1 < C2 < C0 |
| N5 | plant_B_M6_Transformer | 0.2486 | 0.1299 | 0.1307 | C1 < C2 < C0 |
| N20 | plant_A_M3_GRU | 0.3673 | 0.3805 | 0.4168 | C0 < C1 < C2 |
| N20 | plant_B_M6_Transformer | 0.4364 | 0.6878 | 0.6778 | C0 < C2 < C1 |

> 该表用于检验排序是否依赖某一组权重；**不用于挑选用权重**。主比较使用 `default`。

## 4. Gate 5 — 理论—实验交叉核验（冻结调度误差）

**定义（计划书 §9）**：对**同一个候选输入序列** `U` 与名义序列 `Ū`：

- `z_full(U)`：每一步重算 `A(c_i), B(χ_i)`；
- `z_fr(U; Ū)`：先用 `Ū` 做名义 rollout 得到 `Ā_i, B̄_i`，再在候选 rollout 中冻结。

**不得**把两个控制器各自轨迹的差异称为冻结误差。

模型 `M5`，时域 H=25，起点数 24。

| ‖U−Ū‖ 水平 | 实测 ‖U−Ū‖ | max‖z_full−z_fr‖ | max‖c_full−c̄‖ | ‖A_full−Ā‖₂ max | ‖B_full−B̄‖₂ max | 代价差 max |
|---|---|---|---|---|---|---|
| 0.00 | 0.000 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| 0.25 | 1.716 | 1.495e-01 | 7.249e-01 | 1.289e-02 | 9.111e-04 | 5.402e-04 |
| 0.50 | 3.610 | 3.481e-01 | 1.496e+00 | 2.681e-02 | 1.931e-03 | 1.721e-03 |
| 1.00 | 7.001 | 1.026e+00 | 2.498e+00 | 4.532e-02 | 5.486e-03 | 9.519e-03 |
| 2.00 | 13.914 | 1.223e+00 | 2.853e+00 | 4.895e-02 | 5.722e-03 | 7.866e-03 |

**理论一致性检查**

- P1（`U = Ū` 时冻结误差恒为 0，07 §2：驱动量是输入不匹配而非 δ_A/δ_B 本身）：**成立**
- P2（冻结误差随 ‖U−Ū‖ 增长）：**成立**

**决策比较（同一可行集、仅输入约束）**

| 量 | 值 |
|---|---|
| `J_full_U_frozen_QP` | 0.004961661955795967 |
| `J_full_U_recorded_nominal` | 0.004132503382255583 |
| `J_full_U_local_NLP` | 0.0033365781869057246 |
| `gap_vs_local_NLP` | 0.001625083768890242 |
| `gap_of_nominal_vs_local_NLP` | 0.0007959251953498585 |
| `local_solver_success` | True |
| `qp_status` | solved |
| `same_feasible_set` | True |
| `constraint` | u in [-3.5, 3.5] (both problems, input-only constraints) |

> J_full(U_fr) - J_full(U_loc) is measured against a LOCAL L-BFGS-B solution of the non-convex full problem, NOT against a global optimum; no global suboptimality value is claimed.

**不声称**：global optimality of the non-convex full problem；epsilon_J certificate (the constants would need to be estimated, and an empirical bound is not a certificate)；closed-loop stability, recursive feasibility or real-time performance。

## 5. 未验证项与待确认问题

- `u_limit = ±100` 仅来自旧部署配置，**尚未由用户确认**（Q3）；所有控制结论以此假设为前提，
  并额外给出 `data_range_u` 敏感性设置以隔离外推影响。
- 未做真实硬件实验；无急停/传感器异常/控制超时回退的实测。
- 控制权重为**先验固定**（`configs/control_protocol.yaml`），另做敏感性分析；
  不以控制器相对优劣为准则调参。
- C3（完整非线性 MPC）与 C4（多次调度更新）未实现，原因已登记在 `configs/control_protocol.yaml`，
  **不是**被静默丢弃。

