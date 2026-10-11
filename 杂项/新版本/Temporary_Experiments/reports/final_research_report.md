# 临时建模与控制实验：最终研究报告

> **状态**：临时实验材料，**不是论文正文**；不修改论文任何章节。
> **计划书**：`C:/Users/12187/Downloads/Temporary_Modeling_and_Control_Experiments_Plan.md`（Gate 0–5）。
> **事实源**：`results/**`（机器可读）＋ `reports/modeling_comparison.md`、`reports/control_comparison.md`（脚本生成）。
> **数值来源**：本文件只做综合与索引；**所有数值以两个 gate 报告与 `results/**` 为准**，不在此重复键入。

---

## 1. 目标与边界

**WP-M（系统辨识与多步预测比较）**：在**同一数据、同一划分、同一预测任务、同等调参预算**下，比较
旧模型 `A(c)z+B0u`、新模型 `A(c)z+B(χ)u`（`χ=C_x z=x_k`）、以及 M0–M3/M6 基线的多步开环预测能力。

**WP-C（控制比较）**：在 WP-M 冻结的模型上构建冻结调度 LTV-MPC，**先做离线闭环仿真**；真实硬件试验未做。

**不做**（计划书 §0）：预设优劣、修改原论文结果、把离线回放说成闭环控制、用测试集选超参数、
把预测模型当作真实被控对象而声称完成真实控制验证。

---

## 2. 数据与协议（冻结口径）

| 项 | 值 | 来源 |
|---|---|---|
| 数据 | 真实平台采集；100 条记录 × 300 步；dt = 0.2 s | `configs/data_manifest.yaml`、`reports/data_audit.md` |
| 语义 | x = 光点在二维屏幕的移动坐标；u = 电机控制量（用户 2026-10-11 确认，DEC-084） | 同上 |
| 划分 | 按**完整轨迹** 70/20/10；滑动窗口不跨轨迹、不跨划分 | `configs/split_manifest.yaml` |
| 归一化 | 仅 train 拟合后冻结 | `models/protocol.py` |
| 窗口 | P = 8 测量 + P−1 = 7 过去输入；当前输入 `u_k` **不进** context | `configs/modeling_protocol.yaml` |
| 递推 | **latent 递归传播**（`z_0 = g_θ(X_0)` 只算一次；`X_i` 由传播后的 `C_x z_j` 构成） | `DEC-085`、单测 T7 |
| 评估起点 | 冻结整数算法生成，所有模型/种子完全相同 | `models/protocol.py` |
| 选择准则 | validation 多步 rollout RMSE（H=25）；**从不使用 test** | `scripts/run_gate1.py` |
| 预算 | 每模型 6 trial random search → 选定配置 3 seed 重训 → test 只评估一次 | `configs/search_spaces.yaml` |
| 硬件 | NVIDIA RTX 4060 Laptop 8 GB；torch 2.6.0+cu124 | `results/modeling/gate1_run.log` |

---

## 3. Gate 状态

| Gate | 状态 | 证据 |
|---|---|---|
| 0 数据/代码审计 | ✅ conditional go（C1–C5 已闭合） | `EV-*`、`REV-TASK044-001..004`、`gate --task TASK-044` allowed |
| 1 基线预测 M0–M6 | ✅ | `EV-GATE1-MODELS-001` |
| 2 有效性诊断 E-M3/E-M4/E-M5 | ✅ | `results/modeling/gate2_diagnostics.json` |
| 3 控制器单测 | ✅ 31/31 | `EV-GATE3-QP-001`、`results/control/gate3_unit_tests.txt` |
| 4 控制场景（离线闭环） | ✅ | `results/control/control_test.json`、`control_val_search.json`、`reports/control_comparison.md` §3 |
| 5 冻结误差交叉核验 | ✅ | `results/theory_diagnostics/freezing_diagnostics.json` |

---

## 4. 主要发现（按证据强度排序，**负结果保留**）

### F1（强，配对实验）**起作用的是历史条件化转移 `A(c)`，不是测量依赖输入调制 `B(χ)`**

E-M3 四个结构用**同一 encoder / 窗口 / latent 维度 / 损失 / 优化预算 / 种子**训练，只改调度分支：

| 结构 | roll H=25 | 结论 |
|---|---|---|
| `A0+B0` | ≈ 0.0755 | 基线 |
| `A(c)+B0` | ≈ 0.0265 | **A(c) 带来大幅改善** |
| `A0+B(χ)` | ≈ 0.0744 | **与基线无差别** |
| `A(c)+B(χ)` | ≈ 0.0258 | 与 `A(c)+B0` 无差别 |

→ `B(χ)` 分支在本数据集上**没有可测量的收益**（增益全部来自 `A(c)`）。这与"两个分支都重要"的论文叙事**不一致**，
必须如实报告（详见 `reports/modeling_comparison.md` §6）。

### F2（强）Gate 1 主表里 M4 与 M5 **被搜索选中了完全相同的配置**，且误差在噪声内并列

| 方法 | one-step | roll H=25 | 参数量 |
|---|---|---|---|
| M4 `A(c)+B0` | ≈ 0.0093 | ≈ 0.0265 | 20818 |
| M5 `A(c)+B(χ)` | ≈ 0.0094 | ≈ 0.0258 | 20872 |

参数量相差 0.26%（E-M4 容量匹配因此是**平凡满足**）→ 不能用"参数量更多"解释任何差异，
也不能把两者差异称为收益（差值远小于种子间波动）。

### F3（强）调度分支**确实在动**，但幅度小；且**调度后的 A 不稳定**

E-M5（test 起点）：`‖A(c)−A0‖₂ max ≈ 0.027`（ΔA 有效秩 3），`‖B(χ)−B0‖₂ max ≈ 0.012`，
同输入下跨测量状态的输入响应相对差仅 **1.2%–2.2%**。
同时 `ρ(A) max ≈ 1.01–1.03 > 1` → **`A(c)` 不是稳定矩阵**（理论只约束 `‖A(c)−A0‖`，不约束稳定），
与 H=100 上观察到的发散一致。这解释了为什么"有界"不等于"长时程可用"。

### F4（强）长时程（H=100）**不稳定**，且种间差异巨大

M4/M5 的 H=100 逐 seed 值为 0.24 / 0.31 / 0.63（均值 0.39 ± 0.17）——标准差与均值同量级。
M3（GRU）反而稳定（0.070 ± 0.003）。**只报均值会掩盖这一点**，故报告逐 seed 列出。

### F5（强）冻结调度误差的结构与理论一致，但**冻结决策在完整模型上并未改善代价**

Gate 5：`‖U−Ū‖ = 0` 时冻结误差**精确为 0**（Theory 07 §2：驱动量是输入不匹配，而非 δ_A/δ_B 本身）；
误差随 `‖U−Ū‖` 单调增长；代价差最大约 1e-2。`nominal_rollout` 与独立实现的自检差为 0。

决策比较（同一输入约束集 `u ∈ [-3.5, 3.5]`，两个问题都只用输入约束）：

| 量 | 值 |
|---|---|
| `J_full(U_fr)`（冻结 QP 解代回完整模型） | ≈ 4.96e-3 |
| `J_full(U_nominal)`（原始记录输入） | ≈ 4.13e-3 |
| `J_full(U_loc)`（完整问题局部 NLP 解） | ≈ 3.34e-3 |
| `J_full(U_fr) − J_full(U_loc)` | ≈ 1.63e-3 |

**必须如实报告的观察**：冻结 QP 解代回**完整模型**后的代价**高于**原始记录输入，
即冻结近似的决策在本例中**没有带来改善**。该结论只针对本起点、本权重、本局部求解器，
**不声称全局次优性**，也不推广为"冻结方法无效"。

### F6（强）控制器数值正确性已被独立参照验证

31 项单测：冻结仿射映射 `Z=F+GU` 与显式冻结 rollout 逐位一致（6.7e-16）；OSQP 与 cvxpy 独立参考
目标值/解一致（max|ΔU| = 2.4e-15）；盒约束满足；LTI 退化情形冻结模型与完整 rollout 完全一致。

### F7（Gate 4，离线闭环仿真）调度模型在 plant A 上明显优于线性基线，但**结论不稳健且大部分是外推**

| 指标 | plant A (M3 GRU) | plant B (M6 Transformer) |
|---|---|---|
| 跟踪 RMSE（C0 / C1 / C2） | 0.413 / 0.210 / 0.212 | 0.339 / 0.279 / 0.319 |
| 定点稳态误差（C0 / C1 / C2） | 0.473 / 0.409 / 0.412 | 0.285 / 0.259 / 0.355 |
| 输入越界比例（超出 train 范围） | 0.79 / 0.42 / 0.44 | 0.90 / 0.73 / 0.78 |
| 约束违反 / 求解失败 | 0 / 0 | 0 / 0 |
| 中位求解耗时 | 0.06–0.12 ms | 0.10–0.12 ms |

**必须同时报告的限定条件**：

1. **C1 ≈ C2**（与 Gate 1/2 一致）→ 闭环里 `B(χ)` 同样没有带来收益。
2. **输入越界比例 0.42–0.90**：控制器把学习到的 plant 推出训练输入范围，
   因此这些数字**大部分是外推**，只能作「在所学 plant 上的相对比较」，**不能**当作真实平台性能。
3. **排序不稳健**：把权重/时域同时施加到三个控制器后，`tight_R` 与 `N20` 下 **C0 反而最好**
   （见 `reports/control_comparison.md` §3.5）→ 不能宣称"调度控制器更优"。
4. **有一个场景对三个控制器都失败**：`setpoint_2`（p95/p05 目标）RMSE 1.40、稳态误差 1.17、
   输入越界 100% → 该目标在本 plant + 本约束下**不可达**，属场景设计问题，已如实列出。
5. **M6 的种子 0 训练不可复现**（同种子重跑 one-step 差 1.74e-2，约 40%），
   故 plant B 的结论只对本进程实际使用的那个 M6 成立；报告已改用**实际 plant 的**保真度并给出复现检查表。
6. 离线求解耗时**不是**控制周期；未做任何实时性声明。

---

## 5. 过程中发现并已修正的真实缺陷

| # | 缺陷 | 影响 | 处理 |
|---|---|---|---|
| 1 | **rollout 每步重新编码**，与 `Theory_Package/01` §4.3、`06` §2 的 latent 递归传播冲突 | 首轮 Gate 1 训练全部作废；冻结 LTV 与模型自身 rollout 不自洽 | 改为 latent 传播（`DEC-085`），新增单测 T7 断言 encoder 每 rollout 只调 1 次 |
| 2 | 目标函数缺与 `U` 无关的常数项 | `UᵀMU+2fᵀU` 与直接求和不一致 | 修正并纳入单测 T2 |
| 3 | E-M5 有效秩在 `ΔA ≡ 0` 时出现 0/0 | 假值 1 | 修正为 rank 0 + `degenerate=True`，重算 E-M5 |
| 4 | 闭式模型 M0/M1/M2 的拟合矩阵不在 `state_dict` | 加载 checkpoint 得到 `A=None` 并崩溃 | `load_or_train` 对闭式模型强制重训 |
| 5 | 主机内存（16 GB，训练时仅余 ~3 GB）耗尽 | 长时训练中断；报错表现为 **CUDA OOM 而 GPU 仅占 32 MiB** | 逐模型独立进程 + `gc.collect()`/`empty_cache()` + batch 128 |

框架缺陷（`.project-log/docs/framework-defects.md`）：本轮新增 `D-016`（evidence schema 无文档、
`file_hashes` 路径基准靠试错）、`D-017`（无"工作留痕"记录种类）。

---

## 6. 未验证项与未决问题（不得当作已完成）

1. **`u_limit = ±100` 未由用户确认**（Q3）——仅来自旧部署配置；所有控制结论以此假设为前提，
   并额外给出 `data_range_u` 敏感性设置以隔离 plant 外推影响。
2. **没有真实硬件实验**；无急停、传感器异常、控制超时回退的实测。
3. **未声称**：闭环稳定性、递归可行性、实时性/截止时间（离线 QP 求解耗时不等于控制周期）、
   非凸完整问题的全局最优性。
4. M8（PatchTST-style 受控预测器）与 M9（Deep Koopman）**未实现**；C3（完整非线性 MPC）、
   C4（多次调度更新）**未实现**，原因已登记在 `configs/control_protocol.yaml`，不是被静默丢弃。
5. 文献任务只完成**元数据核实与改造点对照**（`reports/literature_baselines.md`），逐篇精读未完成；
   `#4 Lusch et al. (2018)` 的 DOI 标为**待核实**。
6. 超参搜索预算为 6 trial/模型（计划书建议 12），理由记录在 `configs/search_spaces.yaml`。
7. 跨轨迹方差为**单 seed 补充诊断**（统计单位为一条独立测试轨迹）。

---

## 7. 对研究方向的直接含义（供用户决策，不代替用户决策）

- 若论文的核心卖点是"**测量依赖的输入调制 `B(χ)`**"，本实验**不支持**该卖点：
  在本数据集上它没有可测量的预测收益，且其幅度仅 1–2%。
- 有实证支持的部分是"**历史条件化的转移 `A(c)`**"，但它**不稳定**（`ρ(A) > 1`），
  长时程误差发散，且 M3（GRU）在 H=100 上明显更稳——这构成对"用 scheduled Koopman 做长时程预测"的实质挑战。
- 上述结论只在**本数据集、本划分、本预算**下成立，不支持跨工况泛化。

---

## 8. 交付物索引

| 类别 | 文件 |
|---|---|
| 审计 | `reports/data_audit.md`、`reports/code_audit.md`、`reports/go_no_go.md` |
| 配置 | `configs/data_manifest.yaml`、`split_manifest.yaml`、`modeling_protocol.yaml`、`search_spaces.yaml`、`control_protocol.yaml` |
| 代码 | `models/protocol.py`（唯一评估实现）、`models/library.py`、`controllers/ltv_mpc.py`、`scripts/*.py` |
| 测试 | `tests/test_ltv_qp.py`（31 项） |
| 结果 | `results/audit/`、`results/modeling/`、`results/control/`、`results/theory_diagnostics/` |
| 报告 | `reports/modeling_comparison.md`、`reports/control_comparison.md`、`reports/literature_baselines.md`、`reports/gate_review_scope.md` |
| 图 | `figures/em1_summary.png`、`figures/em2_horizon_rmse.png` |
| 检查点 | `checkpoints/*.pt` |
