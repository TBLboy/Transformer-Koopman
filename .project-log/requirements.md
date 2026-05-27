# Requirements

## Project Summary

- **Goal**: 噪声鲁棒的 PatchTST-Koopman 非线性系统建模与分层 LQR 控制框架，用于柔性机械臂控制。产出学术论文。
- **Users / Operators**: 论文作者（研究生/研究员），上位机操作员（实验室环境）
- **Current stage**: 代码重构完成（code-projectv2/），可独立运行；论文撰写进行中

## Requirements

### 功能需求

1. PatchTST 编码器 + Koopman 动力学模型 + Linear 解码器（主方法）
2. 两种训练方法：EDMD（两步法）和 End-to-End（联合训练）
3. MLP-Koopman 对照基线
4. Traditional EDMD 对照基线（多项式 / RBF / 机械臂专用升维函数）
5. 7 种消融变体（no_patch, no_attention, no_positional, window, patch_size, readout, pure_feature）
6. 部署到上位机 FlexibleArmControl34 的控制器包（TransformerKoopmanController）
7. 论文配图生成脚本（轨迹对比图、消融柱状图、LaTeX 表格）

### 非功能需求

- 代码可重新训练出论文结果
- 部署包不依赖训练包（上位机无需安装 patchtst_koopman）
- 消融实验可复现

## 任务范围

- **In scope**: 两个实验平台（Platform 1: 6-DOF 柔性机械臂 / Platform 2: 2-DOF 软体机器人）
- **Out of scope**: 实时控制系统的硬件在环测试；上位机 GUI 开发

## 约束

- 不能用第三方 Koopman 库（自制实现）
- 原 code_project/ 完全不动

## 验收标准

- `scripts/smoke_test.py` 全部通过
- 所有模型可导入、训练 1 epoch 不报错
- 部署控制器可加载预训练资产
- 消融所有变体可训练

## 决策

- 重构为正规 Python 包（pyproject.toml + src/patchtst_koopman/）
- 消融模型从 nn.Module()+lambda 改为正规子类
- 数据自包含（data/ 从原项目复制）
- 中文目录全部英文化
