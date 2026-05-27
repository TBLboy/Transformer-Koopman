"""
传统EDMD对照组使用说明
"""

# 传统EDMD对照组

这是论文中的对照组实现，用于与提议的TransformerKoopman方法进行比较。

## 特点

- **纯数学方法**：无神经网络，使用手写升维函数
- **升维函数**：支持多项式和RBF两种基函数
- **闭式解**：直接计算Koopman矩阵A、B，无迭代优化
- **独立参数**：与TransformerKoopman的EDMD参数完全分离

## 配置

在 `config/default_config.yaml` 中配置传统EDMD参数：

```yaml
training:
  traditional_edmd:
    # 升维函数配置
    lifting_function:
      type: "polynomial"  # polynomial / rbf
      params:
        degree: 3         # 多项式阶数（type=polynomial时使用）
        # n_centers: 10   # RBF中心点数量（type=rbf时使用）
        # sigma: 1.0      # RBF宽度（type=rbf时使用）

    # EDMD计算参数
    compute:
      regularization: 0.000001    # Tikhonov正则化
      svd_clipping: false         # 是否应用SVD限制
      batch_size: 1024            # 编码时的batch size
```

## 使用方式

### 1. 训练传统EDMD

```bash
python scripts/train_traditional_edmd.py --config configs/platform1.yaml
```

训练流程：
1. 初始化升维函数（多项式或RBF）
2. 升维所有训练数据
3. 闭式解计算Koopman矩阵A、B
4. 验证性能
5. 自动测试并生成预测图

模型保存到：`./results/metrics/traditional_edmd/`

### 2. 测试传统EDMD

```bash
python scripts/test_traditional_edmd.py --model_dir results/traditional_edmd --config configs/platform1.yaml
```

## 升维函数

### 多项式升维

例如 degree=2，状态 x=[x1, x2] 升维为：
```
z = [1, x1, x2, x1^2, x1*x2, x2^2]
```

升维维度：C(n+d, d)，其中n是状态维度，d是多项式阶数

### RBF升维

使用高斯RBF基函数：
```
z = [1, exp(-||x-c1||^2/sigma^2), exp(-||x-c2||^2/sigma^2), ...]
```

升维维度：1 + n_centers

## 文件结构

```
src/
├── lifting_functions/
│   ├── __init__.py
│   ├── polynomial.py      # 多项式升维函数
│   └── rbf.py             # RBF升维函数
├── training/
│   └── traditional_edmd_trainer.py  # 传统EDMD训练器
└── ...

scripts/
├── train_traditional_edmd.py  # 训练脚本
└── test_traditional_edmd.py   # 测试脚本
```

## 论文中的使用

在论文的实验部分（7.2 Modeling comparison），传统EDMD作为基线模型与以下方法进行比较：
- EDMD（传统EDMD）← 本实现
- MLP-Koopman
- LSTM/GRU-Koopman
- Transformer/PatchTST-Koopman（提议方法）

## 注意事项

1. **不动TransformerKoopman代码**：传统EDMD是完全独立的实现，不影响现有的TransformerKoopman方法
2. **参数分离**：传统EDMD的参数在 `training.traditional_edmd` 块中，与 `training.edmd` 完全分离
3. **模型保存位置**：`./results/metrics/traditional_edmd/`，包含A、B矩阵和结果

## 扩展

可以轻松添加其他升维函数：

```python
# 在 src/lifting_functions/ 中创建新文件
class CustomLifting:
    def fit(self, X):
        # 拟合升维函数
        pass

    def transform(self, X):
        # 升维变换
        pass

    def get_lifted_dim(self):
        # 返回升维后的维度
        pass
```

然后在 `traditional_edmd_trainer.py` 中添加支持。
