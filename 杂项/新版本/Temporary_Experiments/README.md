# Temporary_Experiments — 临时建模与控制实验

> 本目录是 `Temporary_Modeling_and_Control_Experiments_Plan.md` 的**执行落地目录**。
> 计划书来源：`C:/Users/12187/Downloads/Temporary_Modeling_and_Control_Experiments_Plan.md`（用户 2026-10-11 提供）。
> 项目目标：**GOAL-003**（`临时建模与控制实验：WP-M + WP-C`）。
> 当前任务：**TASK-044**（Gate 0：数据与代码审计）。

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
├── data_processing/           数据准备脚本（后续）
├── models/                    M0-M9 各模型实现（后续）
├── controllers/               LTI-MPC / Scheduled LTV-MPC / NMPC（后续）
├── scripts/                   审计与实验入口
│   ├── audit_data.py          Gate 0：原始数据审计
│   ├── audit_split_stats.py   Gate 0：分划统计 + train-only 归一化常数
│   └── audit_legacy_model.py  Gate 0：旧模型端到端复现检查
├── tests/                     单元测试（后续）
├── checkpoints/               本实验训练产物（后续）
├── results/
│   ├── audit/                 Gate 0 审计原始输出
│   ├── modeling/              E-M1..E-M7（后续）
│   ├── control/               Gate 4 控制场景（后续）
│   └── theory_diagnostics/    Gate 5 冻结调度诊断（后续）
├── figures/                   自动生成图表（后续）
└── reports/                   人读报告
    ├── data_audit.md          ✅ Gate 0
    ├── code_audit.md          ✅ Gate 0
    ├── go_no_go.md            ✅ Gate 0
    ├── literature_baselines.md
    ├── modeling_comparison.md
    ├── control_comparison.md
    └── final_research_report.md
```

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
| 1 | 基线预测运行 M0–M6 | 进行中：`configs/modeling_protocol.yaml` 已冻结（C5 闭合、C3 指标口径已定）；C1/C2/C4 见 `reports/go_no_go.md` |
| 2 | 新模型有效性诊断 | 未开始 |
| 3 | 控制器单元测试 | 未开始 |
| 4 | 控制场景评估 | 未开始 |
| 5 | 理论—实验交叉核验 | 未开始 |
