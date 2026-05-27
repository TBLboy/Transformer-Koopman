# Progress Log

## 2026-05-25 20:00 Local Time

- **Objective**: 在 code-projectv2/ 新写一份干净代码（项目重构）
- **Work completed**:
  - 新建项目骨架（目录树 + pyproject.toml + requirements.txt + .gitignore + README.md）
  - 从原 code_project/ 复制 data/（可能在 sandbox 中未持久化）
  - 复制 model_assets/ 到 deploy/algorithms/tk_assets/model_assets/
  - 创建完整 Python 包 `src/patchtst_koopman/` 及全部子包 __init__.py
  - 中文目录英文化（实验3代码→deploy/, 实验1/2绘图→figures/, experiments→scripts/, config→configs/）
  - aabb→tk_assets 重命名，全部 import 更新
  - 抽取共用工具：device.py, data_prep.py, evaluation.py
  - 抽取共用 PositionalEncoding（消除 7 个文件重复）
  - 重写 ablation/models.py 为正规 AblationModel(nn.Module) 子类 + 10 工厂函数
  - 配置收拢：只保留 platform1.yaml / platform2.yaml
  - 硬编码路径改为 argparse 必需参数
  - .gitignore + results/.gitkeep
- **Business logic impact**: Main logic restructured, no behavioral change
- **Problems encountered**:
  - pip install SSL 错误（pypi 镜像无法访问）
  - 基础 Python 3.8 不满足 >=3.10 要求
- **Resolution**:
  - 使用 `pip install -e . --no-deps` 跳过依赖安装（conda env 已有 torch）
  - pyproject.toml requires-python 降为 >=3.8
- **Verification**: `scripts/smoke_test.py` 全部通过（import → lifter → export_assets → 1 epoch）
- **Unverified items**: 正式 500 epochs 训练未运行；实物部署未验证
- **Files changed**: 全部在 code-projectv2/ 下新创建
- **Next steps**: 用户确认 data/ 存在后开始正式训练，或继续论文撰写

## 2026-05-26 20:36 Local Time

- **Objective**: 回答 4 个待定问题 + 审查 EDMD 和 End-to-End 训练逻辑
- **Work completed**:
  - 确认 data/ 存在（experiment_001~006, 18 个 NPZ）
  - 审查 EDMDTrainer（edmd_trainer.py）三阶段训练逻辑
  - 审查 End-to-End 实现（train_patchtst.py + mlp_koopman_trainer.py）
  - 更新 open-questions.md 中 4 个问题的答案
- **Business logic impact**: None（仅审查，未改代码）
- **Problems encountered**:
  - PatchTST 模型的 End-to-End 训练路径未实现（train_patchtst.py:99 抛 NotImplementedError）
  - MLP-Koopman 的 End-to-End 已实现（mlp_koopman_trainer.py._train_end_to_end）
- **Resolution**: 记录为已知缺失，等待用户决定是否需要补全
- **Verification**: 审查完成
- **Unverified items**: 无
- **Files changed**: `.project-log/business-logic/open-questions.md`, `progress.md`, `current-session.md`
- **Next steps**: 等待用户对 End-to-End 缺失的回应
