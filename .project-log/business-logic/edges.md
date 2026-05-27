# Business Logic Edges

## Edge: E1 — Data to Dataset

```yaml
edge_id: E1
from: N1 (RawData)
to: N2 (Dataset)
path: main
status: stable
method: KoopmanDataset 构造
execution_chain:
  - 1. 加载 NPZ 文件
  - 2. 归一化（按训练集 mean/std）
  - 3. 构造滑动窗口样本 (history_length -> P)
  - 4. 返回 DataLoader
inputs:
  - data_dir (config.data.data_dir)
  - config.data.state_dim, config.data.control_dim
  - config.encoder.history_length
outputs:
  - train_ds, val_ds, test_ds
parameters:
  - data_dir: str, 来源 YAML
  - history_length: int, 默认 16
interfaces:
  - patchtst_koopman.utils.data_prep.prepare_datasets()
  - patchtst_koopman.data.dataset.KoopmanDataset
error_handling:
  - NPZ 不存在: FileNotFoundError
  - 维度不匹配: ValueError
verification:
  - prepare_datasets 返回的 dataset 长度非零
```

## Edge: E2 — Dataset to Model (EDMD)

```yaml
edge_id: E2
from: N2 (Dataset)
to: N3 (Trained Model)
path: main
status: stable
method: 两步 EDMD 训练
execution_chain:
  - 阶段 0: 用初始编码器计算 Koopman 矩阵（EDMD 初始化）
  - 阶段 1: 预训练编码器（重构损失 + 潜在一致性损失）
  - 阶段 2: 固定编码器，重新计算 Koopman 矩阵（SVD 裁剪）
  - 保存 checkpoint
inputs:
  - train_ds, val_ds
  - full config
outputs:
  - model state_dict + koopman A/B matrices
parameters:
  - training.method: "edmd"
  - training.edmd.pretrain.num_epochs
  - training.edmd.pretrain.learning_rate
  - training.edmd.compute.svd_clipping: true/false
interfaces:
  - patchtst_koopman.training.edmd_trainer.EDMDTrainer
error_handling:
  - NaN loss -> 降低 learning rate 或检查归一化
  - 谱半径 > 1 且 svd_clipping=false -> 警告
verification:
  - train loss 下降
  - val loss 不 NaN
  - 模型保存成功
```

## Edge: E3 — Dataset to Model (End-to-End)

```yaml
edge_id: E3
from: N2 (Dataset)
to: N3 (Trained Model)
path: main
status: draft
method: End-to-End 联合训练
execution_chain:
  - 1. 编码器 + Koopman 层 + 解码器构成完整计算图
  - 2. 端到端 BP 更新所有参数
  - 3. 可选的 Koopman 矩阵正交正则化
inputs:
  - train_ds, val_ds
  - config
outputs:
  - model state_dict
parameters:
  - training.method: "end_to_end"
interfaces:
  - patchtst_koopman.training.edmd_trainer.EDMDTrainer
verification:
  - 收敛性优于 EDMD 两步法（待验证）
```

## Edge: E4 — Model to Evaluation

```yaml
edge_id: E4
from: N3 (Trained Model)
to: N4 (Evaluation Results)
path: main
status: stable
method: 半开环迭代预测
execution_chain:
  - 1. 从测试集取初始窗口 x_history
  - 2. 使用真值 u 迭代预测 x_pred
  - 3. 计算 RMSE/MAE
  - 4. 绘制真实 vs 预测对比图
inputs:
  - model
  - test_ds
  - traj_idx
outputs:
  - RMSE, MAE
  - comparison plot (.png)
  - results .npz
parameters:
  - traj_idx: int
interfaces:
  - patchtst_koopman.utils.evaluation.iterative_prediction()
  - patchtst_koopman.utils.evaluation.plot_trajectory_comparison()
verification:
  - RMSE 与论文一致
  - 图像正确保存
```

## Edge: E5 — Model to Deploy

```yaml
edge_id: E5
from: N3 (Trained Model)
to: N5 (DeployAssets)
path: main
status: stable
method: 导出部署资产
execution_chain:
  - 1. 加载 .pth checkpoint
  - 2. 重映射 key（pos_encoder -> positional_encoding 等）
  - 3. 复制到 deploy/tk_assets/model_assets/
  - 4. 写入 platform2_metadata.json
inputs:
  - source .pth path
outputs:
  - platform2_full_model.pth
  - platform2_metadata.json
parameters:
  - source: str, checkpoint 路径（argparse 必需）
interfaces:
  - deploy.export_assets.main()
verification:
  - TransformerKoopmanLifter 加载成功
  - 前向推理 shape 正确
```

## Edge: E6 — Deploy to Real-Time Controller

```yaml
edge_id: E6
from: N5 (DeployAssets)
to: N6 (RealTimeControl)
path: main
status: draft
method: 复制到上位机目录
execution_chain:
  - 1. 将 deploy/algorithms/ 复制到 FlexibleArmControl34/algorithms/
  - 2. AlgorithmManager 自动扫描发现 TransformerKoopmanController
  - 3. 加载模型资产
  - 4. 运行控制循环
inputs:
  - deploy/algorithms/ 目录
outputs:
  - (dx, dy) 电机控制量
parameters:
  - Q_x1, Q_x2, alpha, R_control, ff_gain, u_limit
interfaces:
  - BaseAlgorithm.calculate_control()
  - FlexibleArmControl34.AlgorithmManager
verification:
  - 人工验证（实物实验）
```

## Edge: E7 — Ablation

```yaml
edge_id: E7
from: N2 (Dataset) + config
to: N7 (AblationResults)
path: main
status: stable
method: 消融实验
execution_chain:
  - 1. 遍历 ABLATION_VARIANTS
  - 2. 每个变体用对应的 factory 创建 AblationModel
  - 3. 训练（与 E2 相同逻辑）
  - 4. 评估
  - 5. 收集结果到 DataFrame
  - 6. 生成 CSV / LaTeX 表 / 柱状图
inputs:
  - config
  - variants list
outputs:
  - CSV, .tex, .pdf, .png
parameters:
  - variants: "module" / "hyperparameter" / "all"
interfaces:
  - patchtst_koopman.ablation.models.ABLATION_MODELS
  - scripts.ablation.train_ablation
  - figures.ablation.generate_ablation_materials
verification:
  - full_model 在所有变体中表现最好
  - 去掉 Patch/Attention/PositionalEncoding 后性能下降
```
