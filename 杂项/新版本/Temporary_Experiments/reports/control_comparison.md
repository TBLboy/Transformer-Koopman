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
「用被测试控制器自身的同一个学习模型当唯一 plant」因此被避免；M5 的**非冻结**完整模型
只作 sanity 参考，不作唯一 plant。

## 2. Gate 3 — 控制器单元测试

**命令**

```powershell
D:\conda\envs\edmddl2\python.exe -u tests\test_ltv_qp.py   # cwd = 杂项/新版本/Temporary_Experiments
```

**结果：28/28 通过。** 原始输出 `results/control/gate3_unit_tests.txt`，
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

*待运行：`python scripts/run_gate4.py --split test`。*

## 4. Gate 5 — 理论—实验交叉核验（冻结调度误差）

*待运行：`python scripts/run_gate5.py`。*

## 5. 未验证项与待确认问题

- `u_limit = ±100` 仅来自旧部署配置，**尚未由用户确认**（Q3）；所有控制结论以此假设为前提，
  并额外给出 `data_range_u` 敏感性设置以隔离外推影响。
- 未做真实硬件实验；无急停/传感器异常/控制超时回退的实测。
- 控制权重为**先验固定**（`configs/control_protocol.yaml`），另做敏感性分析；
  不以控制器相对优劣为准则调参。
- C3（完整非线性 MPC）与 C4（多次调度更新）未实现，原因已登记在 `configs/control_protocol.yaml`，
  **不是**被静默丢弃。

