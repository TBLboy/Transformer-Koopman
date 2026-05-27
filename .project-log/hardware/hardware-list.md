# Hardware

## Platform 1 — 6-DOF Flexible Manipulator

- **Type**: 柔性机械臂
- **State**: 6-DOF (6 joint angles)
- **Control**: 3 个电机
- **Data source**: 已采集的 NPZ 文件 (experiment_00x)
- **Status**: 数据已有，模型已训练过（原项目结果）

## Platform 2 — 2-DOF Soft Robotic Arm

- **Type**: 软体机器人
- **State**: 2-DOF (x, y 位置)
- **Control**: 2 个通道（气动/线驱动）
- **Data source**: 已采集的 NPZ 文件 (experiment_00x)
- **Upper computer**: FlexibleArmControl34 (C#/Qt)
- **Controller**: TransformerKoopmanController (Python, PyTorch CPU)
- **Status**: 数据已有，有预训练模型资产（部署包自带）
