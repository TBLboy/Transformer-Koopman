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

1. **同一评估实现**：所有模型的窗口/起点/归一化/分位数是否都走 `models/protocol.py`，有无旁路；RMSE 公式在 Gate 1/4 脚本内联重算，需确认与 `protocol.py` 数值等价（复核已确认等价）。
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

## 4. 主 Agent 代跑并粘贴的原始输出（复核者无 shell，无法自行执行）

### 4.1 版本绑定

- git 提交：`096e2cc`（分支 `paper`，已推送 origin）
- 证据记录：`EV-GATE1-MODELS-002`、`EV-GATE2-DIAG-001`、`EV-GATE3-QP-002`、
  `EV-GATE4-CONTROL-001`、`EV-GATE5-FREEZE-001`（均绑定 `096e2cc`）
- 被 `evidence refresh` 标记 stale 的旧记录：`EV-GATE1-MODELS-001`、`EV-GATE3-QP-001`、
  `EV-TASK044-GATE0-002`（覆盖文件在记录之后变化；旧记录保留不删）

### 4.2 文件 sha256（工作区字节；证据绑定使用同一算法）

> 下表为**信息性**参考（本文件自身也会变动）；**权威绑定**以 `.project-log` 账本中
> 绑定最终提交 `b7a3e8d` 的 `EV-GATE1-MODELS-003` / `EV-GATE2-DIAG-002` /
> `EV-GATE3-QP-003` / `EV-GATE4-CONTROL-002` / `EV-GATE5-FREEZE-002` 的 `file_hashes` 为准。

| 文件（项目根相对路径） | sha256 |
|---|---|
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/models/protocol.py` | `ead56041e0dfa6bbe54a7f3bb3cb5e1bd71e5e80a4d229a7dd1c928382a3528e` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/models/library.py` | `ee71135dad75e414b547a9238954acdf4a5459c7c69f7334ef347f892bdf7bb0` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/controllers/ltv_mpc.py` | `39354803b93682178bef9b8a4d4b31aca804c3abd2618d841e9edb74b85e81fc` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/tests/test_ltv_qp.py` | `ddbbdd0184aa4d402dd82c289aed34bf9b6e7ae524adccb81803251219ddbba5` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/scripts/run_gate1.py` | `2df06cb82d5f2f2728992d1460e253e996d9394ad6050942327e6ceb018b73db` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/scripts/run_gate2.py` | `eaa32f32ce64af82eb9b7d429e68e091de477455178f0206a53afbc09830fd83` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/scripts/run_gate4.py` | `da85e0284595fc5c93f1f246c4267c2fd989e8f24c25f65bee9c28553c7cbeaa` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/scripts/run_gate5.py` | `376b6e6297d341d69282e28c4d20a29d9261b881092c231ff362799360b42664` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/scripts/report_modeling.py` | `a8c5e813fa61004a9a93133465fa36fa36e7b37a62340a4a091655eef8b316ce` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/scripts/report_control.py` | `f92f84a5ddc25024e6f118fdc30212091817145155dca67a16c5457e47498dc3` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/scripts/xtraj_variance.py` | `f75418f6c1b2bfd4cc08ae34d7947599207bfd94c14839ee05828755384a5dbb` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/configs/modeling_protocol.yaml` | `a7ea5ef77d2f4968882876a65283ce98658b8933fbcf2d15ee4f7a79b1f12c4b` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/configs/search_spaces.yaml` | `cd3fe31473d26a6491eb0d5dab22225d2a111260155b4dd30b9882d19fa45f5b` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/configs/control_protocol.yaml` | `557aa32da8a3fb6061d0a286e45f3db71ca691156e8a4e7a1ad5967bc76f78df` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/results/modeling/gate1_ledger.json` | `9d93eafd835b1c8e7ec5fc52a557a49611a4343212508b9d5dedd8f11c9f0e4c` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/results/modeling/gate2_diagnostics.json` | `a90b7263499d3ec3b304dab61a0e4301ae8170d8103520d19828dc61766b2f0f` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/results/modeling/xtraj_variance.json` | `f42a6d9df99f5bfa0675bf91b4e7564de7922756f6e6e8866c6953c48185a94d` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/results/control/gate3_unit_tests.txt` | `da832012b7fcf8cc553a5921a60fc9b38b1cbc194f2bd00a7671a410418e1393` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/results/control/gate3_hashes.txt` | `c44a70a9dfecd0e4d32e2392e1d4c8d8de5e15474556dac7b5bd797e37086ff3` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/results/control/control_test.json` | `527ef2d7ca3127187611d831de623e5b8490df1221d41499902360324d389dfc` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/results/control/control_val_search.json` | `7b385d83cbe1eb77bea7abcfc9c354de048d9b74df099f54c6c65aece808eb7a` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/results/theory_diagnostics/freezing_diagnostics.json` | `35c7405ce07256fea0441f20eeaccfc2aa265c189f8208bf906836f93bf838c2` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/reports/modeling_comparison.md` | `4cacaaa280bafb46fe8bd008dada708531379ce5b62d0ccc5ac6d48f084c9b0e` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/reports/control_comparison.md` | `3e5e4df956855941390c2f3e9395fcd7bcdbd477d51fc43749d0a17e5ffaa010` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/reports/final_research_report.md` | `dad64f0ca2bd381ba18197ac576981cf56190fb6f1d1d7afd8a7cf5d77342d57` |
| `Transformer-Koopman/杂项/新版本/Temporary_Experiments/reports/literature_baselines.md` | `01653669c1dc62faa5acb1afec88af517da3f55a5b1bd9978d1de09c5642aae5` |

### 4.3 关键命令与原始输出

**(a) Gate 3 单测（`python tests/test_ltv_qp.py`，原始输出见 `results/control/gate3_unit_tests.txt`）**

```text
T7 encoder is applied exactly once per rollout (latent propagation) PASS  encoder calls=1
T7b rollout step 0 equals the one-step prediction          PASS  
T7c rollout depends on the future control inputs           PASS  
T8 M5: Gate-5 helper matches the model rollout             PASS  max|err|=0.000e+00
T8 M4: Gate-5 helper matches the model rollout             PASS  max|err|=0.000e+00
T8 M_base: Gate-5 helper matches the model rollout         PASS  max|err|=0.000e+00
31/31 tests passed
```

**(b) Gate 4 模型复现一致性检查（`python scripts/run_gate4.py --split test` 原始输出）**

```text
﻿  M3 reproduction check: one-step 0.016351 vs ledger 0.016351 (|d|=0.00e+00)
M4 reproduction check: one-step 0.009565 vs ledger 0.009445 (|d|=1.20e-04)
M5 reproduction check: one-step 0.009795 vs ledger 0.009645 (|d|=1.50e-04)
M6 reproduction check: one-step 0.024095 vs ledger 0.041539 (|d|=1.74e-02)
```

**(c) Gate 5 理论核验（`results/theory_diagnostics/freezing_diagnostics.json`）**

```json
{
 "P1_zero_mismatch_gives_zero_error": true,
 "P1_detail": "delta=0 means U == bar U; the frozen and full trajectories must coincide (07 section 2: the driver is the input mismatch)",
 "P2_monotone_growth": true
}
```

```text
delta=0.00 |dU|=0.000  max||z_f-z_r||=0.000e+00  A_dev=0.000e+00  B_dev=0.000e+00  cost_gap=0.000e+00
delta=0.25 |dU|=1.716  max||z_f-z_r||=1.495e-01  A_dev=1.289e-02  B_dev=9.111e-04  cost_gap=5.402e-04
delta=0.50 |dU|=3.610  max||z_f-z_r||=3.481e-01  A_dev=2.681e-02  B_dev=1.931e-03  cost_gap=1.721e-03
delta=1.00 |dU|=7.001  max||z_f-z_r||=1.026e+00  A_dev=4.532e-02  B_dev=5.486e-03  cost_gap=9.519e-03
delta=2.00 |dU|=13.914  max||z_f-z_r||=1.223e+00  A_dev=4.895e-02  B_dev=5.722e-03  cost_gap=7.866e-03
decision: J_full(U_fr)=0.004962  J_full(U_nominal)=0.004133  J_full(U_local)=0.003337  gap=1.625e-03
```

**(d) 门禁当前判定（`vibe gate --task TASK-045`）**

```text
decision = blocked；唯一阻塞项 = high-risk task TASK-045 lacks an independent review
（证据失效问题已通过绑定最终字节的新证据解决）
```

### 4.4 需要复核者特别注意的三处偏离与限制

1. **Q3 / N3 / Q4（`u_limit = ±100`）未由用户确认**。Gate 0 的 `go_no_go.md` 原定「Gate 3/4 前确认」，实际未确认即运行了 Gate 3/4，处置方式为：
   - 所有位置标注为**假设**（`control_test.json` 的 `u_limit_physical_assumed`）；
   - 额外做 `data_range_u` 敏感性设置，把输入约束收到 train 经验范围以隔离 plant 外推影响；
   - 这是**已知偏离**，需要用户裁决，不得被复核判定为已满足 Gate 0 的 N3。
2. **M6（Transformer）种子 0 训练不可复现**（|Δone-step| = 1.74e-2，约 40%）。plant B 的结论只对本进程实际使用的 M6 成立；报告已改用实际 plant 保真度并给出复现检查表。
3. **Gate 0 证据重绑定**：`EV-TASK044-GATE0-002` 覆盖的 4 个文件在 DEC-084（用户确认 `x`/`u` 语义与数据来源）之后被更新，故已 stale；新增 `EV-TASK044-GATE0-003` 绑定当前字节。该更新方向是**把「待确认」变为「已确认」**，属增强而非削弱，但复核者应确认该判断（对照 `reports/data_audit.md` §3/§6/§8 与 `configs/data_manifest.yaml`）。

## 5. 已知限制（复核时请确认报告是否已披露，而非要求消除）

- `u_limit=±100` 为**假设**（旧部署配置，Q3 未由用户确认）。
- 无真实硬件实验；无急停/超时回退实测。
- 学习 plant 存在外推风险，报告需给出越界比例（`plant_state_out_of_train_range_frac`）。
- 超参搜索预算为 6 trial/模型（计划书建议 12），已在 `configs/search_spaces.yaml` 记录理由。
- M8/M9（可选基线）未实现；C3/C4（可选控制器）未实现，原因已登记。
