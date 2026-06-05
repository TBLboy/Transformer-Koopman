# Current Session

## Last Updated

- 2026-06-05 17:00 Local Time

## Current Objective

- **已完成**: 双平台 4 方法全部训练 + 消融实验 + 控制器部署 + 轨迹跟踪实验
- **当前**: 消融实验 bug 修复 + 评估结果整理，准备进入论文撰写阶段

## Current Business Logic Position

- Main path: Data -> Dataset -> Train(EDMD) -> Eval -> Deploy -> Control
- **Current node: N7 (AblationResults) — 评估完成，结果表已整理**
- N6 (RealTimeControl) — 控制器封装完成，等待上位机实物验证
- Active branch: **main**（主项目，所有训练/消融已回到可复现状态）

## Completed This Session (cumulative)

### 训练完成（2026-05-27 ~ 2026-06-02）

| 方法 | Platform1 RMSE | Platform2 RMSE |
|------|---------------|---------------|
| PatchTST-Koopman | **0.157** (最优) | **0.474** (最优, latent_dim=10) |
| MLP-Koopman | 0.420 | 1.380 / 1.431 |
| LSTM-Koopman | 0.410 | 1.689 / 1.796 |
| Traditional EDMD | 0.903 | 1.332 |

### 消融实验完成（2026-06-04 ~ 06-05）

- Platform1: 19 种变体全部跑完，baseline RMSE=0.4116
- Platform2: 18 种变体全部跑完，baseline RMSE=0.7942
- 结果路径: `results/ablation/platform*/ablation_platform*/` 下时间戳目录

### Bug 修复（2026-06-05）

本次修复了消融实验 pipeline 的 4 类 bug：

1. **ImportError 修复** — `test_ablation.py:18`
   - `from scripts.ablation.train_ablation import ...` → `from train_ablation import ...`
   - 原因：subprocess 运行时 Python 不识别 `scripts.ablation` 为 package（无 `__init__.py`）

2. **EDMD 数值稳定性修复** — `edmd_trainer.py:461-474`
   - `np.linalg.inv` → `np.linalg.solve`（更稳定的线性求解）
   - 新增 NaN/Inf 检测，含 Z 统计信息的错误提示

3. **5 个 encoder 文件缺失 divisibility check** — 全部添加 `history_length % patch_length != 0` 校验：
   - `src/patchtst_koopman/models/patchtst_encoder.py`
   - `src/patchtst_koopman/ablation/encoders/no_attention.py`
   - `src/patchtst_koopman/ablation/encoders/no_positional.py`
   - `src/patchtst_koopman/ablation/encoders/readout.py`
   - `src/patchtst_koopman/ablation/encoders/pure_feature.py`

4. **Platform1 latent_dim=256 NaN 问题**（已知，非 bug）
   - 256-dim 潜在空间导致数值溢出，属超参数不稳定，非代码错误

### 消融评估结果（2026-06-05 最新评估）

- 使用 `test_ablation.py` 在测试集上 rollout 评估
- 平台1: 19 变体 PASSED，baseline rollout RMSE=0.4116
- 平台2: 18 变体 PASSED，baseline rollout RMSE=0.7942
- 关键发现已在 ablation 结果表中标注

### 控制器部署（2026-06-05）

- 4 个基线控制器（Transformer/MLP/LSTM/EDMD）导出到 FlexibleArmControl34
- `scripts/verify_koopman_controllers.py` 校验通过
- Experiment 3 轨迹跟踪（正弦/方/圆/星）已完成

## Problems And Resolutions

### 已修复
- EDMD lifter `C.shape[1]` → `C.shape[0]` 维度错误
- 消融代码路径 glob 错误（`generate_report.py`, `plot_ablation_results.py`）
- `test_ablation.py` 默认路径和 `strict=True` 问题
- **ImportError: `ModuleNotFoundError: No module named 'scripts.ablation'`** — 改为 bare import
- **EDMD `np.linalg.inv` 数值不稳定** — 改为 `np.linalg.solve` + NaN/Inf 检测
- **5 个 encoder 缺失 divisibility check** — 全部补上

### 已确认
- ~~PatchTST End-to-End 训练未实现~~ **❌ 已确认实际可用** — `edmd_trainer.py` 的 `_train_end_to_end()` 已完整实现

## Current State

- 所有训练脚本可重复跑出当前结果
- `configs/platform1.yaml` / `platform2.yaml` 为最终一致版本
- Git HEAD: `693efab` 恢复之后的版本，测试过没问题
- 下一步方向由用户决定

## Next Steps

1. 论文配图生成（`figures/ablation/generate_ablation_materials.py` 已验证可用）
2. 上位机实物测试控制器
3. 论文撰写
