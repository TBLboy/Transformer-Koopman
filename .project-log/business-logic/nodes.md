# Business Logic Nodes

## Node Template

```yaml
id: <node-id>
name: <node-name>
status: draft | stable | deprecated
state:
  - <what has become true at this node>
inputs:
  - <required input data or signal>
outputs:
  - <available output data or signal>
data_format:
  - <data type, message type, file type, coordinate frame, etc.>
related_hardware:
  - <hardware if any>
related_interfaces:
  - <python API, file format, config key>
verification:
  - <how to confirm this state is reached>
```

## Nodes

### N1: RawData

```yaml
id: N1
name: Raw NPZ Data
status: stable
state:
  - 原始传感器数据已采集
  - 保存为 NPZ 格式
inputs:
  - 传感器采集的物理信号
outputs:
  - train.npz / val.npz / test.npz
data_format:
  - NPZ 文件包含：x (N,state_dim), u (N,control_dim), t (N,), trajectory_id (N,)
related_hardware:
  - Platform 1: 6-DOF 柔性机械臂
  - Platform 2: 2-DOF 软体机器人
related_interfaces:
  - numpy .npz
verification:
  - np.load() 可读取，shape 正确
```

### N2: Dataset

```yaml
id: N2
name: KoopmanDataset
status: stable
state:
  - 原始数据已加载、归一化
  - 滑动窗口样本已构造
inputs:
  - NPZ 文件路径
  - config (history_length, state_dim, control_dim)
outputs:
  - train_ds, val_ds, test_ds (PyTorch Dataset)
data_format:
  - 每个样本: (x_history [P, n], u_t [m]) -> x_next [n]
  - x_history: 过去 P 步状态
  - u_t: 当前控制输入
  - x_next: 下一时刻状态
related_interfaces:
  - patchtst_koopman.data.dataset.KoopmanDataset
  - patchtst_koopman.utils.data_prep.prepare_datasets()
verification:
  - len(ds) 正确，第一个样本 shape 符合预期
```

### N3: Model

```yaml
id: N3
name: Trained Model
status: stable
state:
  - 编码器 + Koopman 动力学 + 解码器 全部参数已训练
inputs:
  - train_ds, val_ds
  - config (model architecture params, training hyperparams)
outputs:
  - PatchTSTKoopmanModel (state_dict + config)
data_format:
  - PyTorch .pth 文件 (model_state_dict + config + koopman_matrices)
related_interfaces:
  - patchtst_koopman.models.full_model.PatchTSTKoopmanModel
  - patchtst_koopman.training.edmd_trainer.EDMDTrainer
verification:
  - 模型前向传播无误
  - 谱半径 <= 1 (SVD 裁剪后)
  - val loss 收敛
```

### N4: Evaluation

```yaml
id: N4
name: Evaluation Results
status: stable
state:
  - 多步预测结果已生成
  - 对比图已保存
inputs:
  - model, test_ds, traj_idx
outputs:
  - RMSE, MAE
  - trajectory comparison plot
  - prediction results .npz
data_format:
  - 图像 .png
  - 数值 .npz (predicted vs ground truth)
related_interfaces:
  - patchtst_koopman.utils.evaluation.iterative_prediction()
  - patchtst_koopman.utils.evaluation.plot_trajectory_comparison()
verification:
  - 半开环预测与真实轨迹吻合
  - RMSE 与论文一致
```

### N5: DeployAssets

```yaml
id: N5
name: Deployable Assets
status: stable
state:
  - 模型 checkpoint 已导出到 deploy/tk_assets/model_assets/
inputs:
  - .pth checkpoint
outputs:
  - platform2_full_model.pth (部署侧独立模型)
  - platform2_metadata.json
data_format:
  - 独立 .pth (不依赖 patchtst_koopman 包的 key 映射)
  - JSON 元信息 (source, platform, model_type)
related_interfaces:
  - deploy.export_assets.main()
verification:
  - TransformerKoopmanLifter 可加载并向前推理
```

### N6: RealTimeControl

```yaml
id: N6
name: Real-Time Controller
status: draft
state:
  - 控制器已部署到上位机
  - AlgorithmManager 自动发现并加载
inputs:
  - current_pos, current_step, trajectory_sequence
  - model_assets/ (预加载的 .pth)
outputs:
  - (dx, dy) 电机控制量
data_format:
  - Python float tuple
related_hardware:
  - FlexibleArmControl34 上位机
  - 2-DOF 软体机器人
related_interfaces:
  - deploy.algorithms.transformer_koopman_controller.TransformerKoopmanController
  - BaseAlgorithm.calculate_control()
verification:
  - 上位机测试（人工验证）
```

### N7: AblationResults

```yaml
id: N7
name: Ablation Experiment Results
status: stable
state:
  - 多个消融变体已训练并评估
  - CSV / LaTeX 表格 / 柱状图已生成
inputs:
  - platformX.yaml
  - variants list (module / hyperparameter / all)
outputs:
  - CSV 文件 (RMSE, MAE by variant)
  - LaTeX 表格文件
  - PDF/PNG 柱状图
data_format:
  - CSV, .tex, .pdf, .png
related_interfaces:
  - scripts.ablation.train_ablation
  - figures.ablation.generate_ablation_materials
verification:
  - 柱状图趋势与论文一致
  - 消融排序合理（full_model 最优，去掉关键组件后性能下降）
```
