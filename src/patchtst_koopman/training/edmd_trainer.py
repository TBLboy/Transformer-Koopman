"""
EDMD训练器
"""
import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from tqdm import tqdm
import numpy as np


class EDMDTrainer:
    """
    EDMD训练方法

    流程：
        阶段1：预训练编码器和降维矩阵（端到端）
        阶段2：固定编码器，用EDMD计算Koopman矩阵
    """

    def __init__(self, model, config):
        self.model = model
        self.config = config
        self.device = config['experiment']['device']
        self.edmd_config = config['training']['edmd']
        exp = config.get('experiment', {})
        self.use_amp = (
            self.device == 'cuda'
            and exp.get('amp', True)
            and exp.get('precision', 'float32') == 'float32'
        )
        self.scaler = torch.amp.GradScaler('cuda', enabled=self.use_amp)

    def _loader_kwargs(self, shuffle=False, batch_size=256):
        """Create DataLoader kwargs with CUDA-friendly defaults."""
        training = self.config['training']
        num_workers = training.get('num_workers', 0)
        kwargs = {
            'batch_size': batch_size,
            'shuffle': shuffle,
            'num_workers': num_workers,
        }
        if self.device == 'cuda':
            kwargs['pin_memory'] = True
            if num_workers > 0:
                kwargs['persistent_workers'] = True
                kwargs['prefetch_factor'] = training.get('prefetch_factor', 4)
        return kwargs

    def _to_device(self, tensor):
        return tensor.to(self.device, non_blocking=(self.device == 'cuda'))

    def train(self, train_dataset, val_dataset):
        """统一训练入口：根据 ``config.training.method`` 自动调度 EDMD 或 End-to-End。"""
        method = self.config["training"]["method"]

        if method == "edmd":
            self._train_edmd(train_dataset, val_dataset)
        elif method == "end_to_end":
            self._train_end_to_end(train_dataset, val_dataset)
        else:
            raise ValueError(f"Unknown training method: {method}")

    def _train_end_to_end(self, train_dataset, val_dataset):
        """端到端训练：所有参数全程梯度下降，无 EDMD 闭式求解阶段。"""
        e2e = self.config["training"]["end_to_end"]
        precision = self.config["experiment"].get("precision", "float32")
        if precision == "float64":
            self.model = self.model.double()
        else:
            self.model = self.model.float()

        train_loader = DataLoader(
            train_dataset,
            **self._loader_kwargs(
                shuffle=True, batch_size=e2e["batch_size"]
            )
        )
        val_loader = DataLoader(
            val_dataset,
            **self._loader_kwargs(batch_size=e2e["batch_size"]),
        )

        scheduler_type = e2e.get("scheduler", "reduce_on_plateau")
        if scheduler_type == "step":
            sp = e2e.get("scheduler_params", {})
            scheduler = torch.optim.lr_scheduler.StepLR(
                optimizer,
                step_size=sp.get("step_size", 100),
                gamma=sp.get("gamma", 0.9),
            )
        else:
            # default: ReduceLROnPlateau (matches MLP end-to-end / EDMD pretrain)
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode="min", factor=0.5, patience=10, min_lr=1e-6
            )

        loss_weights = e2e.get("loss_weights", {"prediction": 1.0, "stability": 0.0, "regularization": 0.0})
        w_pred = loss_weights.get("prediction", 1.0)
        w_stab = loss_weights.get("stability", 0.0)
        w_reg = loss_weights.get("regularization", 0.0)

        best_val_loss = float("inf")
        patience_counter = 0
        prev_lr = e2e["learning_rate"]
        n_features = self.config["data"]["state_dim"]

        print("\n" + "=" * 60)
        print("端到端训练 PatchTST-Koopman")
        print("=" * 60)

        for epoch in range(e2e["num_epochs"]):
            # ── 训练 ──────────────────────────────────────────────
            self.model.train()
            total_loss = 0

            for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}"):
                x_history = self._to_device(batch["x_history"])
                u_t = self._to_device(batch["u_t"])
                x_next = self._to_device(batch["x_next"])

                optimizer.zero_grad(set_to_none=True)

                if self.use_amp:
                    with torch.amp.autocast("cuda"):
                        x_pred = self.model(x_history, u_t)
                        loss = w_pred * F.mse_loss(x_pred, x_next)
                        if w_stab > 0:
                            A = self.model.koopman.A
                            I = torch.eye(A.size(-1), device=A.device, dtype=A.dtype)
                            loss = loss + w_stab * F.mse_loss(A.T @ A, I)
                        if w_reg > 0:
                            reg_penalty = sum(p.pow(2).sum() for p in self.model.parameters())
                            loss = loss + w_reg * reg_penalty
                    self.scaler.scale(loss).backward()
                    if e2e.get("grad_clip", 0) > 0:
                        self.scaler.unscale_(optimizer)
                        torch.nn.utils.clip_grad_norm_(
                            self.model.parameters(), e2e["grad_clip"]
                        )
                    self.scaler.step(optimizer)
                    self.scaler.update()
                else:
                    x_pred = self.model(x_history, u_t)
                    loss = w_pred * F.mse_loss(x_pred, x_next)
                    if w_stab > 0:
                        A = self.model.koopman.A
                        I = torch.eye(A.size(-1), device=A.device, dtype=A.dtype)
                        loss = loss + w_stab * F.mse_loss(A.T @ A, I)
                    if w_reg > 0:
                        reg_penalty = sum(p.pow(2).sum() for p in self.model.parameters())
                        loss = loss + w_reg * reg_penalty
                    loss.backward()
                    if e2e.get("grad_clip", 0) > 0:
                        torch.nn.utils.clip_grad_norm_(
                            self.model.parameters(), e2e["grad_clip"]
                        )
                    optimizer.step()

                total_loss += loss.item()

            # ── 可选的 SVD 投影 ──────────────────────────────────
            svd_proj = e2e.get("svd_projection", {})
            if svd_proj.get("enabled", False) and epoch % svd_proj.get("frequency", 1) == 0:
                self.model.koopman.ensure_stability()

            train_loss = total_loss / len(train_loader)

            # ── 验证 ──────────────────────────────────────────────
            val_loss = self._validate(val_loader)

            # ── 学习率调整 ────────────────────────────────────────
            if scheduler_type == "step":
                scheduler.step()
            else:
                scheduler.step(val_loss)

            current_lr = optimizer.param_groups[0]["lr"]
            if current_lr != prev_lr:
                print(f"  >>> 学习率降低: {prev_lr:.2e} -> {current_lr:.2e}")
                prev_lr = current_lr

            print(f"Epoch {epoch+1}/{e2e['num_epochs']}: "
                  f"Train={train_loss:.6f}  Val={val_loss:.6f}  LR={current_lr:.2e}")

            # ── 早停 ──────────────────────────────────────────────
            if e2e["early_stopping"]:
                if val_loss < best_val_loss - e2e["min_delta"]:
                    best_val_loss = val_loss
                    patience_counter = 0
                    self._save_checkpoint("e2e_best.pth")
                else:
                    patience_counter += 1
                if patience_counter >= e2e["patience"]:
                    print(f"早停触发 (patience={patience_counter})")
                    self._load_checkpoint("e2e_best.pth")
                    break

        print(f"端到端训练完成，最佳验证损失: {best_val_loss:.6f}")

    def _train_edmd(self, train_dataset, val_dataset):
        """EDMD 三阶段训练流程。"""

        # ========== 阶段0：初始EDMD计算（初始化Koopman矩阵） ==========
        print("\n" + "=" * 60)
        print("阶段0：初始EDMD计算（初始化Koopman矩阵）")
        print("=" * 60)
        print("使用随机初始化的编码器计算初始Koopman矩阵...")
        self._compute_koopman_with_edmd(train_dataset)
        print("初始Koopman矩阵已设置")

        # ========== 阶段1：预训练编码器和降维矩阵 ==========
        if self.edmd_config['pretrain']['enabled']:
            print("\n" + "=" * 60)
            print("阶段1：预训练编码器和降维矩阵")
            print("=" * 60)
            print("使用初始化的Koopman矩阵进行端到端训练...")
            self._pretrain_encoder_decoder(train_dataset, val_dataset)
        else:
            print("\n跳过预训练阶段")

        # ========== 阶段2：最终EDMD优化Koopman矩阵 ==========
        print("\n" + "=" * 60)
        print("阶段2：最终EDMD优化Koopman矩阵")
        print("=" * 60)
        print("固定编码器，重新计算最优Koopman矩阵...")
        self._compute_koopman_with_edmd(train_dataset)

        print("\nEDMD训练完成！")

    def _pretrain_encoder_decoder(self, train_dataset, val_dataset):
        """
        阶段1：预训练编码器和降维矩阵
        """
        # 创建数据加载器
        train_loader = DataLoader(
            train_dataset,
            **self._loader_kwargs(
                shuffle=True,
                batch_size=self.edmd_config['pretrain']['batch_size']
            )
        )
        val_loader = DataLoader(
            val_dataset,
            **self._loader_kwargs(
                batch_size=self.edmd_config['pretrain'].get('batch_size', 256)
            ),
        )

        # 优化器（不包含解码器参数，因为解码器是固定的）
        optimizer = torch.optim.Adam([
            {'params': self.model.encoder.parameters()},
            {'params': self.model.koopman.parameters()}
        ], lr=self.edmd_config['pretrain']['learning_rate'])

        # 学习率调度器（根据验证损失自适应调整）
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode='min',
            factor=0.5,        # 学习率减半
            patience=10,       # 10个epoch验证损失不下降就降低学习率
            min_lr=1e-6        # 最小学习率
        )

        # 训练循环
        best_val_loss = float('inf')
        patience_counter = 0
        prev_lr = self.edmd_config['pretrain']['learning_rate']

        print("注意：使用状态嵌入式编码器，解码器固定，不使用重建损失")

        for epoch in range(self.edmd_config['pretrain']['num_epochs']):
            # 训练
            train_loss = self._pretrain_epoch(train_loader, optimizer, train_dataset)

            # 验证
            val_loss = self._validate(val_loader)

            # 学习率调整
            scheduler.step(val_loss)
            current_lr = optimizer.param_groups[0]['lr']

            # 检测学习率变化
            if current_lr != prev_lr:
                print(f"  >>> 学习率降低: {prev_lr:.2e} -> {current_lr:.2e}")
                prev_lr = current_lr

            # 打印训练信息
            print(f"Epoch {epoch+1}/{self.edmd_config['pretrain']['num_epochs']}: "
                  f"Train Loss = {train_loss:.6f}, Val Loss = {val_loss:.6f}, LR = {current_lr:.2e}")

            # 早停检查
            if self.edmd_config['pretrain']['early_stopping']:
                if val_loss < best_val_loss - self.edmd_config['pretrain']['min_delta']:
                    best_val_loss = val_loss
                    patience_counter = 0
                    # 保存最佳模型
                    self._save_checkpoint('pretrain_best.pth')
                else:
                    patience_counter += 1

                if patience_counter >= self.edmd_config['pretrain']['patience']:
                    print(f"早停触发（patience={patience_counter}）")
                    # 加载最佳模型
                    self._load_checkpoint('pretrain_best.pth')
                    break

        print(f"预训练完成，最佳验证损失: {best_val_loss:.6f}")

    def _pretrain_epoch(self, train_loader, optimizer, train_dataset=None):
        """预训练的单个epoch（含可选的H步自回归预测损失）。

        当 ``config.training.edmd.pretrain.loss_weights.rollout > 0`` 且
        ``rollout.horizon``  > 1 时，``L_pred`` 变为 H 步自回归预测 MSE。
        H=1 时等价于原来的单步预测损失。
        """
        self.model.train()
        total_loss = 0
        loss_pred_total = 0
        loss_latent_total = 0
        loss_consistency_total = 0

        # ── 获取损失权重 ────────────────────────────────────────────
        loss_weights = self.edmd_config['pretrain'].get('loss_weights',
                                                        {'prediction': 1.0,
                                                         'latent': 0.5,
                                                         'consistency': 0.5})

        rollout_cfg = self.edmd_config.get('rollout', {})
        horizon = int(rollout_cfg.get('horizon', 1))
        gamma = float(rollout_cfg.get('gamma', 1.0))
        use_rollout = (horizon > 1)

        for batch in tqdm(train_loader, desc="预训练"):
            x_history = self._to_device(batch['x_history'])
            u_t = self._to_device(batch['u_t'])
            x_next = self._to_device(batch['x_next'])

            optimizer.zero_grad(set_to_none=True)

            def _compute_losses():
                x_history_next = torch.cat([x_history[:, 1:, :],
                                           x_next.unsqueeze(1)], dim=1)

                z_t = self.model.encoder(x_history)
                z_pred = self.model.koopman(z_t, u_t)
                x_pred = self.model.decoder(z_pred)

                if use_rollout and train_dataset is not None:
                    raw_indices = batch['_raw_idx'].numpy()
                    u_seq, x_seq, mask = self._gather_multi_step(
                        train_dataset, raw_indices, horizon
                    )
                    u_seq = self._to_device(u_seq)
                    x_seq = self._to_device(x_seq)
                    mask = self._to_device(mask)

                    x_pred_seq = self.model.predict_multi_step(x_history, u_seq)
                    per_step_se = ((x_pred_seq - x_seq) ** 2).mean(dim=2)
                    step_weights = gamma ** torch.arange(horizon, device=mask.device)
                    weighted_se = per_step_se * step_weights
                    masked_se = weighted_se * mask
                    L_pred = masked_se.sum() / (mask.sum() + 1e-8)
                else:
                    L_pred = F.mse_loss(x_pred, x_next)

                z_true = self.model.encoder(x_history_next)
                L_latent = F.mse_loss(z_pred, z_true)

                x_history_pred_next = torch.cat(
                    [x_history[:, 1:, :], x_pred.unsqueeze(1)], dim=1
                )
                z_from_pred = self.model.encoder(x_history_pred_next)
                L_consistency = F.mse_loss(z_from_pred, z_true)

                loss = (loss_weights['prediction'] * L_pred +
                        loss_weights['latent'] * L_latent +
                        loss_weights['consistency'] * L_consistency)
                return loss, L_pred, L_latent, L_consistency

            if self.use_amp:
                with torch.amp.autocast("cuda"):
                    loss, L_pred, L_latent, L_consistency = _compute_losses()
                self.scaler.scale(loss).backward()
                self.scaler.step(optimizer)
                self.scaler.update()
            else:
                loss, L_pred, L_latent, L_consistency = _compute_losses()
                loss.backward()
                optimizer.step()

            total_loss += loss.item()
            loss_pred_total += L_pred.item()
            loss_latent_total += L_latent.item()
            loss_consistency_total += L_consistency.item()

        avg_loss = total_loss / len(train_loader)
        avg_pred = loss_pred_total / len(train_loader)
        avg_latent = loss_latent_total / len(train_loader)
        avg_consistency = loss_consistency_total / len(train_loader)

        # 打印各项损失
        print(f"  [损失分解] Pred: {avg_pred:.6f}, Latent: {avg_latent:.6f}, Consistency: {avg_consistency:.6f}")

        return avg_loss

    # ─────────────────────────────────────────────────────────────────
    #  Helper: gather multi-step u / x targets from the raw dataset
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _gather_multi_step(dataset, raw_indices, horizon):
        """For each raw position ``i``, collect ``horizon``-step targets.

        Returns:
            u_seq  ``[B, H, m]``
            x_seq  ``[B, H, n]``
            mask   ``[B, H]``  -- 1 = valid step, 0 = crossed trajectory boundary
        """
        raw_indices = np.asarray(raw_indices, dtype=np.int64)
        n = dataset.n
        m = dataset.m
        x_raw = dataset.x
        u_raw = dataset.u
        traj_id = dataset.trajectory_id
        n_samples = len(x_raw)

        h_offsets_u = np.arange(horizon, dtype=np.int64)
        h_offsets_x = np.arange(1, horizon + 1, dtype=np.int64)
        pos_u = raw_indices[:, None] + h_offsets_u[None, :]
        pos_x = raw_indices[:, None] + h_offsets_x[None, :]

        pos_u_safe = np.clip(pos_u, 0, n_samples - 1)
        pos_x_safe = np.clip(pos_x, 0, n_samples - 1)
        ref_traj = traj_id[raw_indices][:, None]

        valid_u = (pos_u < n_samples) & (traj_id[pos_u_safe] == ref_traj)
        valid_x = (pos_x < n_samples) & (traj_id[pos_x_safe] == ref_traj)
        step_mask = (valid_u & valid_x).astype(np.float32)
        mask_seq = np.cumprod(step_mask, axis=1)

        u_seq = u_raw[pos_u_safe]
        x_seq = x_raw[pos_x_safe]

        return (
            torch.from_numpy(u_seq.astype(np.float32)),
            torch.from_numpy(x_seq.astype(np.float32)),
            torch.from_numpy(mask_seq.astype(np.float32)),
        )

    def _compute_koopman_with_edmd(self, train_dataset):
        """
        阶段2：使用EDMD计算Koopman矩阵
        """
        # 确保模型精度正确（防止加载checkpoint后精度改变）
        precision = self.config['experiment'].get('precision', 'float32')
        if precision == 'float64':
            self.model = self.model.double()
        else:
            self.model = self.model.float()

        print("步骤1：编码所有训练数据...")
        Z, Z_next, U = self._encode_dataset(train_dataset)

        print(f"  编码完成：{Z.shape[0]} 个样本")
        print(f"  潜在维度：{Z.shape[1]}")
        print(f"  控制维度：{U.shape[1]}")

        print("\n步骤2：计算EDMD闭式解...")
        A, B = self._compute_edmd(Z, Z_next, U)

        print(f"  Koopman矩阵A: {A.shape}")
        print(f"  控制矩阵B: {B.shape}")

        # 检查稳定性
        eigenvalues = np.linalg.eigvals(A)
        spectral_radius = np.max(np.abs(eigenvalues))
        print(f"  谱半径（SVD前）: {spectral_radius:.4f}")

        print("\n步骤3：SVD后处理...")
        if self.edmd_config['compute']['svd_clipping']:
            A_stable = self._apply_svd_clipping(A)
            eigenvalues_stable = np.linalg.eigvals(A_stable)
            spectral_radius_stable = np.max(np.abs(eigenvalues_stable))
            print(f"  谱半径（SVD后）: {spectral_radius_stable:.4f}")
        else:
            A_stable = A
            print("  跳过SVD限制")

        print("\n步骤4：更新模型...")
        # 使用模型参数的精度
        dtype = self.model.koopman.A.dtype
        self.model.koopman.A.data = torch.tensor(A_stable, dtype=dtype).to(self.device)
        self.model.koopman.B.data = torch.tensor(B, dtype=dtype).to(self.device)

        print("  Koopman矩阵已更新")

        # 验证预测性能
        print("\n步骤5：验证EDMD性能...")
        train_loader = DataLoader(train_dataset, **self._loader_kwargs(batch_size=256))
        val_loss = self._validate(train_loader)
        print(f"  训练集预测RMSE: {np.sqrt(val_loss):.6f}")

    def _encode_dataset(self, dataset):
        """
        编码所有数据到潜在空间
        """
        self.model.eval()

        Z_list = []
        Z_next_list = []
        U_list = []

        # 创建数据加载器
        batch_size = self.edmd_config['compute'].get('batch_size', 256)
        dataloader = DataLoader(dataset, **self._loader_kwargs(batch_size=batch_size))

        with torch.no_grad():
            for batch in tqdm(dataloader, desc="编码数据"):
                x_history = self._to_device(batch['x_history'])
                u_t = self._to_device(batch['u_t'])
                x_next = self._to_device(batch['x_next'])

                x_history_next = torch.cat(
                    [x_history[:, 1:, :], x_next.unsqueeze(1)], dim=1
                )

                if self.use_amp:
                    with torch.amp.autocast("cuda"):
                        z_t = self.model.encoder(x_history)
                        z_next = self.model.encoder(x_history_next)
                else:
                    z_t = self.model.encoder(x_history)
                    z_next = self.model.encoder(x_history_next)

                Z_list.append(z_t)
                Z_next_list.append(z_next)
                U_list.append(u_t)

        Z = torch.cat(Z_list, dim=0).cpu().numpy()
        Z_next = torch.cat(Z_next_list, dim=0).cpu().numpy()
        U = torch.cat(U_list, dim=0).cpu().numpy()

        return Z, Z_next, U

    def _compute_edmd(self, Z, Z_next, U):
        """
        计算EDMD闭式解
        """
        # 构造增广矩阵
        ZU = np.concatenate([Z, U], axis=1)  # [N, d+m]

        # 正则化参数
        reg = self.edmd_config['compute']['regularization']

        # 求解最小二乘问题
        ZU_T_ZU = ZU.T @ ZU
        reg_matrix = reg * np.eye(ZU_T_ZU.shape[0])
        K = Z_next.T @ ZU @ np.linalg.inv(ZU_T_ZU + reg_matrix)

        # 分离A和B
        d = Z.shape[1]
        A = K[:, :d]  # [d, d]
        B = K[:, d:]  # [d, m]

        return A, B

    def _apply_svd_clipping(self, A):
        """SVD限制确保稳定性"""
        U, S, Vt = np.linalg.svd(A)
        rho_max = self.config['koopman']['rho_max']

        S_clipped = np.clip(S, 0, rho_max)
        A_stable = U @ np.diag(S_clipped) @ Vt

        print(f"    最大奇异值: {S.max():.4f} -> {S_clipped.max():.4f}")
        print(f"    限制的奇异值数量: {np.sum(S > rho_max)}/{len(S)}")

        return A_stable

    def _validate(self, val_loader):
        """验证"""
        self.model.eval()
        total_loss = 0

        with torch.no_grad():
            for batch in val_loader:
                x_history = self._to_device(batch['x_history'])
                u_t = self._to_device(batch['u_t'])
                x_next = self._to_device(batch['x_next'])

                if self.use_amp:
                    with torch.amp.autocast("cuda"):
                        x_pred = self.model(x_history, u_t)
                        loss = F.mse_loss(x_pred, x_next)
                else:
                    x_pred = self.model(x_history, u_t)
                    loss = F.mse_loss(x_pred, x_next)
                total_loss += loss.item()

        return total_loss / len(val_loader)

    def _save_checkpoint(self, filename):
        """保存检查点"""
        save_dir = self.config['experiment']['save_dir']
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        torch.save(self.model.state_dict(), save_path)

    def _load_checkpoint(self, filename):
        """加载检查点"""
        load_path = os.path.join(self.config['experiment']['save_dir'], filename)
        self.model.load_state_dict(torch.load(load_path, weights_only=False))

        # 确保模型精度正确
        precision = self.config['experiment'].get('precision', 'float32')
        if precision == 'float64':
            self.model = self.model.double()
        else:
            self.model = self.model.float()
