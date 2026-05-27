# 快速开始指南

## 1. 环境准备

```bash
cd code-projectv2
pip install -e .
```

## 2. 准备数据

数据已自包含在 `data/` 目录下（NPZ 格式，包含 `x`, `u`, `t`, `trajectory_id` 四个字段）。如需新建实验数据：

```python
import numpy as np

train_data = {
    'x': np.random.randn(2000, 2),
    'u': np.random.randn(2000, 2),
    't': np.arange(2000) * 0.2,
    'trajectory_id': np.array([0]*800 + [1]*600 + [2]*600)
}
np.savez('data/experiment_001/train.npz', **train_data)
# 同样创建 val.npz 和 test.npz
```

## 3. 训练模型

```bash
python scripts/train_patchtst.py --config configs/platform2.yaml
```

## 4. 测试模型

```bash
python scripts/test_patchtst.py \
    --model_path results/models/<checkpoint>.pth \
    --config configs/platform2.yaml \
    --traj_idx 0 \
    --save_dir results/test
```

## 5. 查看结果

- `results/models/<checkpoint>.pth` — 训练好的模型
- `results/test/trajectory_0_comparison.png` — 对比图
- `results/test/trajectory_0_results.npz` — 数值结果

## 6. 调整配置

编辑 `configs/platform1.yaml` 或 `configs/platform2.yaml`：

```yaml
training:
  method: "edmd"  # 或 "end_to_end"

encoder:
  history_length: 16
  patch_length: 4
  latent_dim: 128

training:
  edmd:
    pretrain:
      num_epochs: 100
```

## 7. 常见问题

### Q: 找不到数据文件
A: 确保 `configs/platformX.yaml` 中 `data.data_dir` 指向正确的 NPZ 目录。

### Q: CUDA out of memory
A: 减小 batch_size 或在 config 中将 `experiment.device` 改为 `"cpu"`。

### Q: 训练不收敛
A: 检查数据是否归一化，尝试降低学习率。

### Q: 谱半径 > 1
A: 在 config 中启用 SVD 限制（`training.edmd.compute.svd_clipping: true`）。

## 8. 下一步

- 查看 `docs/ABLATION_DESIGN.md` 了解消融实验设计
- 查看 `docs/TRADITIONAL_EDMD.md` 了解传统 EDMD 对照基线
- 运行 `python scripts/ablation/train_ablation.py --platform platform2 --variants all`
