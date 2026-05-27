# Deploy — Platform 2 Transformer-Koopman LQR Controller

部署给上位机控制软件 `FlexibleArmControl34` 用的控制器包。

## 产物结构

```text
deploy/
  README.md
  export_assets.py                              # 从训练 checkpoint 导出资产
  algorithms/
    transformer_koopman_controller.py           # 主控制器（algorithms/ 根目录唯一 .py）
    configs/
      transformer_koopman_controller.json       # GUI 默认参数
    tk_assets/                                  # 依赖包（曾用名 aabb/）
      __init__.py
      transformer_koopman_model.py              # 部署侧独立模型定义
      transformer_koopman_lifter.py             # 在线升维函数 + 历史缓冲
      model_assets/
        platform2_full_model.pth
        platform2_metadata.json
```

## 部署目标

把 `deploy/algorithms/` 下的全部内容复制到上位机：

```text
C:\Users\Windows\Desktop\FlexibleArmControl34\algorithms\
```

`AlgorithmManager` 会自动扫描并加载 `TransformerKoopmanController`。

## 运行依赖（上位机虚拟环境）

- PyTorch（CPU 即可，CUDA 也支持）
- NumPy
- PyQt6
- `control`（首选 `dlqr`；不可用时回退到 Riccati 迭代）

## 控制器接口

继承 `BaseAlgorithm`，实现：

- `calculate_control(current_pos, current_step, trajectory_sequence)`
- `get_settings_widget()`
- `get_name()`
- `reset()`

## 默认参数

- `Q_x1=800`、`Q_x2=700`、`alpha=0.0`、`R_control=1.0`、`ff_gain=1.0`、`u_limit=100`
- `device="cuda"`，CUDA 不可用时自动回退 CPU
- 输出符号 `(-u0, +u1)` 与既有 `KoopmanLQRController` 保持一致

## 重新生成资产

```bash
# 在 code-projectv2/ 目录下，先训练得到 results/.../full_model_model.pth
python deploy/export_assets.py \
    --source results/models/ablation_platform2/<run_id>/full_model/full_model_model.pth
```

`export_assets.py` 会把 checkpoint 复制为 `deploy/algorithms/tk_assets/model_assets/platform2_full_model.pth`，并写出 `platform2_metadata.json`。

## 命名说明

历史上这个依赖包叫 `aabb/`，重构时改名为 `tk_assets/`（Transformer-Koopman assets）。如果你要把新版部署到上位机，需要同时复制：

- `deploy/algorithms/transformer_koopman_controller.py`
- `deploy/algorithms/configs/transformer_koopman_controller.json`
- `deploy/algorithms/tk_assets/` 整个目录
