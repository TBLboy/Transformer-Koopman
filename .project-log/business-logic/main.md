# Main Business Logic

## Status

- Current main path status: Stable（重构后，消融实验评估完成）

## Main Path

```text
Data -> Dataset -> Train(EDMD/End2End) -> Eval -> Deploy -> Control
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

- Current target node: **N3 (Trained Model) + N7 (AblationResults) 均已完成**
- Current target edge: N3 -> N4 -> N5 -> N6（全链路已贯通，已产出论文可用结果）

## Completed Path Segments

| 路径 | 状态 |
|------|------|
| Data → Dataset → Train(EDMD) → Eval | ✅ 双平台 4 方法全部完成 |
| Data → Dataset → Train(Ablation) → Eval | ✅ 双平台消融完成，bug 已修复 |
| Eval → Deploy → Control | ✅ 控制器封装完成，Experiment 3 跟踪完成 |
| Paper figures | ✅ `figures/experiment1/output/` 已产出，`figures/ablation/` 脚本已验证可用 |

## Current Best Results

| Method | Platform1 RMSE | Platform2 RMSE |
|--------|---------------|---------------|
| PatchTST-Koopman | **0.157** | **0.474** |
| MLP-Koopman | 0.420 | 1.380 |
| LSTM-Koopman | 0.410 | 1.796 |
| Traditional EDMD | 0.903 | 1.332 |

## Ablation Latest Evaluation (2026-06-05)

| Platform | Variants | Baseline Rollout RMSE | Status |
|----------|----------|----------------------|--------|
| Platform1 (6-state) | 19 | 0.4116 | ✅ PASSED |
| Platform2 (2-state) | 18 | 0.7942 | ✅ PASSED |

## Known Code Fixes (2026-06-05)

| File | Issue | Severity |
|------|-------|----------|
| `test_ablation.py:18` | ImportError: `scripts.ablation` not a package | Critical |
| `edmd_trainer.py:461-474` | `np.linalg.inv` → `np.linalg.solve` + NaN guard | High |
| 5 encoder files | Missing `history_length % patch_length` check | High |

## Stable Assumptions

- PyTorch 作为自动求导框架
- Koopman 矩阵使用 SVD 裁剪保证稳定性
- 所有配置通过 YAML 文件管理
- PLATFORM_CONFIGS 用于消融实验跨平台参数
- EDMD 闭式解使用 `np.linalg.solve`（非 `inv`）保证数值稳定性

## Verification Status

- scripts/smoke_test.py 全部通过（import、lifter、export_assets、1 epoch 训练）
- 双平台 PatchTST / MLP / LSTM / Traditional EDMD 均完成完整训练并保存可复现结果
- 消融实验 37 组变体全部跑完 + 评估通过
- Bug 修复已验证，pipeline 可重复运行
