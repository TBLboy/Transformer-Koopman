# 消融实验安排文档

## 一、实验目标

通过系统性地移除或替换 PatchTST-Koopman 模型中的关键组件，验证各模块对模型性能的影响，为论文中的消融实验提供详细的实验依据和可视化素材。

---

## 二、实验平台

### 平台1：Flexible Manipulator（三自由度机械臂）
- **状态维度**: 6维 (3个关节位置 + 3个关节速度)
- **控制维度**: 3维 (3个关节力矩)
- **采样时间**: dt = 0.004s
- **数据来源**: `data/experiment_001`

### 平台2：Soft Robot（软体机器人）
- **状态维度**: 2维
- **控制维度**: 2维
- **采样时间**: dt = 0.2s
- **数据来源**: `data/experiment_006`

---

## 三、消融实验设计

### 3.1 模块级消融（Component Ablation）

**目的**: 验证 PatchTST 编码器中各核心模块的必要性

| 变体ID | 变体名称 | 移除/替换内容 | 预期结论 |
|--------|----------|--------------|---------|
| `no_patch` | Without Patching | 移除 Patch 机制，直接输入时间序列 | 验证 Patch 对噪声抑制和时间特征提取的作用 |
| `no_attention` | Without Attention | 用两层全连接层替代 Transformer | 验证自注意力机制对长距离时序依赖建模的重要性 |
| `no_positional` | Without Positional Encoding | 移除正弦位置编码 | 验证位置信息对时序建模的贡献 |

**训练配置**:
- 训练方法: EDMD
- 预训练轮数: 300 epochs (平台1) / 500 epochs (平台2)
- 批量大小: 128
- 学习率: 3e-4 (带早停和学习率衰减)

---

### 3.2 超参数消融（Hyperparameter Ablation）

**目的**: 确定针对各平台的最优超参数设置

#### 平台1 超参数范围

| 参数类型 | 参数名 | 基线值 | 消融范围 | 说明 |
|---------|--------|--------|---------|------|
| 历史窗口长度 | History (P) | 16 | 4, 8, 32, 64 | 影响模型捕获的历史信息量 |
| Patch长度 | Patch (L) | 4 | 2, 8, 16 | 影响时间序列分割粒度 |
| Readout方式 | Readout | mean | max, last | 影响序列信息的聚合方式 |

#### 平台2 超参数范围

| 参数类型 | 参数名 | 基线值 | 消融范围 | 说明 |
|---------|--------|--------|---------|------|
| 历史窗口长度 | History (P) | 4 | 2, 8, 16 | 影响模型捕获的历史信息量 |
| Patch长度 | Patch (L) | 2 | 1, 4 | 影响时间序列分割粒度 |
| Readout方式 | Readout | mean | max, last | 影响序列信息的聚合方式 |

---

## 四、实验变体汇总

### 4.1 平台1 实验变体 (共9个)

| 序号 | 变体ID | 变体名称 | 类型 | 参数设置 |
|------|--------|----------|------|---------|
| 1 | `full_model` | Full Model (Baseline) | 基准 | P=16, L=4, readout=mean |
| 2 | `no_patch` | Without Patching | 模块消融 | 无Patch机制 |
| 3 | `no_attention` | Without Attention | 模块消融 | 用FC层替代Transformer |
| 4 | `no_positional` | Without Positional Encoding | 模块消融 | 无位置编码 |
| 5 | `patch_L2` | Patch Length L=2 | 超参数消融 | L=2 |
| 6 | `patch_L8` | Patch Length L=8 | 超参数消融 | L=8 |
| 7 | `history_P4` | History P=4 | 超参数消融 | P=4 |
| 8 | `history_P8` | History P=8 | 超参数消融 | P=8 |
| 9 | `readout_max` | Max Pooling | 超参数消融 | readout=max |

### 4.2 平台2 实验变体 (共8个)

| 序号 | 变体ID | 变体名称 | 类型 | 参数设置 |
|------|--------|----------|------|---------|
| 1 | `full_model` | Full Model (Baseline) | 基准 | P=4, L=2, readout=mean |
| 2 | `no_patch` | Without Patching | 模块消融 | 无Patch机制 |
| 3 | `no_attention` | Without Attention | 模块消融 | 用FC层替代Transformer |
| 4 | `no_positional` | Without Positional Encoding | 模块消融 | 无位置编码 |
| 5 | `patch_L1` | Patch Length L=1 | 超参数消融 | L=1 |
| 6 | `history_P2` | History P=2 | 超参数消融 | P=2 |
| 7 | `history_P8` | History P=8 | 超参数消融 | P=8 |
| 8 | `readout_max` | Max Pooling | 超参数消融 | readout=max |

---

## 五、训练配置

### 5.1 模型架构参数

| 参数 | 平台1 | 平台2 |
|------|-------|-------|
| latent_dim | 64 | 10 |
| d_model | 128 | 16 |
| n_layers | 3 | 3 |
| n_heads | 4 | 2 |
| d_ff | 256 | 64 |
| dropout | 0.1 | 0.1 |

### 5.2 训练超参数

| 参数 | 平台1 | 平台2 |
|------|-------|-------|
| 预训练轮数 | 300 | 500 |
| 批量大小 | 128 | 128 |
| 初始学习率 | 3e-4 | 3e-4 |
| 早停patience | 50 | 50 |
| 学习率衰减 | 0.5 (patience=10) | 0.5 (patience=10) |

### 5.3 EDMD参数

| 参数 | 平台1 | 平台2 |
|------|-------|-------|
| 正则化系数 | 1e-6 | 1e-6 |
| SVD裁剪 | 关闭 | 关闭 |
| 谱半径约束 | 无 | 无 |

---

## 六、评估指标

### 6.1 主要指标
- **RMSE**: 均方根误差
- **MAE**: 平均绝对误差

### 6.2 评估方法
- **数据集**: 测试集第一条轨迹
- **预测方式**: 多步迭代预测
- **预测长度**: 轨迹剩余所有时刻

### 6.3 性能下降计算
```
性能下降率 = (变体RMSE - 基准RMSE) / 基准RMSE × 100%
```

---

## 七、实验执行顺序

### 阶段1: 基准测试（每个平台1个变体）
```
1. platform1_full_model
2. platform2_full_model
```
**目的**: 验证训练流程正确性，确认基准性能

### 阶段2: 模块消融（每个平台3个变体）
```
平台1: no_patch, no_attention, no_positional
平台2: no_patch, no_attention, no_positional
```
**目的**: 验证核心组件的必要性

### 阶段3: 超参数消融（每个平台4-5个变体）
```
平台1: patch_L2, patch_L8, history_P4, history_P8, readout_max
平台2: patch_L1, history_P2, history_P8, readout_max
```
**目的**: 确定最优超参数

---

## 八、预期结论

### 8.1 模块消融预期

| 变体 | 预期性能下降 | 原因分析 |
|------|-------------|---------|
| `no_patch` | 中等下降 | Patch机制有助于噪声抑制和特征提取 |
| `no_attention` | 显著下降 | 自注意力对长距离依赖建模至关重要 |
| `no_positional` | 轻微下降 | 位置信息有一定作用但非决定性 |

### 8.2 超参数消融预期

**History长度 (P)**:
- P过小: 无法捕获足够历史信息
- P过大: 引入过多噪声和计算负担
- 预期: 各平台存在最优P值

**Patch长度 (L)**:
- L过小: 失去时间聚合优势
- L过大: 丢失细节信息
- 预期: L=4(平台1) 和 L=2(平台2) 为较优选择

**Readout方式**:
- mean: 适合平稳信号
- max: 适合突出峰值
- last: 适合突变检测

---

## 九、结果保存

### 9.1 目录结构
```
results/models/ablation_{platform}/{timestamp}/
├── ablation_results.json          # 所有变体结果汇总
├── full_model_platform1/         # 各变体模型目录
│   └── full_model_model.pth
├── no_patch_platform1/
│   └── no_patch_model.pth
└── ...
```

### 9.2 结果文件格式
```json
{
  "platform": "platform1",
  "platform_name": "Platform 1 (Flexible Manipulator)",
  "timestamp": "20260426_091126",
  "baseline_params": {
    "history_length": 16,
    "patch_length": 4,
    "latent_dim": 64
  },
  "results": {
    "full_model": {
      "name": "Full Model (Baseline)",
      "rmse": 0.0123,
      "mae": 0.0089,
      "params": 523456
    },
    "no_patch": {
      "name": "Without Patching",
      "rmse": 0.0156,
      "mae": 0.0112,
      "params": 498765
    }
  },
  "baseline_rmse": 0.0123
}
```

---

## 十、可视化需求

### 10.1 柱状图对比
- 模块消融RMSE对比 (Full vs no_patch vs no_attention vs no_positional)
- 超参数消融RMSE对比 (不同P/L组合)

### 10.2 趋势图
- History长度 vs RMSE (P=4,8,16,32,64)
- Patch长度 vs RMSE (L=2,4,8,16)
- Readout方式对比 (mean vs max vs last)

### 10.3 预测轨迹图
- 各变体在测试集上的多步预测对比

---

## 十一、注意事项

1. **随机种子**: 统一使用 seed=42 确保可复现性
2. **设备**: 使用 CPU 进行训练（当前环境无 CUDA 支持）
3. **精度**: float64 双精度确保数值稳定性
4. **归一化**: 使用训练集统计量对测试集进行归一化
5. **轨迹边界**: 确保历史窗口不跨越不同轨迹

---

## 十二、命令执行

### 运行全部消融实验
```bash
cd code-projectv2
python scripts/ablation/train_ablation.py --platform platform1 --variants all --device cpu
python scripts/ablation/train_ablation.py --platform platform2 --variants all --device cpu
```

### 仅运行模块消融
```bash
python scripts/ablation/train_ablation.py --platform platform1 --variants module --device cpu
```

### 仅运行超参数消融
```bash
python scripts/ablation/train_ablation.py --platform platform1 --variants hyperparameter --device cpu
```

### 仅运行基准模型
```bash
python scripts/ablation/train_ablation.py --platform platform1 --variants full_model --device cpu
```

---

*文档生成时间: 2026-04-26*
*最后更新: 2026-04-26*
