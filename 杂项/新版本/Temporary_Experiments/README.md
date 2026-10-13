# Temporary_Experiments — 临时建模与控制实验

> 本目录是 `Temporary_Modeling_and_Control_Experiments_Plan.md` 的**执行落地目录**。
> 计划书来源：`C:/Users/12187/Downloads/Temporary_Modeling_and_Control_Experiments_Plan.md`（用户 2026-10-11 提供）。
> 项目目标：**GOAL-003**（软体平台，TASK-045，已完成）与 **GOAL-004**（机械臂，TASK-046）。
> 当前任务：**TASK-046**（在 3 关节机械臂数据上重跑同一套实验）。

## 位置理由

项目 `AGENTS.md` 规定「实验性的代码写在 `Transformer-Koopman\杂项`」；`.project-log` 记录的目录契约把
`杂项/新版本/` 定义为**验证路径（临时实验与前期结果）**。因此本实验放在
`杂项/新版本/Temporary_Experiments/`，而非计划书 §12 示例中的仓库根 `Temporary_Experiments/`。

## 边界（不可越线）

1. **不修改论文**：`论文/` 零改动；不写摘要 / Introduction / 实验章节 / 标题。
2. **不修改源数据**：`数据备份/` 只读。
3. **禁止**：预设优劣、修改原论文结果、把离线回放说成闭环控制、用测试集选超参数、
   把预测模型当作真实被控对象而声称完成真实控制验证（计划书 §0）。
4. 文献与数据来源未核实项一律标「待确认」，不得推断为事实。
5. 机械臂的**力矩限幅是假设**（train 经验范围 × 1.05，DEC-086），不是执行器额定值。

## 设备层（device layer）

同一套方法与协议要跑在两个设备上，且**软体平台的数值必须逐位不变**：

```
models/device.py    设备规格：n_state / n_ctrl / P / patch / latent_dim / 时域 / 起点数
                    / 归一化常量（train-only，冻结）/ 数据目录 / 控制盒约束 / 输出目录
```

选择顺序（高 → 低）：`--device NAME` / `-d NAME`（脚本首行 `device.bootstrap_from_argv()`
在 `protocol`、`library` 冻结常量**之前**解析）→ 环境变量 `TK_DEVICE` → 默认 `soft_platform`。

| 设备 | n_state | n_ctrl | dt | 轨迹 | 划分 | d | 时域（步） | MPC N |
|---|---|---|---|---|---|---|---|---|
| `soft_platform` | 2 | 2 | 0.2 s | 100×300 | 70/20/10 | 10 | 5 / 25 / 100 | 10 |
| `arm_3link` | 6 | 3 | 0.004 s | 20×~4977 | 15/4/1 | 14 | 5 / 25 / 100 / 500 / 1000 | 50 |

**隐维规则**：`z = [x_k ; h_k]` 且 `n_psi = 8`（软体平台 d = 2 + 8 = 10），机械臂沿用同一规则 → d = 6 + 8 = 14。
**时域**：协议步数口径保留（方法同一性），另加物理时间口径 500/1000 步 = 2 s / 4 s
（250 Hz 下 H=25 只有 0.1 s，与软体平台的 5 s 不可比）。
**输出布局**：软体平台保持原路径（证据连续性）；机械臂落在 `results/arm/`、`checkpoints/arm/`、
`reports/arm_*.md`、`figures/arm_*.png`。

### 泛化回归验证（DEC-087 D9）

`scripts/regression_ab_soft.py`：用**同一批 checkpoint**分别由「改造前代码」与「改造后代码」评估，
逐项对比 → 7 个模型 × 151 项指标全部 0 差异（`results/modeling/regression_ab_soft.json`）。

> 注意：把 checkpoint 与 ledger 直接比**不是**回归测试——ledger 的 test 数字来自进程内重新训练，
> 而神经模型在本机训练不可复现（AMP + TF32 + cuDNN benchmark）。只有同 checkpoint 的 A/B 能隔离改造影响。

## 目录

```
Temporary_Experiments/
├── README.md                  本文件
├── configs/                   data_manifest / split_manifest / modeling_protocol / search_spaces
│                              / control_protocol（软体平台）
│                              / arm_protocol.yaml（机械臂设备冻结口径）
├── models/
│   ├── device.py              **设备规格层**（唯一设备事实源）
│   ├── protocol.py            **唯一**评估实现：窗口 / 冻结评估起点 / 指标（自检 PASS）
│   └── library.py             M0 DMDc / M1 EDMDc / M2 EDMD-DL-control / M3 GRU-LSTM
│                              / M4 A(c)+B0 / M5 A(c)+B(x) / M6 Controlled Transformer
│                              （另含 M7 A0+B(x) 与 M_base A0+B0，供 E-M3 消融）
├── controllers/
│   └── ltv_mpc.py             冻结调度 LTV-MPC（Theory_Package/06 的 F/G/H/f）+ OSQP + cvxpy 参考
├── scripts/                   审计与实验入口
│   ├── audit_data.py / audit_split_stats.py / audit_legacy_model.py   Gate 0（软体平台）
│   ├── run_gate1.py           Gate 1：pilot -> formal -> multi-seed -> frozen test
│   ├── run_gate2.py           Gate 2：E-M3 配对消融 / E-M4 容量匹配 / E-M5 调度诊断
│   ├── run_gate4.py           Gate 4：离线闭环控制场景（plant = M3 / M6）
│   ├── run_gate5.py           Gate 5：冻结调度误差交叉核验
│   ├── eval_ckpt_soft.py      用保存的 checkpoint 复算全部指标（供 A/B 回归）
│   ├── regression_soft.py     checkpoint vs ledger（诊断训练不可复现，**不是**回归测试）
│   ├── regression_ab_soft.py  **回归测试**：改造前 vs 改造后，同 checkpoint
│   ├── report_modeling.py / report_control.py   软体平台报告生成
│   └── report_arm.py          机械臂报告生成（建模 / 控制 / 跨设备对照）
├── tests/
│   └── test_ltv_qp.py         Gate 3：31 项冻结 LTV-QP 数值单测（两设备均须常绿）
├── checkpoints/               软体平台训练产物；checkpoints/arm/ 机械臂训练产物
├── results/
│   ├── audit/                 Gate 0 审计原始输出
│   ├── modeling/              gate1_ledger.json / gate2_diagnostics.json / xtraj_variance.json
│   │                          / regression_ab_soft.json / eval_soft_{old,new}code.json
│   ├── control/               Gate 3 原始输出 + control_*.json（Gate 4）
│   ├── theory_diagnostics/    freezing_diagnostics.json（Gate 5）
│   └── arm/                   机械臂：modeling/ control/ theory_diagnostics/
├── figures/                   自动生成图表
└── reports/                   人读报告（机械臂为 arm_* 前缀）
```

## 复现命令

```powershell
$py = "D:\conda\envs\edmddl2\python.exe"
cd D:\Project\Transformer-Koopman\Transformer-Koopman\杂项\新版本\Temporary_Experiments

# 协议自检 + Gate 3 单测（两设备都必须全绿）
& $py models\protocol.py
& $py -u tests\test_ltv_qp.py
& $py -u tests\test_ltv_qp.py --device arm_3link

# 回归验证（软体平台数值必须逐位不变）
& $py -u scripts\regression_ab_soft.py

# 软体平台 Gate 1（逐模型独立进程：主机内存 16 GB，合并跑会 OOM）
foreach ($m in "M0","M1","M2","M3","M4","M5","M6") {
  & $py scripts\run_gate1.py --stage formal --trials 6 --epochs 50 --models $m
  & $py scripts\run_gate1.py --stage final  --seeds 3  --epochs 50 --models $m
  & $py scripts\run_gate1.py --stage test   --seeds 3  --epochs 50 --models $m
}
& $py scripts\run_gate2.py --seeds 3
& $py scripts\run_gate4.py --split val --search
& $py scripts\run_gate4.py --split test
& $py scripts\run_gate5.py
& $py scripts\report_modeling.py
& $py scripts\report_control.py

# 机械臂 Gate 1-5（同一脚本，仅加 --device arm_3link）
foreach ($m in "M0","M1","M2","M3","M4","M5","M6") {
  & $py scripts\run_gate1.py --device arm_3link --stage formal --trials 6 --epochs 50 --models $m
  & $py scripts\run_gate1.py --device arm_3link --stage final  --seeds 3  --epochs 50 --models $m
  & $py scripts\run_gate1.py --device arm_3link --stage test   --seeds 3  --epochs 50 --models $m
}
& $py scripts\run_gate2.py --device arm_3link --seeds 3
& $py scripts\run_gate4.py --device arm_3link --split val --search
& $py scripts\run_gate4.py --device arm_3link --split test
& $py scripts\run_gate5.py --device arm_3link
& $py scripts\report_arm.py --device arm_3link
```

**已知环境陷阱**：主机 RAM 只有 16 GB（训练时可用约 3 GB）。内存耗尽时报错表现为
`CUDA error: out of memory`，而 GPU 实际只占用几十 MiB——**不要**误判为显存不足。
规避手段：逐模型独立进程 + `gc.collect()` / `torch.cuda.empty_cache()` + batch 128。

## 运行环境

```powershell
# 项目解释器（torch 2.6.0+cu124，CUDA 可用；numpy/scipy/pandas/matplotlib/cvxpy+osqp 齐备）
$py = "D:\conda\envs\edmddl2\python.exe"

# Vibe CLI（记账）
$vibe = "D:\conda\envs\vibe-coding\python.exe"
& $vibe "C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py" --root D:\Project\Transformer-Koopman status
```

已探明算力：**CUDA 可用（1 卡）**；无 optuna、无 h5py、无 `control` 包（需另行安装或替代）。

## Gate 状态

### 软体平台（GOAL-003 / TASK-045）

| Gate | 内容 | 状态 |
|---|---|---|
| 0 | 数据/代码审计 | ✅ conditional go；独立复核四轮（REV-TASK044-001..004） |
| 1 | 基线预测运行 M0–M6 | ✅ 完成（6 trial → 3 seed → frozen test） |
| 2 | 新模型有效性诊断 | ✅ 完成（E-M3/E-M4/E-M5） |
| 3 | 控制器单元测试 | ✅ 31/31 通过 |
| 4 | 控制场景评估（离线闭环） | ✅ 完成（plant M3/M6，控制器 C0/C1/C2 + 敏感性） |
| 5 | 理论—实验交叉核验 | ✅ 完成（P1/P2 成立） |

收口：`REV-TASK045-001` verdict = **go**；`vibe gate --task TASK-045` = allowed。
核心结论：A(c) 调度收益大；**B(χ) 无可测量收益**；M4/M5 选中相同配置；ρ(A) > 1；
闭环结果大部分是 plant 外推且排序对权重不稳健；M6 种子 0 训练不可复现。

### 机械臂（GOAL-004 / TASK-046）

| Gate | 内容 | 状态 |
|---|---|---|
| 0 | 数据审计 | ✅ `reports/data_audit_arm.md`（语义独立验证、逐元素一致、15/4/1 划分可追溯） |
| 1 | 基线预测运行 M0–M6 | 见 `results/arm/modeling/gate1_ledger.json` |
| 2 | 新模型有效性诊断 | 见 `results/arm/modeling/gate2_diagnostics.json` |
| 3 | 控制器单元测试（n=6,m=3） | 见 `results/arm/control/gate3_unit_tests_arm.txt` |
| 4 | 控制场景评估（离线闭环） | 见 `results/arm/control/control_*.json` |
| 5 | 理论—实验交叉核验 | 见 `results/arm/theory_diagnostics/freezing_diagnostics.json` |

### 单测暴露并已修正的两个真实缺陷（软体平台首轮）

1. **目标函数缺常数项** → `UᵀMU + 2fᵀU` 与直接求和不等。已修正。
2. **rollout 每步重新编码**（与 `Theory_Package/01` §4.3、`06` §2 的 latent 递归传播冲突）→ 已按理论修正（DEC-085），
   并新增单测 T7 断言「一次 rollout 内 encoder 只调用 1 次」防止回归。**该修正使首轮 Gate 1 训练全部作废。**

> 所有数值表由脚本从 `results/**` 自动生成，不手工填写；进度性摘要不写入本文件，避免与生成视图冲突。
