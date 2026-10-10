# 杂项 — 研究材料与代码归档

本目录集中保存 Transformer-Koopman 项目在研究过程中产生的**研究代码、模型检查点、实验结果与脚本**，防止它们仅存在于系统临时文件夹而丢失。

## 来源与完整性
- **来源**：`C:\Users\12187\AppData\Local\Temp\opencode\`（OpenCode 临时工作目录）
- **归档时间**：2026-10-06
- **方式**：**复制**（临时目录中的原始文件未删除，可确认无误后另行清理）
- **校验**：逐文件 sha256 比对，0 处不匹配

## 目录结构
| 目录 | 内容 | 文件数 |
|---|---|---|
| `研究代码/` | 研究脚本：gate 系列（新路线模型/实验/诊断）、路线探索（`V_`/`D_`/`Q_`/`N_`/`spike_`）、控制与评估、绘图/渲染 | 72 |
| `流程脚本/` | 项目日志与 vibe CLI 驱动脚本（`record_`/`dump_`/`probe_`/`check_`/`fix_`/`verify_` 等） | 248 |
| `模型检查点/` | 训练权重（`gate_states/` 全部 17 个 + `plant_dnn.pt`） | 18 |
| `实验结果/` | 实验/诊断结果 JSON（`gate*`/`N_`/`D_`/`Q_`/`V_`/`spike_`/`test*`/`p1_*` 等） | 51 |
| `记录载荷/` | project-log 记录用的 payload/covers JSON 与 `vibe-status` 快照 | 185 |
| `图表/` | 论文插图/裁剪（`eq49_crop.png`、`p08_300.png`） | 2 |
| `说明文档/` | 交付说明头、提交信息、PDF 文本抽取等 | 7 |

## 关键材料（新路线实现与证据）
- **新路线模型与训练**：
  - `研究代码/gate_context_koopman.py`（`CtxKoopman`，A/B/AB 调制对照）
  - `研究代码/gate14_stabilize.py`（`BudgetedCtxKoopman`：`A(c)=A0+U·diag(δ_A·π⊙tanh(g(c)))·Vᵀ`，r=2；开环 scheduled 传播训练 + 谱半径惩罚）
- **理论诊断（论文表 I / 图 3 的单一事实源）**：
  - `研究代码/gate16_diag_final.py` → `实验结果/gate16_diag_final.json`（stride-1）
  - `研究代码/gate16_diag_fix.py` → `实验结果/gate16_diag_fix.json`（stride-4，图 3 用）
- **匹配 oracle 控制实验 / RTI 运行时**：
  - `研究代码/gate16_matched_oracle.py` → `实验结果/gate16_matched_oracle_N5.json`、`_N8.json`
  - `研究代码/gate14d_rti.py` → `实验结果/gate14d_result*.json`
- **冻结部署预测器权重**：`模型检查点/A_stab_openloop_lam0.0_rho0.99.pt`（gate16 诊断所用；r=2, P=8, d=10）
- **论文改写脚本**：`研究代码/rewrite_ivb.py`（把 §IV-B/Algorithm 1/Fig.2 重写为实际实现）

## 未纳入本目录（仍在临时目录）
- `tectonic/`、`tectonic.zip`：LaTeX 编译引擎（工具，可重新获取）。
- `milk-milk-go-before-filter.bundle`：与本项目无关的 `milk` 仓库 git bundle（120 MB）。
- `pdf_v2…v5`、`pdf_pages`、`pdf_r4`：论文 PDF 渲染图（可由 `Main.tex` 重新生成）。
- `vr3/`、`__pycache__/`、`installed-backup*/`、`gate-git-*/`：vibe 框架副本与测试产物。

> ⚠️ `模型检查点/` 与 `研究代码/` 中的脚本是**新路线（A(c) + rollout-aware scheduled 训练）的唯一实现**——迁移进仓库的 `训练代码/` 仅含旧固定-A 路线。请勿删除。
