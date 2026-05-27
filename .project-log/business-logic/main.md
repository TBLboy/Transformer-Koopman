# Main Business Logic

## Status

- Current main path status: Stable（重构后）

## Main Path

```text
Data -> Dataset -> Train(EDMD/End2End) -> Eval -> Deploy
```

## Path Summary

1. **Data**: NPZ 文件 (x, u, t, trajectory_id) 存于 data/experiment_00x/
2. **Dataset**: KoopmanDataset 构造滑动窗口样本 (x_history, u_t -> x_next)
3. **Train**: 
   - EDMD 两步法：① 预训练编码器（重构损失） ② EDMD 计算 Koopman 矩阵 + SVD 裁剪
   - End-to-End：联合训练编码器+Koopman+解码器
   - Traditional EDMD：手工升维函数 + 最小二乘 Koopman 矩阵
   - MLP-Koopman：MLP 编码器代替 PatchTST
4. **Eval**: iterative_prediction() 多步预测 + RMSE/MAE + 轨迹对比图
5. **Deploy**: export_assets.py 导出 .pth → 上位机 TransformerKoopmanController

## Implementation Priority

- Current target node: Data（训练数据已有）
- Current target edge: Train -> Eval（已实现，可用于正式训练）

## Stable Assumptions

- PyTorch 作为自动求导框架
- Koopman 矩阵使用 SVD 裁剪保证稳定性
- 所有配置通过 YAML 文件管理
- PLATFORM_CONFIGS 用于消融实验跨平台参数

## Verification Status

- scripts/smoke_test.py 全部通过（import、lifter、export_assets、1 epoch 训练）
