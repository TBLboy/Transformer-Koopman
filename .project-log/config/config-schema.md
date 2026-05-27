# Config

## Config Schema

| Parameter | Type | Default | Source | Used By | Notes |
|---|---|---|---|---|---|
| data.data_dir | str | ./data/experiment_001 | YAML | data_prep.prepare_datasets | |
| data.state_dim | int | 2 | YAML | dataset.KoopmanDataset | Platform 1: 6, Platform 2: 2 |
| data.control_dim | int | 2 | YAML | dataset.KoopmanDataset | Platform 1: 3, Platform 2: 2 |
| encoder.history_length | int | 16 | YAML | dataset.KoopmanDataset | 滑动窗口大小 P |
| encoder.patch_length | int | 4 | YAML | patchtst_encoder | PatchTST patch 长度 p |
| encoder.latent_dim | int | 128 | YAML | patchtst_encoder | 潜在空间维度 d |
| encoder.num_heads | int | 4 | YAML | patchtst_encoder | Transformer 头数 |
| encoder.num_layers | int | 2 | YAML | patchtst_encoder | Transformer 层数 |
| encoder.dropout | float | 0.1 | YAML | patchtst_encoder | |
| training.method | str | edmd | YAML | edmd_trainer | "edmd" / "end_to_end" |
| training.edmd.pretrain.num_epochs | int | 500 | YAML | edmd_trainer | |
| training.edmd.pretrain.learning_rate | float | 1e-3 | YAML | edmd_trainer | |
| training.edmd.pretrain.batch_size | int | 64 | YAML | edmd_trainer | |
| training.edmd.pretrain.early_stopping | bool | true | YAML | edmd_trainer | |
| training.edmd.pretrain.patience | int | 50 | YAML | edmd_trainer | |
| training.edmd.compute.svd_clipping | bool | true | YAML | koopman_dynamics | 保证稳定性 |
| experiment.seed | int | 42 | YAML | seed.set_seed | 实验随机种子 |
| experiment.device | str | cuda | YAML + auto-fallback | device.resolve_device | 自动回退 CPU |
| experiment.save_dir | str | ./results | YAML | checkpoint | |
| experiment.name | str | ablation_platform2 | YAML | logging | |

## Config Files

- **platform1.yaml**: 六自由度柔性机械臂配置（state_dim=6, control_dim=3）
- **platform2.yaml**: 二自由度软体机器人配置（state_dim=2, control_dim=2）
