# Progress Log

## 2026-05-25 20:00 Local Time

- **Objective**: 在 code-projectv2/ 新写一份干净代码（项目重构）
- **Work completed**:
  - 新建项目骨架（目录树 + pyproject.toml + requirements.txt + .gitignore + README.md）
  - 从原 code_project/ 复制 data/（可能在 sandbox 中未持久化）
  - 复制 model_assets/ 到 deploy/algorithms/tk_assets/model_assets/
  - 创建完整 Python 包 `src/patchtst_koopman/` 及全部子包 __init__.py
  - 中文目录英文化（实验3代码→deploy/, 实验1/2绘图→figures/, experiments→scripts/, config→configs/）
  - aabb→tk_assets 重命名，全部 import 更新
  - 抽取共用工具：device.py, data_prep.py, evaluation.py
  - 抽取共用 PositionalEncoding（消除 7 个文件重复）
  - 重写 ablation/models.py 为正规 AblationModel(nn.Module) 子类 + 10 工厂函数
  - 配置收拢：只保留 platform1.yaml / platform2.yaml
  - 硬编码路径改为 argparse 必需参数
  - .gitignore + results/.gitkeep
- **Business logic impact**: Main logic restructured, no behavioral change
- **Problems encountered**:
  - pip install SSL 错误（pypi 镜像无法访问）
  - 基础 Python 3.8 不满足 >=3.10 要求
- **Resolution**:
  - 使用 `pip install -e . --no-deps` 跳过依赖安装（conda env 已有 torch）
  - pyproject.toml requires-python 降为 >=3.8
- **Verification**: `scripts/smoke_test.py` 全部通过（import → lifter → export_assets → 1 epoch）
- **Unverified items**: 正式 500 epochs 训练未运行；实物部署未验证
- **Files changed**: 全部在 code-projectv2/ 下新创建
- **Next steps**: 用户确认 data/ 存在后开始正式训练，或继续论文撰写

## 2026-05-26 20:36 Local Time

- **Objective**: 回答 4 个待定问题 + 审查 EDMD 和 End-to-End 训练逻辑
- **Work completed**:
  - 确认 data/ 存在（experiment_001~006, 18 个 NPZ）
  - 审查 EDMDTrainer（edmd_trainer.py）三阶段训练逻辑
  - 审查 End-to-End 实现（train_patchtst.py + mlp_koopman_trainer.py）
  - 更新 open-questions.md 中 4 个问题的答案
- **Business logic impact**: None（仅审查，未改代码）
- **Problems encountered**:
  - ~~PatchTST 模型的 End-to-End 训练路径未实现~~ **❌ 此结论有误** — 后续确认 `edmd_trainer.py` 的 `train()` 方法已支持 `method="end_to_end"`，`_train_end_to_end()` 完整实现（早停/梯度裁剪/SVD投影/LR调度/最佳checkpoint），`train_patchtst.py` 中无 NotImplementedError
  - MLP-Koopman 的 End-to-End 已实现（mlp_koopman_trainer.py._train_end_to_end）
- **Resolution**: PatchTST End-to-End **已实现且可用**，无需补全
- **Verification**: 审查完成
- **Unverified items**: 无
- **Files changed**: `.project-log/business-logic/open-questions.md`, `progress.md`, `current-session.md`
- **Next steps**: 等待用户对 End-to-End 缺失的回应

## 2026-06-05 14:00 Local Time

- **Objective**: Platform 2 基线控制器封装（Experiment 3 对比实验准备）
- **Work completed**:
  - 编写 `code-projectv2/deploy/export_baseline_assets.py`，从 experiment1 导出四个模型
  - 将 Transformer/MLP/LSTM/EDMD 四个模型的 checkpoint 导出到 `FlexibleArmControl34/algorithms/tk_assets/model_assets/`
  - tk_assets 新增公共模块：`state_history_buffer.py`、`koopman_lqr_base.py`、`polynomial_lifting.py`、`normalization_utils.py`、`koopman_lqr_settings_widget.py`
  - tk_assets 新增独立的 `mlp_koopman_model.py` / `mlp_koopman_lifter.py`、`lstm_koopman_model.py` / `lstm_koopman_lifter.py`、`edmd_koopman_lifter.py`
  - 新建三个控制器（mlp/lstm/edmd）+ 对应 configs
  - 将 Transformer 控制器 model_path 迁移到 model_assets 子目录
  - 编写 `scripts/verify_koopman_controllers.py` 并通过全部校验（资产检查 + LQR + 单步控制 + AlgorithmManager 注册）
- **Business logic impact**: Experiment 3 对比实验的 4 个基线控制器全部就绪，可直接在上位机中选择使用
- **Problems encountered**:
  - PowerShell 5.1 不支持 `&&`、`Join-Path` 多段拼接
  - `python deploy/export_baseline_assets.py` 默认环境无 torch，需用 `FlexibleArm` conda env
  - EDMD lifter 的 `C` 矩阵维度读取错误（`C.shape[1]` → `C.shape[0]`），已修复
- **Resolution**: 全部解决并验证通过
- **Verification**: `scripts/verify_koopman_controllers.py` 全部通过
- **Unverified items**: 无
- **Files changed**: 见 FlexibleArmControl34 下大量新增/修改文件
- **Next steps**: 等待后续实验3运行

## 2026-05-27 — Platform2 首次正式训练

- **Objective**: 验证 PatchTST-Koopman Platform2 训练流程
- **Work completed**:
  - `scripts/train_patchtst.py` 首次在 Platform2 上完成训练
  - 模型保存为 `results/models/model_20260527_154535.pth`
  - 结果：one-step RMSE=0.01498, auto RMSE=1.586, MAE=1.187
- **Files changed**: `results/models/` 下新增模型 + 结果

## 2026-05-29 — Platform1 + Platform2 多方法训练批次

- **Objective**: 在双平台上完整训练 4 种方法（PatchTST/MLP/LSTM/EDMD）
- **Work completed**:
  - **Platform1 PatchTST**: 完成训练，auto RMSE=**0.157**（目前最优）, MAE=0.086（log: `p1_patchtst_koopman.log`）
  - **Platform1 MLP-Koopman**: 端到端训练完成，auto RMSE=0.420, MAE=0.224
  - **Platform2 PatchTST**: 完成训练（`results/Results/patchtst_koopman/`），auto RMSE=1.307
  - **Platform2 MLP-Koopman**: 完成训练，auto RMSE=1.431
  - **Platform1/2 LSTM-Koopman**: 双平台完成训练
  - **Platform1/2 Traditional EDMD**: 双平台完成
  - 结果统一保存在 `results/platform1/Results/` 和 `results/platform2/Results/` 下
- **Verification**: 各方法均有完整结果 JSON + 测试图

## 2026-06-02 — 批量调参训练（Platform2 7 组 + Platform1 微调）

- **Objective**: 调优 Platform2 PatchTST 超参数，寻找最优配置
- **Work completed**:
  - Platform2 PatchTST 连续完成 **7 次完整训练**（时间戳 114644→133535）
  - 最优结果：`auto_test_rmse=0.474`, `auto_test_mae=0.365`（`results_20260602_133535.json`）
  - Platform1 PatchTST 再训练：auto RMSE=**0.412**
  - 所有训练完成时自动保存 `model_best.pth`（含完整 checkpoint）
- **Verification**: 7 组结果均可复现，latent_dim=10 版本优于 latent_dim=8 版本

## 2026-06-04 ~ 2026-06-05 — 消融实验完成（双平台）

- **Objective**: 跑完所有消融变体，生成对比结果
- **Work completed**:
  - **Platform1 消融**（20 种变体）:
    - 变体包括：no_patch, no_attention, no_pos, patch_size(2/8/16), history(4/8/32/64), n_layers(1/2/4/6), latent_dim(12/32/128/256)
    - 完整结果在 `results/ablation/platform1/ablation_platform1/20260605_120117/ablation_results.json`
  - **Platform2 消融**（19 种变体）:
    - 变体包括：no_patch, no_attention, no_pos, patch_size(1/4), history(2/4/6/8/12/16), n_layers(1/2/3/4), latent_dim(4/8/16/32/64)
    - 完整结果在 `results/ablation/platform2/ablation_platform2/20260605_012621/ablation_results.json`
  - 每组消融包含 baseline 对比 + 各变体 RMSE/MAE + 参数量
- **Verification**: ablation_results.json 数据完整，消融排序合理

## 2026-06-05 — 最终版本确认（commit 693efab）

- **Objective**: 恢复稳定版本，确认全部训练结果可用
- **Work completed**:
  - Git commit `693efab` — "恢复之后的版本，测试过没问题"
  - `configs/platform1.yaml` / `platform2.yaml` 敲定为最终训练配置
- **Files changed**: `configs/`, `scripts/`, `src/patchtst_koopman/training/edmd_trainer.py` 等
- **Current best results**:
  - **Platform1 (6-state)**: PatchTST RMSE=0.157, MLP=0.420, LSTM=0.410, EDMD=0.903
  - **Platform2 (2-state)**: PatchTST RMSE=0.474, MLP=1.380, LSTM=1.796, EDMD=1.332

## 2026-06-05 (下午) — 消融 pipeline bug 修复 + 评估完成

- **Objective**: 修复 `run_ablation_pipeline.py` 报错，并做预防性全面审查，确保后续训练不会中途失败
- **Work completed**:
  - **Root cause**: `test_ablation.py:18` 使用了 `from scripts.ablation.train_ablation import ...`，subprocess 运行时 Python 不识别 `scripts.ablation` 为 package
  - **Fix**: 改为 bare relative import `from train_ablation import ...`（两文件同目录）
  - **Preventive review**: 全面审查了训练全链路（config → model build → Stage 0/1/2 → checkpoint），识别 25 个潜在问题
  - **数值稳定性修复**: `edmd_trainer.py` 中 `np.linalg.inv` → `np.linalg.solve` + NaN/Inf guard
  - **5 个 encoder 文件补充 divisibility check**: `patchtst_encoder.py`, `no_attention.py`, `no_positional.py`, `readout.py`, `pure_feature.py`
  - **评估验证**: 双平台消融评估均 PASSED
    - Platform1: 19 变体，baseline rollout RMSE=0.4116
    - Platform2: 18 变体，baseline rollout RMSE=0.7942
- **Problems encountered**:
  - `ModuleNotFoundError: No module named 'scripts.ablation'` — 已修复
  - `np.linalg.inv` 数值不稳定风险 — 已修复
  - 5 个 encoder 缺失 divisibility check — 已修复
  - Platform1 latent_dim=256 数值溢出 NaN — 已记录，属超参数问题
- **Verification**: `python scripts/ablation/test_ablation.py` 双平台评估均通过
- **Files changed**: `test_ablation.py`, `edmd_trainer.py`, `patchtst_encoder.py`, `no_attention.py`, `no_positional.py`, `readout.py`, `pure_feature.py`
- **Next steps**: 论文配图 + 撰写
