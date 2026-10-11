# Gate 0 — 代码审计（旧路线 + 新路线）

> 依据：`Temporary_Modeling_and_Control_Experiments_Plan.md` §1.2。
> 方法：只读静态审计 + 主 Agent 亲自 dump checkpoint 二进制。
> **验证标记**：`[主核]` = 主 Agent 亲自读取文件/运行脚本核实；`[子核]` = 由独立只读子 Agent 审计并经主 Agent 抽查；
> `[待确认]` = 无法核实，不得当作事实。

---

## 1. 索引表

### 1.1 旧路线（固定 A、B）— `代码部分/老版本/训练代码/`

| 文件 | 关键符号 | 行号 | 作用 |
|---|---|---|---|
| `configs/platform2.yaml` | — | 4–16 / 21–36 / 41–57 / 62–64 / 69–152 | Platform 2 全部超参与路径 |
| `src/patchtst_koopman/models/patchtst_encoder.py` | `PatchTSTEncoder.__init__` / `_create_patches` / `forward` | 22–64 / 66–70 / 72–82 | PatchTST 编码器，输出 `z=[x_t;h_t]` `[主核]` |
| `src/.../models/koopman_dynamics.py` | `KoopmanDynamics.__init__` / `forward` / `ensure_stability` | 15–22 / 24–25 / 27–32 | **固定** `A`、`B`；`z⁺=Az+Bu` `[主核]` |
| `src/.../models/linear_decoder.py` | `LinearDecoder.forward` | 13–19 | 固定解码 `x=z[:,:n]`（无参数）`[子核]` |
| `src/.../models/full_model.py` | `PatchTSTKoopmanModel.forward` | 21–24 | encoder→koopman→decoder `[主核]` |
| `src/.../models/rollout.py` | `predict_multi_step` / `roll_out_latent` | 20–41 / 43–61 | 多步 rollout（回填预测值）`[子核]` |
| `src/.../data/dataset.py` | `KoopmanDataset.__init__` / `_compute_valid_indices` / `__getitem__` | 25–98 / 100–117 / 142–165 | `(X_k,u_k)→x_{k+1}`，shift=1 `[主核]` |
| `src/.../training/edmd_trainer.py` | `_train_edmd` / `_pretrain_encoder_decoder` / `_compute_koopman_with_edmd` / `_save_checkpoint` | 216–244 / 246–313 / 425–467 / 558–563 | EDMD 三阶段 `[子核]` |
| `src/.../utils/koopman_solve.py` | `solve_koopman_operator` | 36–46 | 正则化最小二乘闭式解 `[子核]` |
| `src/.../utils/checkpoint.py` | `save_model` / `load_model` / `_map_legacy_keys` | 32–79 / 82–114 / 17–29 | checkpoint 读写 `[子核]` |
| `scripts/prepare_data.py` | `SPLIT_PLAN` / `build_split` | 37–47 / 84–138 | 原始数据→train/val/test.npz `[主核]` |
| `tests/*`（14 文件） | — | — | 迁移安全网 `[主核]`（已运行） |

### 1.2 新路线（scheduled A(c)）— `杂项/老版本/研究代码/`

| 文件 | 关键符号 | 行号 | 作用 |
|---|---|---|---|
| `gate_context_koopman.py` | `build_split` / `CtxKoopman` / `train_model` / `eval_rollout` | 26–42 / 45–77 / 80–100 / 103–127 | **新路线主实现**：fixed/A/B/AB 对照，r=3 `[主核]` |
| `gate14_stabilize.py` | `BudgetedCtxKoopman` / `build_seq_split` / `openloop_forward` / `train` / `rho_penalty` | 24–57 / 60–72 / 75–84 / 87–118 / 54–57 | 有界 A(c) + 谱半径惩罚 + 开环 scheduled 训练，r=2 `[主核]` |
| `gate13b_rsweep.py` | 主流程 | 17–19 | rank 扫描 → `A_r*.pt` `[子核]` |
| `gate14_directnn.py` | `DirectNN` | 21–31 | 独立 plant 基线网络（hidden=48）`[子核]` |
| `gate14c_control.py` / `gate14d_rti.py` | `mpc` / `run_closed_loop` / `rti_step` | 57–88 / 48–81 | 数据侧 MPC/RTI 代理 `[子核]` |
| `gate16_matched_oracle.py` / `gate16_diag_final.py` / `gate16_diag_fix.py` | 主流程 | 41 / 27–105 / 21–34 | 匹配 oracle、理论诊断（表 I / 图 3）`[子核]` |

### 1.3 部署与控制接口 — `代码部分/老版本/训练代码/deploy/`

| 文件 | 关键符号 | 行号 | 作用 |
|---|---|---|---|
| `algorithms/transformer_koopman_controller.py` | `load_model_and_design_lqr` / `design_lqr` / `calculate_control` | 77–93 / 95–140 / 142–167 | **LQR + 参考前馈**（非 MPC）`[子核]` |
| `algorithms/tk_assets/transformer_koopman_model.py` | `PatchTSTEncoder` / `KoopmanDynamics` / `PatchTSTKoopmanModel` | 41–95 / 98–108 / 120–131 | 部署侧独立镜像（固定 A、B）`[主核]` |
| `algorithms/tk_assets/transformer_koopman_lifter.py` | `StateHistoryBuffer` / `TransformerKoopmanLifter` | 14–41 / 44–129 | 在线升维 + 历史缓冲 `[子核]` |
| `algorithms/tk_assets/model_assets/platform2_full_model.pth` | — | — | 部署权重（**P=4, L=3**）`[主核]`（已 dump） |

---

## 2. 旧路线现状

### 2.1 模型与预测

- 单步：`PatchTSTKoopmanModel.forward = decoder(koopman(encoder(x_history), u_t))`（`full_model.py:21-24`）。
- 动力学：`z @ A.T + u @ B.T`，`A`、`B` 是**单一稠密 `nn.Parameter`**（`koopman_dynamics.py:21-25`）。**旧路线没有 `A0/B0` 命名，也没有任何调制**。
- 多步：`predict_multi_step` 每步把**预测**的 `x_next` 回填窗口（`rollout.py:36-40`）→ **不泄漏未来真实测量** ✓。
- 部署侧另有手工镜像实现同一逻辑（`tk_assets/transformer_koopman_model.py:120-131`）。

### 2.2 Encoder 与 latent 维度

- 输入 `[B, P, n]`；patch 化 `[B, P/p, p·n]`；`P % p != 0` 直接报错（`patchtst_encoder.py:26-30, 66-70`）。
- patch embedding `Linear(p·n → d_model)`（`:42`）；正弦位置编码相加（`:43`）；`TransformerEncoder(n_layers)`（`:45-52`）；readout `mean`（`:55-56`）；projection `Linear(d_model → d − n)`（`:39, 64`）。
- `forward` 返回 `cat([x_history[:,-1,:], h_t])`（`:73, 82`）→ **`z = [x_k; h_k]`**，故 **`d = n + n_psi`**（P2：`10 = 2 + 8`）✓ `[主核]`。
- 解码固定 `x = z[:, :n]` → **`C_x = [I_n | 0]`**，`C_x z = x_k` ✓ `[主核]`。

### 2.3 Context map

- **旧路线不存在 `C_φ`**（无 context 网络、无低秩调制）。`C_φ` 仅存在于新路线与理论验证脚本。

### 2.4 历史窗口与 shift

- `x_history = x[i-P+1 : i+1]`（**含当前 `x_i`**）、`u_t = u[i]`、`x_next = x[i+1]`（`dataset.py:144-146`）→ **shift = 1** ✓
- 合法性过滤：窗口与目标必须同属一条轨迹（`dataset.py:100-117`）。
- **`u_k` 只进转移，不进 context** ✓（旧路线无 context）。
- P2 配置未声明 `multi_step` → `N_L = 0`（`dataset.py:56-62`）→ **P2 实际只训练单步** `[子核]`。

### 2.5 训练阶段（`method: edmd`）

1. 阶段 0：随机初始化后直接闭式解 `A,B`（`edmd_trainer.py:219-225`）。
2. 阶段 1 预训练：500 epoch / bs 2048 / lr 1e-3 / patience 100（`platform2.yaml:78-83`）；损失 = `w₁·MSE(x̂,x⁺) + w₂·MSE(ẑ,z⁺) + w₃·MSE(encoder([x_{k+1:n-1};x̂]), z⁺)`，权重 1/1/1（`:86-89`）；`ReduceLROnPlateau(factor=0.5, patience=10)` **硬编码**（`edmd_trainer.py:267-273`）。
3. 阶段 2 闭式 EDMD：`K = solve(ZUᵀZU + λI, ZUᵀZ_next)ᵀ`，`λ = 1e-4`（`koopman_solve.py:36-46`、`platform2.yaml:93`）；含 NaN/Inf 守卫。
4. **稳定性约束在 P2 实际被跳过**：`compute.svd_clipping: false`（`platform2.yaml:94`）→ `A_stable = A`，`koopman.rho_max = 0.9999` **未被消费** `[子核]`。
5. `training.edmd.decoder.{method,regularization}`（`platform2.yaml:98-100`）在本模型下**疑似死配置**（decoder 无参数）`[待确认]`。

### 2.6 归一化

- **只在训练集拟合**（`dataset.py:71-75`），val/test 复用传入统计量（`:76-88`）；`prepare_datasets` 先建 train（`utils/data_prep.py:17-21`）。
- 公式 `(x−mean)/(std+1e-8)`，`np.std` ddof=0（`dataset.py:119-129`）。
- 存入 `checkpoint["normalization"] = {x_mean,x_std,u_mean,u_std}`（`checkpoint.py:63-70`）✓；**中途 checkpoint（`pretrain_best.pth`）不含**（`edmd_trainer.py:558-563`）`[主核]`（已 dump 验证：`pretrain_best.pth` normalization ABSENT）。

### 2.7 随机性与确定性

- `set_seed(42)`（`scripts/train_patchtst.py:76`、`platform2.yaml:6`）；`random/np/torch/cuda` 全播种。
- **P2 非确定性**：`deterministic: false`、`cudnn_benchmark: true`、`amp: true`、`allow_tf32: true`、`float32_matmul_precision: "high"`（`platform2.yaml:10-14`）→ **逐位复现不可得**。

### 2.8 Checkpoint 存取 `[主核]`（主 Agent 已 dump 二进制）

`save_model` 保存键（实测）：`model_state_dict`、`config`（含全部 YAML 段）、`koopman_A`、`koopman_B`、`spectral_radius`、`timestamp`、`model_info{state_dim,control_dim,latent_dim,history_length,patch_length}`、`normalization{...}`。
`load_model` 读 `config` 重建模型，`_map_legacy_keys` 兼容旧键名。

---

## 3. 新路线现状

### 3.1 `gate_context_koopman.py`（结构 gate，r=3）`[主核]`

- 硬编码 `REPO = ...\Transformer-Koopman\训练代码`（`:13`）、`OUT/STATE` 指向 `%TEMP%\opencode`（`:20-21`）。
- `build_split`（`:26-42`）：`XH = x[i-P+1:i+1]`（P 个测量）、`UH = u[i-P+1:i]`（**P−1 个过去输入**）、`UT = u[i]`（当前输入，**只入转移**）、`XN = x[i+1]`（`:38-40`）→ **shift=1，`u_k` 不入 context** ✓✓ 与理论一致。
- `CtxKoopman`（`:45-77`）：
  - `in_ctx = P·n + (P−1)·m`（`:51`）→ P=8,n=m=2 ⇒ **30** ✓ 与 `ctx.0.weight(64,30)` 算术吻合；
  - `ctx = Linear(30,64)+Tanh+Linear(64,16)+Tanh`（`:52`）→ `c ∈ R^16`；
  - `A0 = I + 0.01·randn`、`B0 = 0.1·randn`（`:53-54`）；
  - A 调制：`A = A0 + (Ua ⊙ g_a(c)) @ Vaᵀ`（`:69`）→ 即 **`A0 + U_A diag(γ_A(c)) V_Aᵀ`** ✓ 形式正确；
  - B 调制：`Bm = B0 + (Ub ⊙ g_b(c)) @ Vbᵀ`（`:71`）→ 形式正确，**但调度变量是 `c`（历史+过去输入）而非 `χ_k = C_x z_k`** ✗；
  - **`γ` = 裸线性输出 `Linear(c_dim, r)`：既无 softmax 也无 tanh**（`:57, 59, 69, 71`）✗；
  - 无列归一化、无 `δ_A` 界。
- 训练 `train_model`（`:80-100`）：**纯单步 MSE**（`:92`），无 rollout 目标、无谱半径惩罚、无 EDMD；A/B/AB 从 `fixed` 的 state_dict 初始化（`:151`）✓。
- 评估 `eval_rollout`（`:103-127`）：stride=8，`H_EVAL=[1,5,10,20]`；每步回填**预测**测量、喂入**真实未来输入**（`:120-123`）→ **不泄漏** ✓。
- 指标定义：`errs[h]` 存**每步 L2 范数**，再 `sqrt(mean(square(v)))`（`:126-127`）→ **不是逐通道 RMSE**，与其他模型的 RMSE 口径不同 ✗（影响统一协议）。

### 3.2 `gate14_stabilize.py`（有界 A(c) + 谱惩罚 + 开环 scheduled 训练，r=2）`[主核]`

- `BudgetedCtxKoopman`（`:24-57`）：`pi = softmax(s, 0)`（`:40`，**softmax 作用在常量参数 `s` 上，与 `c` 无关**）；`a = delta_A · pi ⊙ tanh(g(c))`（`:41`，`delta_A = 0.07`）；`U`、`V` **列归一化**（`:42-43`）；`dA = U diag(a) Vᵀ`（`:44`）→ `‖dA‖₂ ≤ δ_A` ✓；`A = A0 + dA`（`:45`）；**`Bm = B0` 固定，无 B 调制**（`:46`）✗。
- `rho_penalty = mean(relu(ρ(A) − ρ_max)²)`（`:54-57`）；`train` 中 `loss += lam·rho_penalty`（`:107`）。
- `openloop_forward`（`:75-84`）每步用解码值回填 `xh`/`uh` 并重算 `A` → **scheduled 传播** ✓；`train(mode="openloop")` 用 H=20 rollout MSE（`:104-105`）✓。
- `eval_prop`（`:121-151`）：`sched=False` 冻结 A,B；`sched=True` 逐步重算；回填预测测量 ✓。

### 3.3 检查点 ↔ 脚本对应 `[主核]`（形状已 dump 核对）

| 检查点 | 生成脚本 | P / d / r / 其他 |
|---|---|---|
| `fixed.pt`, `A.pt`, `B.pt`, `AB.pt`（+`_s1`） | `gate_context_koopman.py:146,152` | P=8, d=10, **r=3**, c_dim=16, d_model=16, L=1, p=2 |
| `A_r1/r2/r3/r5.pt` | `gate13b_rsweep.py:17-19` | 同上，r ∈ {1,2,3,5} |
| `A_stab_{one_step,openloop}_lam{0.0,10.0}_rho0.99.pt` | `gate14_stabilize.py:207-208` | P=8, d=10, **r=2**, δ_A=0.07 |
| `plant_dnn.pt` | `gate16_matched_oracle.py:41` | `DirectNN(hidden=48)` |

- 新路线检查点保存**裸 state_dict**，**不含 config / normalization / 谱半径**（`:146/:152`、`:208`）→ 超参只能靠脚本常量推断。
- 实测 `A_stab_openloop_lam0.0_rho0.99.pt` 的 `rho_median = 1.02985 > 1`（`实验结果/gate14_result.json:175-176`）`[主核]` → **被冻结的预测器不是稳定矩阵**；`lam10.0` 版本为 0.9888 ≤ 1（`:148-149`）→ 惩罚生效但最终冻结用了 `lam=0`。

---

## 4. 与新理论的差异清单

理论基准：`杂项/新版本/Transformer_Scheduled_Koopman_MPC_Research_Plan.md` + DEC-079。

| # | 理论要求 | 代码实际 | 证据 | 影响 | 核 |
|---|---|---|---|---|---|
| D1 | `A(c)=A0+U_A diag(γ_A)V_Aᵀ` | **旧路线完全没有 A 调制**（单一稠密 A） | `koopman_dynamics.py:21-25` | 旧路线不实现新模型 | 主 |
| D2 | `γ_A = g_A·softmax·tanh` | **r=3 实现：裸线性输出，无 softmax/tanh** | `gate_context_koopman.py:57,69` | 有界性命题在该实现下不成立 | 主 |
| D3 | softmax 应为 `c` 的函数 | **r=2 实现：`softmax(s)`，`s` 是常量参数** | `gate14_stabilize.py:40-41` | 「softmax 混合随调度变化」在训练模型里不存在 | 主 |
| D4 | `B(χ)=B0+U_B diag(γ_B(χ))V_Bᵀ` | **被冻结的 r=2 模型无 B 调制**（`Bm=B0`） | `gate14_stabilize.py:46`；`env_tX0-dec024.json`（"fixed B/C"） | 新理论核心动机之一在选定模型里缺失 | 主/子 |
| D5 | `χ_k = C_x z_k` | **平台训练实现中无 `C_x`/`χ`**；B 的调度变量是 context `c`。（`validate_theory.py:39,122-125` 的合成验证脚本里有 `C_x=[I_n\|0]`、`χ=C_x z`） | grep `杂项/老版本/研究代码` 无 `C_x`/`χ` 匹配；`gate_context_koopman.py:71`；`validate_theory.py:39,122-125` | 理论的 measurement-dependent 分支在平台实现中无对应代码 | 主 |
| D6 | `C_φ` 形式在阶段一未固定 | 代码固定为 `Linear(30,64)+Tanh+Linear(64,16)+Tanh`；合成验证用**单层 tanh**（又一种） | `gate_context_koopman.py:52`；`validate_theory.py:87-88` | `L_φ` 取值依赖所选形式 | 主/子 |
| D7 | rollout-aware scheduled 训练 | 仅 `gate14_stabilize.py` 有；r=3 脚本是纯单步 MSE | `gate14_stabilize.py:104-107` vs `gate_context_koopman.py:92` | 论文泛称会失准 | 主 |
| D8 | 稳定性/谱约束 | r=2 有惩罚，但**最终冻结权重用 `lam=0`**，实测 ρ_median=1.0299>1 | `gate14_stabilize.py:107`；`gate14_result.json:175-176` | 不得声称 ρ<1 / 收缩 | 主 |
| D9 | 冻结 LTV-MPC 为凸 QP，Hessian ⪰0 | 数据侧用**通用非线性求解器**（SLSQP / L-BFGS-B），未构造/验证 Hessian | `gate14c_control.py:57-71`；`gate14d_rti.py:29-45` | 措辞须限定为「同一代价的通用求解」 | 子 |
| D10 | 次优性 `0 ≤ J_full(u^fr)−J_full(u*) ≤ 2ε_J` | 代码无该不等式验证 | `validate_theory.py:315-352` | 该命题无代码验证 | 子 |
| D11 | 部署栈应反映论文方法 | 部署栈 = **旧路线固定 A/B + LQR**，非 RTI-MPC | `transformer_koopman_controller.py:95-167`；`env_tZ10-audit.json:36-37` | 部署与论文不同源 | 主/子 |
| D12 | 指标口径统一 | r=3 脚本用「每步 L2 范数的 RMS」，非逐通道 RMSE | `gate_context_koopman.py:126-127` | Gate 1 必须统一口径 | 主 |

---

## 5. 部署与控制接口

- **部署控制器 = 升维 + 离散 LQR + 参考前馈 + 幅值裁剪，不是 MPC**：`design_lqr`（`transformer_koopman_controller.py:95-140`，优先 `control.dlqr`，失败回退 2000 次 Riccati 迭代，再失败 `K=0`）；`calculate_control` 输出 `u = −K·e_z + ff_gain·B⁺(z_ref⁺ − A z_ref)`，唯一约束是 `np.clip(u, −u_limit, +u_limit)`，`u_limit=100`（`:142-167`）。
- 输入 `current_pos / current_step / trajectory_sequence`；输出 `(delta_x, delta_y)`，单位 = 电机脉冲数（`软控逻辑.txt:326`）。上位机周期默认 `Ts = 0.2 s`（`软控逻辑.txt:214, 570`）。
- **不主张任何实时截止时间满足。**
- 数据侧控制实验（`gate14c_control.py` oracle 闭环、`gate14d_rti.py` RTI）**不是部署控制器**。

---

## 6. 数据来源与训练数据溯源（主 Agent 亲测，Gate 0 最重要的发现）

主 Agent 直接 dump 了全部旧路线 checkpoint 的二进制，并与两份数据逐项对比：

| 事实 | 证据 |
|---|---|
| 全部旧路线 checkpoint 内嵌 `data_dir = ./data/experiment_006` | `[主核]` dump：`platform2_full_model.pth`、`model_best.pth`、`model_2026*.pth` 全部如此 |
| 旧路线归一化常数 = `x_mean=[0.345229,0.423334]`、`x_std=[3.497781,3.20667]` | `[主核]` dump |
| `code-projectv2/data/experiment_006/train.npz` = **24150 样本 / 49 轨迹 / 长度 {150,500}**，其 `x_mean/x_std` 与上述**在浮点精度内一致**（`0.423332` vs `0.423334`，末位差异源于 float32/float64 存储） | `[主核]` 亲算 |
| 当前 `数据备份/软体平台数据/处理后的数据/train.npz` = **21000 样本 / 70 轨迹 / 长度 {300}**，`x_mean=[-0.696318,0.048996]`、`x_std=[3.243583,3.415089]` | `[主核]` 亲算 |
| **两者不是同一份数据** | 样本数 24150 vs 21000、轨迹数 49 vs 70、轨迹长度 {150,500} vs {300}、统计量不同 |

**结论**：
1. **旧路线的历史 checkpoint 不是用当前 `软体平台数据` 训练的**，因此**不能直接当作 M4 基线**，其历史指标（`main.md:43` 的 0.474；`results_*.json` 的 `auto_test_rmse` 1.14–2.59）**都指 experiment_006**，与当前数据不可比。
2. 新路线脚本的数据路径（`cfg["data"]["data_dir"] = "../数据备份/软体平台数据/处理后的数据"` 相对硬编码 `REPO`）解析到**当前** `软体平台数据`；其 checkpoint 不存归一化，故「新路线模型确实用当前数据训练」**在 Gate 1 需以重训或重算验证**（`[待确认]`）。
3. **Gate 1 必须重训旧模型（M4）与新模型（M5）**，不能复用任何历史 checkpoint 作为公平基线。

---

## 7. 迁移导致的工程缺陷（可运行性）

1. **旧路线数据路径在 2026-10-10 目录重构后失效** `[主核]`（已运行 pytest 验证）：
   - `configs/platform2.yaml:23` 的 `data_dir: "../数据备份/..."` 相对 `训练代码/` 解析 → `代码部分/老版本/数据备份/...`，**该目录不存在**；
   - `conftest.py` 的 `REPO_ROOT = PROJECT_DIR.parent` 现在指向 `代码部分/老版本`，`test_ascii_identifiers.py:46-54` 的目录钉因此失配；
   - **实测：`python -m pytest tests -q` → 41 failed, 179 passed, 2 skipped, 1 xfailed**（5.07 s）。41 个失败**全部**源于上述相对路径失效（`test_data_contract.py` 38 项 + `test_config_contract.py` 2 项 + `test_ascii_identifiers.py` 1 项），**无一个是逻辑错误**。
2. **新路线脚本硬编码已失效路径**：`gate_context_koopman.py:13` 的 `REPO = ...\Transformer-Koopman\训练代码`（重构后为 `代码部分/老版本/训练代码`）→ `sys.path.insert(REPO/src)` 失效；同类硬编码约 32 处 `[子核]`。
3. **新路线脚本依赖 `%TEMP%\opencode` 作为模块搜索路径与 checkpoint 目录**（`gate14_stabilize.py:13,20` 等）→ 临时目录被清理后不可运行。
4. `deploy/.../platform2_metadata.json:2` 保留旧机器绝对路径（`C:\Users\Windows\Desktop\论文4\...`），被 `test_no_hardcoded_paths.py` 作为唯一白名单例外登记 `[子核]`。

---

## 8. 待确认问题

| # | 问题 | 影响 |
|---|---|---|
| Q1 | 新路线 checkpoint 是否确实用当前 `软体平台数据` 训练（无归一化可查） | 决定 M5 可否复用历史权重 |
| Q2 | `A_stab_one_step.pt` / `A_stab_openloop.pt`（无 lam/rho 后缀）由哪一版脚本产生 | 仅历史追溯 |
| Q3 | `training.edmd.decoder.*` 是否为死配置 | 无功能影响 |
| Q4 | `validate_plant_cartpole.py` 是否已执行、其产物是否为本机当前版本 | TASK-043 复核已完成，此处仅确认 |
| Q5 | 数据物理单位与来源（真实/仿真） | 见 `data_audit.md` §8 |
| Q6 | `u_limit = 100` 是否为权威输入约束 | 见 `data_audit.md` §8 |

---

## 9. 结论与对 Gate 0 的影响

1. **两条路线在代码上完全分离**：正式路径 `代码部分/老版本/训练代码/`（`代码部分/新版本/` 为空）只实现**固定 A、B 的 EDMD 路线**；scheduled `A(c)` 与任何 B 调制**只存在于** `杂项/老版本/研究代码/`（`杂项/老版本/README.md:41` 明确为该路线唯一实现）。
2. **新理论没有单一的平台训练实现**：`A(c)` 的 softmax·tanh 形式、`B(χ)` 且 `χ=C_x z`、开环 scheduled 训练，**从未同时出现在同一平台训练脚本**。最接近理论形式的是合成验证脚本 `validate_theory.py:42-46,71-84,122-125`（满足三条模型**形式**，但为随机参数、非 P2 数据、不训练）。
3. **旧模型不可直接复现**：历史 checkpoint 训练于另一份数据（§6），且旧路线数据路径已因重构失效（§7）→ **Gate 1 必须重训**。
4. **P=8 是权威配置**（已被项目自身记录裁定）：`记录载荷/env_tZ10-audit.json`（`PHASE2-CONFIG-AUDIT-001`）明确「论文用 P=8；`deploy/.../platform2_full_model.pth`（P=4, L=3）是旧项目导入的作废遗留物，仓库内不存在 P=8 最终模型 checkpoint」`[主核]`。这与本报告 §2.8/§6 的二进制 dump 一致。
5. **不得作为事实**：任何来自 `.pt` 内部的未 dump 断言、「softmax 随调度变化」的机制断言、「P=4 部署模型代表本方法」的表述。
