# Business Logic Constraints

## System Constraints

- 训练和评估在 Windows 10 上进行
- 使用 conda 环境（koopman/edmddl2），Python 3.8-3.9
- PyTorch 版本兼容性（torch >= 2.0.0 但 conda 环境可能只有 1.x）

## Hardware Constraints

- Platform 1: 6-DOF 柔性机械臂，state_dim=6, control_dim=3
- Platform 2: 2-DOF 软体机器人，state_dim=2, control_dim=2
- 上位机: FlexibleArmControl34 (C#/Qt)
- GPU: CUDA 可用时自动使用，不可用回退 CPU

## Software Constraints

- 部署包必须独立于训练包（上位机只装 PyTorch CPU，不装 patchtst_koopman）
- 所有配置通过 YAML 管理，不硬编码路径（scripts 入口除外，args 必需）

## Configuration Constraints

- config 参数类型必须与运行时类型一致
- 训练方法（edmd / end_to_end）影响全部训练流程

## Safety Constraints

- Koopman 矩阵必须做 SVD 裁剪保证谱半径 <= 1（控制器稳定性）
- 控制量有硬限制 u_limit

## Repository Constraints

- 原 `code_project/` 目录完全不动
- 新项目 `code-projectv2/` 可独立运行
