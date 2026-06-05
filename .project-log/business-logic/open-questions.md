# Open Business Logic Questions

## Resolved Questions

### Q-20260526-001 — data/ 实际状态 ✅

- **Related node**: N1 (RawData)
- **Question**: `code-projectv2/data/` 目录当前为空。之前的复制操作在 sandbox 中执行，完成后数据实际是否存在？
- **Answer**: **数据已存在。** experiment_001 ~ experiment_006 共 18 个 NPZ 文件。

### Q-20260526-002 — 正式训练计划 ✅

- **Related node**: N3 (Trained Model)
- **Question**: 用户是否需要立即启动完整训练？
- **Answer**: **训练已全部完成**（2026-05-27 ~ 06-02），双平台 4 种方法 × 多次调参 × 消融实验均已跑完。

### Q-20260526-003 — 上位机部署验证 ✅

- **Related node**: N6 (RealTimeControl)
- **Question**: 是否需要将 deploy/ 复制到 FlexibleArmControl34？
- **Answer**: **已部署完成。** 4 个基线控制器（Transformer/MLP/LSTM/EDMD）均已导出到 FlexibleArmControl34 并通过校验。

### Q-20260526-004 — End-to-End 训练 ✅

- **Related node**: N3 (Trained Model)
- **Question**: End-to-End 训练方法是否已完全实现并验证？
- **Answer**: **PatchTST 和 MLP 均已实现。**
  - PatchTST: `edmd_trainer.py:65-66` 中 `train()` 方法支持 `method="end_to_end"`，调度 `_train_end_to_end()`（完整实现：早停/梯度裁剪/SVD投影/LR调度/最佳checkpoint回载）
  - 旧报告 "train_patchtst.py:99 抛 NotImplementedError" 在最新代码中**不成立**，脚本中无任何 `NotImplementedError`
  - MLP-Koopman: `mlp_koopman_trainer.py._train_end_to_end()` 已实现
- **Status**: ✅ **已实现，无需补全**

### Q-20260605-001 — 模型保存行为 ✅

- **Related node**: N3 (Trained Model)
- **Question**: 最终保存的 `model_best.pth` 是否真的来自最佳 epoch？
- **Answer**: 当前 EDMDTrainer 在预训练阶段保存的是 best val_loss checkpoint，但 EDMD refit（最小二乘 Koopman 矩阵）在早停恢复最佳权重之后执行；refit 不依赖 epoch 所以最终模型 = best encoder + refit 后的 A/B。**LSTM 训练器不跟踪 best 模型，只保存最终结果。**

### Q-20260605-002 — 消融 pipeline ImportError ✅

- **Related node**: N7 (AblationResults)
- **Question**: `run_ablation_pipeline.py` 评估阶段报 `ModuleNotFoundError: No module named 'scripts.ablation'`，原因和修复？
- **Answer**: `test_ablation.py:18` 使用了包式 import，但 subprocess 下 `scripts/` 不被识别为 package。改为 bare relative import `from train_ablation import ...` 解决。

### Q-20260605-003 — 消融训练潜在 bug 审查 ✅

- **Related node**: N7 (AblationResults)
- **Question**: 消融训练全链路是否有其他潜在 bug 会导致训练中途失败？
- **Answer**: 全面审查发现 3 类高优先级问题，均已修复：
  1. EDMD `np.linalg.inv` 数值不稳定 → `np.linalg.solve`
  2. 5 个 encoder 缺失 divisibility check → 全部补上
  3. EDMD 矩阵无 NaN/Inf 检测 → 添加 guard

## Active Questions

### Q-20260605-004 — 代价函数从 3 项扩展为 5 项（理论修改）

- **Related node**: N3 (Trained Model), Section IV-B (Training Procedure)
- **Context**: 参考 LSTM-Enhanced Deep Koopman 的多步损失设计，论文当前仅使用单步预测损失（$\mathcal{L}_x, \mathcal{L}_z, \mathcal{L}_c$），存在 train-test mismatch（训练单步，评估多步 rollout）
- **Proposed change**: 新增两个多步损失，扩展为 5 项：
  1. $\mathcal{L}_x$ — 单步物理预测（保留）
  2. $\mathcal{L}_z$ — 单步 latent 一致性（保留）
  3. $\mathcal{L}_c$ — 重编码一致性（保留，重新定位为编码器鲁棒性正则项）
  4. $\mathcal{L}_{\mathrm{multi},x}$ **(新增)** — 多步物理轨迹预测 $\sum_{i=1}^{N_L}\|\hat{\mathbf{x}}_{k+i} - \mathbf{x}_{k+i}\|_2^2$
  5. $\mathcal{L}_{\mathrm{multi},z}$ **(新增)** — 多步 latent 轨迹预测 $\sum_{i=1}^{N_L}\|\hat{\mathbf{z}}_{k+i} - \mathbf{z}_{k+i}\|_2^2$
- **Design decisions (待确认)**:
  - $N_L$ (预测步数): 待定超参数
  - $\lambda_{\mathrm{multi},x}, \lambda_{\mathrm{multi},z}$ (权重): 待定超参数，参考文章给多步物理损失最高权重 (10×)
  - $\mathcal{L}_c$ 去留: **暂定保留**，理由：多步损失检查的是动力学预测精度，$\mathcal{L}_c$ 检查的是编码器对输入扰动的鲁棒性，两者互补。$\mathcal{L}_c$ 定位调整为 encoder consistency regularizer，权重建议取较小值
  - 不需要加重构损失：state-embedded 设计 $\mathbf{C}=[\mathbf{I}_n\;\mathbf{0}]$ 天然保证精确重构
- **Paper sections to modify**:
  - Section IV-B: 新增多步损失定义 + 更新总损失方程（3项→5项）
  - Algorithm 1: Stage 1 循环中加入多步 rollout 步骤
  - Section I (Introduction): 贡献点 2 微调，提及 multi-step prediction objectives
- **Impact on code** (后续): `edmd_trainer.py` Stage 1 训练循环需加入多步 rollout + 两新损失项的计算
- **Status**: 🔴 **待用户确认** — 需确定 $N_L$、权重取值、$\mathcal{L}_c$ 最终去留，然后进入论文正文修改
