# Temporary_Experiments — 临时建模与控制实验

> 本目录是 `Temporary_Modeling_and_Control_Experiments_Plan.md` 的**执行落地目录**。
> 计划书来源：`C:/Users/12187/Downloads/Temporary_Modeling_and_Control_Experiments_Plan.md`（用户 2026-10-11 提供）。
> 项目目标：**GOAL-003**（`临时建模与控制实验：WP-M + WP-C`）。
> 当前任务：**TASK-045**（Gate 1–5：建模比较、有效性诊断、控制器单测、控制场景、冻结误差核验）。

## 位置理由

项目 `AGENTS.md` 规定「实验性的代码写在 `Transformer-Koopman\杂项`」；`.project-log` 记录的目录契约把
`杂项/新版本/` 定义为**验证路径（临时实验与前期结果）**。因此本实验放在
`杂项/新版本/Temporary_Experiments/`，而非计划书 §12 示例中的仓库根 `Temporary_Experiments/`。

## 边界（不可越线）

1. **不修改论文**：`论文/` 零改动；不写摘要 / Introduction / 实验章节 / 标题。
2. **不修改源数据**：`数据备份/` 只读。
3. **Gate 0 未通过前不启动大规模训练**（计划书 §1）。
4. **禁止**：预设优劣、修改原论文结果、把离线回放说成闭环控制、用测试集选超参数、
   把预测模型当作真实被控对象而声称完成真实控制验证（计划书 §0）。
5. 文献与数据来源未核实项一律标「待确认」，不得推断为事实。

## 目录

```
Temporary_Experiments/
├── README.md                  本文件
├── configs/                   data_manifest.yaml / split_manifest.yaml / modeling_protocol.yaml
│                              / search_spaces.yaml / control_protocol.yaml
├── data_processing/           数据准备脚本（本实验直接读 数据备份/软体平台数据/处理后的数据）
├── models/
│   ├── protocol.py            **唯一**评估实现：窗口 / 冻结评估起点 / 指标（自检 PASS）
│   └── library.py             M0 DMDc / M1 EDMDc / M2 EDMD-DL-control / M3 GRU-LSTM
│                              / M4 A(c)+B0 / M5 A(c)+B(x) / M6 Controlled Transformer
│                              （另含 M7 A0+B(x) 与 M_base A0+B0，供 E-M3 消融）
├── controllers/
│   └── ltv_mpc.py             冻结调度 LTV-MPC（Theory_Package/06 的 F/G/H/f）+ OSQP + cvxpy 参考
├── scripts/                   审计与实验入口
│   ├── audit_data.py          Gate 0：原始数据审计
│   ├── audit_split_stats.py   Gate 0：分划统计 + train-only 归一化常数
│   ├── audit_legacy_model.py  Gate 0：旧模型端到端复现检查
│   ├── run_gate1.py           Gate 1：pilot -> formal -> multi-seed -> frozen test
│   ├── run_gate2.py           Gate 2：E-M3 配对消融 / E-M4 容量匹配 / E-M5 调度诊断
│   ├── run_gate4.py           Gate 4：离线闭环控制场景（plant = M3 / M6）
│   ├── run_gate5.py           Gate 5：冻结调度误差交叉核验
│   ├── report_modeling.py     从 ledger 生成 reports/modeling_comparison.md + figures
│   └── report_control.py      从结果 JSON 生成 reports/control_comparison.md
├── tests/
│   └── test_ltv_qp.py         Gate 3：28 项冻结 LTV-QP 数值单测（必须常绿）
├── checkpoints/               本实验训练产物（<M>_seed<S>.pt）
├── results/
│   ├── audit/                 Gate 0 审计原始输出
│   ├── modeling/              gate1_ledger.json（全部 trial、含失败）、gate1_run.log、gate2_diagnostics.json
│   ├── control/               Gate 3 原始输出 + control_*.json（Gate 4）
│   └── theory_diagnostics/    freezing_diagnostics.json（Gate 5）
├── figures/                   自动生成图表（em2_horizon_rmse.png、em1_summary.png）
└── reports/                   人读报告
    ├── data_audit.md          ✅ Gate 0
    ├── code_audit.md          ✅ Gate 0
    ├── go_no_go.md            ✅ Gate 0
    ├── literature_baselines.md  ✅ 元数据核实 + 改造点对照
    ├── modeling_comparison.md   E-M1/E-M2（由脚本生成）
    ├── control_comparison.md    Gate 3/4/5（由脚本生成）
    └── final_research_report.md 待写
```

## 复现命令（按顺序）

```powershell
$py = "D:\conda\envs\edmddl2\python.exe"
cd D:\Project\Transformer-Koopman\Transformer-Koopman\杂项\新版本\Temporary_Experiments

# 协议自检 + Gate 3 单测（必须全绿）
& $py models\protocol.py
& $py -u tests\test_ltv_qp.py

# Gate 1：逐模型独立进程（主机内存 16 GB，合并跑会 OOM）
foreach ($m in "M0","M1","M2","M3","M4","M5","M6") {
  & $py scripts\run_gate1.py --stage formal --trials 6 --epochs 50 --models $m
  & $py scripts\run_gate1.py --stage final  --seeds 3  --epochs 50 --models $m
  & $py scripts\run_gate1.py --stage test   --seeds 3  --epochs 50 --models $m
}

# Gate 2 / 4 / 5
& $py scripts\run_gate2.py --seeds 3
& $py scripts\run_gate4.py --split val --search
& $py scripts\run_gate4.py --split test
& $py scripts\run_gate5.py

# 报告
& $py scripts\report_modeling.py
& $py scripts\report_control.py
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

| Gate | 内容 | 状态 |
|---|---|---|
| 0 | 数据/代码审计 | ✅ 完成（判定 conditional go；独立复核四轮：REV-TASK044-001 conditional → 002 go → 003 conditional → 004 go） |
| 1 | 基线预测运行 M0–M6 | 进行中：模型库与驱动完成；**因 rollout 语义修正（DEC-085）全部重跑**。M0–M3 已完成 test；M4–M6 训练中 |
| 2 | 新模型有效性诊断 | 脚本就绪（`run_gate2.py`），待 Gate 1 选定配置 |
| 3 | 控制器单元测试 | ✅ **完成**：28/28 通过（`tests/test_ltv_qp.py`，证据 EV-GATE3-QP-001）。单测抓出 2 个真实缺陷（代价常数项、rollout 重新编码） |
| 4 | 控制场景评估 | 脚本就绪（`run_gate4.py`），待 Gate 1 模型 |
| 5 | 理论—实验交叉核验 | 脚本就绪（`run_gate5.py`），待 Gate 1 模型 |

### 单测暴露并已修正的两个真实缺陷（重要）

1. **目标函数缺常数项** → `UᵀMU + 2fᵀU` 与直接求和不等。已修正。
2. **rollout 每步重新编码**（与 `Theory_Package/01` §4.3、`06` §2 的 latent 递归传播冲突）→ 已按理论修正（DEC-085），
   并新增单测 T7 断言「一次 rollout 内 encoder 只调用 1 次」防止回归。**该修正使首轮 Gate 1 训练全部作废。**

### Gate 1 重跑进度（本次）

| 模型 | 冻结 test（归一化单位，mean over 3 seeds） |
|---|---|
| M0 DMDc | one-step 0.2992 / roll25 0.2655 |
| M1 EDMDc | one-step — / roll25 0.2992 |
| M2 EDMD-DL-control | one-step 0.0433 / roll25 0.1546 |
| M3 GRU | one-step 0.0178 / roll25 0.0377 |
| M4 / M5 / M6 | 训练中 |

> 上表**只是进度**，不是结论；完整主表见 `reports/modeling_comparison.md`（由脚本从 ledger 生成）。
