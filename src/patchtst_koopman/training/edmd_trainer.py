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

    def _loader_kwargs(self, shuffle=False, batch_size=256):
        """Create DataLoader kwargs with CUDA-friendly defaults."""
        num_workers = self.config['training'].get('num_workers', 0)
        kwargs = {
            'batch_size': batch_size,
            'shuffle': shuffle,
            'num_workers': num_workers,
        }
        if self.device == 'cuda':
            kwargs['pin_memory'] = True
            if num_workers > 0:
                kwargs['persistent_workers'] = True
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
        val_loader = DataLoader(val_dataset, **self._loader_kwargs(batch_size=256))

        optimizer = torch.optim.Adam(
            self.model.parameters(), lr=e2e["learning_rate"]
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

                x_pred = self.model(x_history, u_t)

                # 1. 预测损失
                loss = w_pred * F.mse_loss(x_pred, x_next)

                # 2. 稳定性损失：鼓励 A 接近正交 (A^T A ≈ I)
                if w_stab > 0:
                    A = self.model.koopman.A
                    I = torch.eye(A.size(-1), device=A.device, dtype=A.dtype)
                    loss += w_stab * F.mse_loss(A.T @ A, I)

                # 3. 正则化损失：L2 参数惩罚
                if w_reg > 0:
                    reg_penalty = sum(p.pow(2).sum() for p in self.model.parameters())
                    loss += w_reg * reg_penalty

                optimizer.zero_grad()
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
        val_loader = DataLoader(val_dataset, **self._loader_kwargs(batch_size=256))

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
            train_loss = self._pretrain_epoch(train_loader, optimizer)

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

    def _pretrain_epoch(self, train_loader, optimizer):
        """预训练的单个epoch（三项损失：原始空间预测 + 升维空间预测 + 一致性约束）"""
        self.model.train()
        total_loss = 0
        loss_pred_total = 0
        loss_latent_total = 0
        loss_consistency_total = 0

        # 获取损失权重
        loss_weights = self.edmd_config['pretrain'].get('loss_weights',
                                                        {'prediction': 1.0,
                                                         'latent': 0.5,
                                                         'consistency': 0.5})

        for batch in tqdm(train_loader, desc="预训练"):
            x_history = self._to_device(batch['x_history'])
            u_t = self._to_device(batch['u_t'])
            x_next = self._to_device(batch['x_next'])

            # 构造下一时刻的历史窗口
            x_history_next = torch.cat([x_history[:, 1:, :],
                                       x_next.unsqueeze(1)], dim=1)

            # 前向传播
            z_t = self.model.encoder(x_history)
            z_pred = self.model.koopman(z_t, u_t)
            x_pred = self.model.decoder(z_pred)

            # ========== 计算三项损失 ==========

            # 1. 原始空间预测损失
            L_pred = F.mse_loss(x_pred, x_next)

            # 2. 升维空间预测损失
            z_true = self.model.encoder(x_history_next)
            L_latent = F.mse_loss(z_pred, z_true)

            # 3. 一致性损失：用预测的x_pred构造窗口，再编码，与z_true比较
            x_history_pred_next = torch.cat([x_history[:, 1:, :], x_pred.unsqueeze(1)], dim=1)
            z_from_pred = self.model.encoder(x_history_pred_next)
            L_consistency = F.mse_loss(z_from_pred, z_true)

            # 总损失（加权组合）
            loss = (loss_weights['prediction'] * L_pred +
                    loss_weights['latent'] * L_latent +
                    loss_weights['consistency'] * L_consistency)

            # 反向传播
            optimizer.zero_grad()
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

                # 编码当前状态
                z_t = self.model.encoder(x_history)

                # 编码下一时刻状态
                # 需要构造下一时刻的历史窗口：去掉第一个，加上x_next
                x_history_next = torch.cat([x_history[:, 1:, :],
                                           x_next.unsqueeze(1)], dim=1)
                z_next = self.model.encoder(x_history_next)

                Z_list.append(z_t.cpu().numpy())
                Z_next_list.append(z_next.cpu().numpy())
                U_list.append(u_t.cpu().numpy())

        Z = np.concatenate(Z_list, axis=0)
        Z_next = np.concatenate(Z_next_list, axis=0)
        U = np.concatenate(U_list, axis=0)

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
