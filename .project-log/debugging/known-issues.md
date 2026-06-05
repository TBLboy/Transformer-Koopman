# Debugging

## Known Issues

### 2026-05-25 — data/ 可能为空 ✅ 已解决

- **Symptom**: `code-projectv2/data/` 目录当前无文件
- **Likely cause**: 之前的复制操作在 Cursor sandbox 中进行，可能未持久化
- **Fix**: 手动从 `code_project/data/` 复制
- **Command**: `Copy-Item "C:\Users\Windows\Desktop\论文4\code_project\data\*" "C:\Users\Windows\Desktop\论文4\code-projectv2\data\" -Recurse`
- **Status**: ✅ **已解决** — data/ 目录完整，experiment_001~006 共 18 个 NPZ 文件已确认存在

### 2026-05-25 — conda run 不支持多行脚本

- **Symptom**: `conda run -n koopman python -c "..."` 当参数包含换行时失败
- **Fix**: 改用单行命令或写入 .py 文件执行
- **Workaround used**: 脚本统一写在 `.py` 文件中调用
- **Status**: Workaround applied

### 2026-06-05 — cursor-gateway dd-gpt-5.4 工具调用异常 🗄️ 已归档

- **Symptom**: 使用 `E:\cursor-gateway` 中转 `dd-gpt-5.4` 模型时，Cursor Agent 的工具面板中缺少 `Write/StrReplace` 等关键文件写入工具
- **Status**: 🗄️ **已归档** — 属于 `cursor-gateway` 框架自身问题，不影响 `code-projectv2` 主项目。当前会话直接使用 `dd-gpt-5.4`（不经 gateway）工作正常

### 2026-06-05 — 消融 pipeline ImportError ✅ 已修复

- **Symptom**: `run_ablation_pipeline.py` 评估阶段报错 `ModuleNotFoundError: No module named 'scripts.ablation'`
- **Root cause**: `test_ablation.py:18` 使用 `from scripts.ablation.train_ablation import ...`，subprocess 运行时 Python 不识别 `scripts.ablation` 为 package（无 `__init__.py`）
- **Fix**: 改为 bare relative import `from train_ablation import ...`
- **Status**: ✅ **已修复**

### 2026-06-05 — EDMD `np.linalg.inv` 数值不稳定 ✅ 已修复

- **Symptom**: 当数据矩阵接近奇异时，`np.linalg.inv` 可能产生极不准确的 Koopman 矩阵
- **Fix**: `edmd_trainer.py:461-474` 改用 `np.linalg.solve` + NaN/Inf 检测 guard
- **Status**: ✅ **已修复**

### 2026-06-05 — 5 个 encoder 缺失 divisibility check ✅ 已修复

- **Symptom**: 当 `history_length` 不能被 `patch_length` 整除时，reshape 操作产生隐晦的 PyTorch 维度错误
- **Files**: `patchtst_encoder.py`, `no_attention.py`, `no_positional.py`, `readout.py`, `pure_feature.py`
- **Fix**: 全部在 `__init__` 中添加 `if self.history_length % self.patch_length != 0: raise ValueError(...)`
- **Status**: ✅ **已修复**

### 2026-06-05 — Platform1 latent_dim=256 NaN 发散 ⚠️ 已知

- **Symptom**: Platform1 消融中 latent_dim=256 变体在 rollout 预测时数值溢出为 NaN
- **Cause**: 256-dim 潜在空间过大，EDMD 矩阵接近奇异，rollout 误差指数放大
- **Status**: ⚠️ **已知，非代码 bug** — 属超参数不稳定，论文中记为无效点
