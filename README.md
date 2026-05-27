# PatchTST-Koopman

噪声鲁棒的 PatchTST-Koopman 非线性系统建模与分层 LQR 控制框架。

两个实验平台：
- **Platform 1** — 6-DOF Flexible Manipulator（柔性机械臂，state 6，control 3）
- **Platform 2** — 2-DOF Soft Robotic Arm（软体机器人，state 2，control 2）

## 目录结构

```
code-projectv2/
├── configs/                  # YAML 配置（platform1.yaml / platform2.yaml）
├── src/patchtst_koopman/     # 可 pip install 的 Python 包
│   ├── models/               # PatchTST 编码器 / Koopman 动力学 / 解码器 / MLP 基线
│   ├── data/                 # KoopmanDataset
│   ├── training/             # EDMD / MLP-Koopman / Traditional EDMD 训练器
│   ├── lifting/              # 传统 EDMD 升维函数（polynomial / rbf / robot / threelink）
│   ├── ablation/             # 7 种消融编码器 + AblationModel + PLATFORM_CONFIGS
│   └── utils/                # config_loader, seed, checkpoint, device, data_prep,
│                             # evaluation, npz_inspector
├── scripts/                  # 所有 CLI 入口
│   ├── train_patchtst.py / test_patchtst.py
│   ├── train_traditional_edmd.py / test_traditional_edmd.py
│   ├── train_mlp_koopman.py / test_mlp_koopman.py
│   ├── encoder_inference_matlab.py
│   ├── ablation/             # 消融实验入口
│   └── debug/                # 调试脚本
├── deploy/                   # 上位机部署包（Platform 2 控制器）
│   ├── README.md
│   ├── export_assets.py
│   └── algorithms/
│       ├── transformer_koopman_controller.py
│       ├── configs/transformer_koopman_controller.json
│       └── tk_assets/        # 模型与 lifter 依赖包
├── figures/                  # 论文配图生成脚本
│   ├── platform1/            # 平台 1 / 平台 2 跟踪/预测对比图
│   └── ablation/             # 消融实验柱状图 + LaTeX 表格生成
├── docs/                     # 文档（QUICKSTART, ABLATION_DESIGN, paper_notes, ...）
├── data/                     # 数据集（NPZ）— 自包含
├── results/                  # 训练产物（模型 / 日志 / 评估）— 跑训练后自动生成
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 安装

```bash
cd code-projectv2
pip install -e .
```

`-e` 表示开发模式，源码改动立即生效。`pip install -e .` 之后可以从任意目录 `import patchtst_koopman.xxx`，不需要任何 `sys.path` 修改。

## 数据准备

数据已经自包含在 `data/` 目录下（NPZ 文件包含 `x`, `u`, `t`, `trajectory_id` 四个字段）。

## 训练

```bash
# PatchTST-Koopman（主方法）
python scripts/train_patchtst.py --config configs/platform2.yaml

# 传统 EDMD 对照基线
python scripts/train_traditional_edmd.py --config configs/platform1.yaml

# MLP-Koopman 对照基线
python scripts/train_mlp_koopman.py --config configs/platform1.yaml
```

## 测试

```bash
python scripts/test_patchtst.py \
    --model_path results/models/<your_checkpoint>.pth \
    --config configs/platform2.yaml \
    --traj_idx 0
```

## 消融实验

```bash
# 跑指定平台的所有变体
python scripts/ablation/train_ablation.py --platform platform2 --variants all

# 单独跑某一组
python scripts/ablation/train_ablation.py --platform platform1 --variants module
python scripts/ablation/train_ablation.py --platform platform1 --variants hyperparameter

# 生成消融论文材料（CSV/LaTeX 表/PDF 柱状图）
python figures/ablation/generate_ablation_materials.py
```

## 上位机部署

详见 `deploy/README.md`。简单流程：

```bash
# 从训练好的 checkpoint 导出部署资产到 deploy/algorithms/tk_assets/model_assets/
python deploy/export_assets.py

# 将 deploy/algorithms/ 整个目录复制到 FlexibleArmControl34/algorithms/
```

## 快速验证（不训练）

```bash
# 探钉：包导入正常吗？
python -c "from patchtst_koopman.models.full_model import PatchTSTKoopmanModel; print('OK')"

# 命令行入口：inspect-npz 是否可用？
inspect-npz data/experiment_006/test.npz
```

## 配置说明

主要参数都在 `configs/platform{1,2}.yaml` 中。关键字段：

- `data.data_dir` — NPZ 数据路径（默认指向 `./data/experiment_00x`）
- `data.state_dim` / `data.control_dim` — 状态与控制维度
- `encoder.history_length` (P) / `encoder.patch_length` (p) / `encoder.latent_dim` (d)
- `training.method` — `edmd` 或 `end_to_end`
- `experiment.device` — `cuda` 或 `cpu`（CUDA 不可用时脚本会自动回退）

## 文档

- [docs/QUICKSTART.md](docs/QUICKSTART.md) — 5 分钟跑通
- [docs/ABLATION_DESIGN.md](docs/ABLATION_DESIGN.md) — 消融实验设计与变体清单
- [docs/TRADITIONAL_EDMD.md](docs/TRADITIONAL_EDMD.md) — 传统 EDMD 对照基线
- [docs/paper_notes.txt](docs/paper_notes.txt) — 论文要点速记
