# Software Architecture

## Module Layout

```text
src/patchtst_koopman/          # 可安装 Python 包
├── models/                    # 模型定义
│   ├── patchtst_encoder.py    # PatchTST 编码器（核心创新）
│   ├── koopman_dynamics.py    # Koopman 线性动力学 (z_{k+1}=A z_k + B u_k)
│   ├── linear_decoder.py      # 线性解码器 (x = C z)
│   ├── full_model.py          # PatchTSTKoopmanModel（组合完整模型）
│   ├── mlp_encoder.py         # MLP 编码器（基线对比）
│   └── mlp_koopman_model.py   # MLP-Koopman（基线对比）
├── data/
│   └── dataset.py             # KoopmanDataset（滑动窗口构造）
├── training/
│   ├── edmd_trainer.py        # EDMD 两步法训练器（主方法）
│   ├── mlp_koopman_trainer.py # MLP-Koopman 训练器
│   └── traditional_edmd_trainer.py  # 传统 EDMD 训练器
├── lifting/                   # 传统 EDMD 升维函数
│   ├── polynomial.py
│   ├── rbf.py
│   ├── robot_lifting.py       # Platform 1 专用升维
│   └── threelink_lifting.py   # Platform 2 专用升维
├── ablation/                  # 消融实验
│   ├── positional_encoding.py # 共用位置编码
│   ├── models.py              # AblationModel + 10 工厂函数
│   ├── platform_configs.py    # PLATFORM_CONFIGS
│   └── encoders/              # 7 种消融编码器变体
└── utils/                     # 共享工具
    ├── config_loader.py
    ├── seed.py
    ├── checkpoint.py
    ├── device.py
    ├── data_prep.py
    ├── evaluation.py
    └── npz_inspector.py

scripts/                       # CLI 入口（薄层，调用包）
├── train_patchtst.py
├── test_patchtst.py
├── train_mlp_koopman.py
├── test_mlp_koopman.py
├── train_traditional_edmd.py
├── test_traditional_edmd.py
├── encoder_inference_matlab.py
├── ablation/
│   ├── train_ablation.py
│   ├── test_ablation.py
│   ├── plot_ablation_results.py
│   └── generate_report.py
├── debug/
│   ├── amplitude.py
│   ├── encoder_output.py
│   └── state_embedded.py
└── smoke_test.py              # 一键验证

deploy/                        # 部署包（独立于训练包）
├── export_assets.py
└── algorithms/
    ├── transformer_koopman_controller.py
    ├── configs/transformer_koopman_controller.json
    └── tk_assets/
        ├── transformer_koopman_model.py     # 部署侧独立模型副本
        ├── transformer_koopman_lifter.py     # 在线升维 + 历史缓冲
        └── model_assets/                     # 预训练资产
```

## GUI / Business Logic Separation

- 项目代码严格分离为：算法包 (src/) + CLI 脚本 (scripts/) + 部署包 (deploy/)
- GUI 仅出现在上位机（FlexibleArmControl34，不在本项目范围内）
- 部署控制器通过 `BaseAlgorithm` 接口与上位机 GUI 对接

## Key Design Decisions

- 部署包通过**独立模型副本**避免依赖训练包（tk_assets/transformer_koopman_model.py）
- 消融实验通过 **ABLATION_MODELS 工厂字典**统一调度，而非重复训练脚本
- 训练、测试、消融全部通过 YAML 配置驱动
