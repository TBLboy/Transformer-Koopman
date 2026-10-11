# TASK-045 独立复核范围（给 verification-reviewer）

> **用途**：复核者在本会话**没有 shell**，无法自行跑命令或算哈希。因此本文件把
> `done_when` 契约、被评范围、可读证据与原始输出集中列出，供逐条核对（框架缺陷 D-013）。
>
> **任务**：`TASK-045`（GOAL-003 临时建模与控制实验，Gate 1–5）。风险等级：**strict**。
> **被评范围**：`杂项/新版本/Temporary_Experiments/` 下的模型、控制器、脚本、配置、结果与报告；
> 以及 `.project-log` 中与本次实验相关的记录。
> **不在范围**：论文正文（`论文/`）、源数据（`数据备份/`）、旧路线代码（只读参考）。

---

## 1. done_when 契约（复核据此判定 go / conditional / no-go）

| Gate | 计划书要求（§11） | 判定证据 |
|---|---|---|
| 0 | 数据与代码审计交付四件套；未通过不得训练 | `reports/data_audit.md`、`reports/code_audit.md`、`configs/data_manifest.yaml`、`reports/go_no_go.md`；`REV-TASK044-001..004` |
| 1 | M0–M6 在同一协议/划分/评估下完成；validation 选择、≥3 seed、test 只评估一次；失败 trial 不得静默排除 | `results/modeling/gate1_ledger.json`、`reports/modeling_comparison.md`、`EV-GATE1-MODELS-001` |
| 2 | E-M3 配对结构消融（同 encoder/窗口/latent/损失/预算）、E-M4 容量匹配、E-M5 调度诊断；负结果保留 | `results/modeling/gate2_diagnostics.json`、`reports/modeling_comparison.md` §6–§8 |
| 3 | 冻结 LTV-QP 的约束/预测矩阵/目标函数/求解状态通过数值测试 | `tests/test_ltv_qp.py`、`results/control/gate3_unit_tests.txt`、`EV-GATE3-QP-001` |
| 4 | 离线闭环仿真；plant 不得是控制器自身模型；区分回放/闭环仿真/真实硬件 | `results/control/control_*.json`、`reports/control_comparison.md` §3 |
| 5 | 冻结误差定义、计算与理论一致；经验结果不得写成无条件理论保证 | `results/theory_diagnostics/freezing_diagnostics.json`、`reports/control_comparison.md` §4 |

## 2. 必须独立核对的具体断言（不是"看起来对"）

1. **同一评估实现**：所有模型的窗口/起点/指标是否都走 `models/protocol.py`（唯一实现），有无旁路。
2. **无测试集泄漏**：超参选择是否只用 validation；test 是否在超参冻结后只评估一次。
3. **无未来测量泄漏**：`ScheduledKoopman.rollout` 是否为 latent 递归传播（encoder 一次 rollout 只调 1 次，单测 T7）。
4. **冻结 LTV 与理论一致**：`Z = F + G U` 的构造是否与 `Theory_Package/06` 的 `G_{i,t}` 约定一致（单测 T1/T4/T5b）。
5. **求解器正确性**：OSQP 解是否与独立参考（cvxpy）一致（单测 T3）。
6. **plant 独立性**：Gate 4 的 plant（M3/M6）是否与控制器内部模型（A0/B0、M4、M5）属于不同模型族。
7. **诚实边界**：报告是否把离线闭环仿真写成真实硬件控制；是否把离线求解耗时当作实时性。
8. **负结果保留**：M4（`A(c)+B0`）与 M5（`A(c)+B(χ)`）近乎并列时，报告是否如实呈现而非淡化。
9. **失败与异常**：主机内存导致的训练中断、rollout 语义缺陷（DEC-085）是否如实记录。
10. **未核实项**：`u_limit=±100`（Q3）是否被标为假设而非事实。

## 3. 可读证据与原始输出

| 文件 | 内容 | 备注 |
|---|---|---|
| `reports/modeling_comparison.md` | E-M1/E-M2 主表、逐 seed 明细、配对比较、跨轨迹方差、E-M3/E-M4/E-M5 | 由脚本从 ledger 生成，无手工数字 |
| `reports/control_comparison.md` | Gate 3/4/5 | 由脚本从 JSON 生成 |
| `reports/literature_baselines.md` | 基线元数据核实与改造点对照 | 未核实项显式标注 |
| `reports/data_audit.md` / `code_audit.md` / `go_no_go.md` | Gate 0 | C1–C5 前置条件 |
| `results/modeling/gate1_ledger.json` | 全部 trial（含失败）、best、final、test | 机器可读 |
| `results/modeling/gate2_diagnostics.json` | E-M3/E-M4/E-M5 | 增量落盘 |
| `results/control/control_*.json` | 控制场景逐指标与轨迹 | 含 `_traj` |
| `results/theory_diagnostics/freezing_diagnostics.json` | 冻结误差与决策比较 | — |
| `results/control/gate3_unit_tests.txt` / `gate3_hashes.txt` | 单测原始输出与文件哈希 | 复核者可直接打开核对 |
| `configs/*.yaml` | 数据/划分/建模协议/搜索空间/控制协议 | 冻结口径 |
| `.project-log/docs/framework-defects.md` | D-010..D-017 | 本轮框架缺陷 |

## 4. 主 Agent 代跑并粘贴的原始输出（复核者无 shell）

（本节在 Gate 2/4/5 完成后补齐：git 提交哈希、文件 sha256、关键命令与退出码。）

## 5. 已知限制（复核时请确认报告是否已披露，而非要求消除）

- `u_limit=±100` 为**假设**（旧部署配置，Q3 未由用户确认）。
- 无真实硬件实验；无急停/超时回退实测。
- 学习 plant 存在外推风险，报告需给出越界比例（`plant_state_out_of_train_range_frac`）。
- 超参搜索预算为 6 trial/模型（计划书建议 12），已在 `configs/search_spaces.yaml` 记录理由。
- M8/M9（可选基线）未实现；C3/C4（可选控制器）未实现，原因已登记。
