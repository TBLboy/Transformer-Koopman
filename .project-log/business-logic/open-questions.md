# Open Business Logic Questions

## Active Questions

### Q-20260526-001 — data/ 实际状态 ✅

- **Related node**: N1 (RawData)
- **Question**: `code-projectv2/data/` 目录当前为空。之前的复制操作在 sandbox 中执行，完成后数据实际是否存在？
- **Answer**: **数据已存在。** experiment_001 ~ experiment_006 共 18 个 NPZ 文件。

### Q-20260526-002 — 正式训练计划 ✅

- **Related node**: N3 (Trained Model)
- **Question**: 用户是否需要立即启动完整训练？
- **Answer**: **用户自行启动，不需要自动触发。**

### Q-20260526-003 — 上位机部署验证 ✅

- **Related node**: N6 (RealTimeControl)
- **Question**: 是否需要将 deploy/ 复制到 FlexibleArmControl34？
- **Answer**: **暂不考虑。**

### Q-20260526-004 — End-to-End 训练 ✅

- **Related node**: N3 (Trained Model)
- **Related edge**: E3
- **Question**: End-to-End 训练方法是否已完全实现并验证？
- **Answer**: **PatchTST 模型未实现。** `train_patchtst.py:99` 中 `method="end_to_end"` 直接抛 `NotImplementedError`。配置文件中 `end_to_end` 节有完整参数，但没有代码使用。**MLP-Koopman 基线有完整的 End-to-End 实现**（`mlp_koopman_trainer.py._train_end_to_end`）。
- **Status**: Resolved — 功能缺失，需了解用户是否需要补全
