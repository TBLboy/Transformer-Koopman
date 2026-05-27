# Business Logic Decision Records

## 2026-05-25 — 重构为 Python 包

- **Decision**: 原 `code_project/` 全部不动，在 `code-projectv2/` 新建正规 Python 包
- **Context**: 原项目无 `__init__.py`，依赖 19 处 `sys.path.append`，无法 `pip install`
- **Alternatives considered**:
  - 在原项目上修修补补 → 风险高，破坏已有工作
  - 只加 `__init__.py` → 目录结构中文仍混乱
- **Reason**: 重建可全面规范结构，原项目保留作为对照
- **Status**: active

## 2026-05-25 — 消融模型类重构

- **Decision**: 将 `nn.Module() + lambda forward` 反模式改为正规 `AblationModel(nn.Module)` 子类 + 10 个工厂函数
- **Context**: 原实现无法正确注册子模块，`model.parameters()` 不完整，影响 optimizer
- **Alternatives considered**: 继续使用 lambda（不修复 bug 会引入隐患）
- **Reason**: PyTorch 最佳实践；submodule 注册正确才能端到端训练
- **Status**: active

## 2026-05-25 — 数据自包含

- **Decision**: 从原项目复制 `data/` 到 `code-projectv2/data/`
- **Context**: 新项目需要独立可运行
- **Reason**: pip install 后立刻能训练，无需额外下载
- **Status**: active（注意：复制操作在 sandbox 中进行，实际 data/ 目录当前为空，需手动重新复制）

## 2026-05-25 — 只保留两个 config

- **Decision**: 新项目只保留 `platform1.yaml` 和 `platform2.yaml`
- **Context**: 原项目有 6 个 YAML（config.yaml, config1.yaml, 目前最好的.yaml, 平台1备份.yaml 等），内容混乱
- **Reason**: 每个平台对应一个权威配置，避免混淆
- **Status**: active

## 2026-05-25 — aabb 改名 tk_assets

- **Decision**: 部署包子包 `aabb/` 改名为 `tk_assets/`
- **Context**: `aabb` 名称无意义（可能是临时命名）
- **Reason**: 语义化目录名（Transformer-Koopman assets）
- **Status**: active

## 2026-05-25 — PositionalEncoding 抽离

- **Decision**: 将 7 个消融编码器重复定义的 `PositionalEncoding` 抽出为共用模块
- **Context**: 每个消融编码器文件都有完全相同的 `PositionalEncoding` 类定义
- **Reason**: DRY；修改参数只需改一处
- **Status**: active
