"""
EDMD训练器
"""
import os
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from tqdm import tqdm

from patchtst_koopman.utils.seed import get_worker_init_fn


class EDMDTrainer:
    """
    EDMD训练方法

    流程：
        阶段0：随机编码器 + EDMD 初始化 Koopman 矩阵
        阶段1：预训练编码器与 Koopman 矩阵（单步预测损失）
        阶段2：固定编码器，EDMD 闭式解重拟合 A/B
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
        seed = self.config['experiment'].get('seed', 42)
        kwargs = {
            'batch_size': batch_size,
            'shuffle': shuffle,
            'num_workers': num_workers,
            'worker_init_fn': get_worker_init_fn(seed),
            'generator': torch.Generator().manual_seed(seed),
        }
        if self.device == 'cuda':
            kwargs['pin_memory'] = True
            if num_workers > 0:
                kwargs['persistent_workers'] = True
                kwargs['prefetch_factor'] = training.get('prefetch_factor', 4)
        return kwargs

    def _to_device(self, tensor):
        return tensor.to(self.device, non_blocking=(self.device == 'cuda'))

    def _accumulate_loss(self, total, value):
        """Accumulate scalar losses without synchronising CUDA every batch."""
        value = value.detach()
        return value if total is None else total + value

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

        print("\n" + "=" * 60)
        print("端到端训练 PatchTST-Koopman")
        print("=" * 60)

        for epoch in range(e2e["num_epochs"]):
            self.model.train()
            total_loss = None

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

                total_loss = self._accumulate_loss(total_loss, loss)

            svd_proj = e2e.get("svd_projection", {})
            if svd_proj.get("enabled", False) and epoch % svd_proj.get("frequency", 1) == 0:
                self.model.koopman.ensure_stability()

            train_loss = (total_loss / len(train_loader)).item()
            val_loss = self._validate(val_loader)

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

        best_path = os.path.join(self.config['experiment']['save_dir'], "e2e_best.pth")
        if os.path.exists(best_path):
            self._load_checkpoint("e2e_best.pth")
            print(f"  >>> 回载最佳检查点 e2e_best.pth (val_loss={best_val_loss:.6f})")
        else:
            print("  >>> 未找到最佳检查点，使用最后一轮模型权重")

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
        """阶段1：预训练编码器和降维矩阵"""
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

        optimizer = torch.optim.Adam([
            {'params': self.model.encoder.parameters()},
            {'params': self.model.koopman.parameters()}
        ], lr=self.edmd_config['pretrain']['learning_rate'])

        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode='min',
            factor=0.5,
            patience=10,
            min_lr=1e-6
        )

        best_val_loss = float('inf')
        patience_counter = 0
        prev_lr = self.edmd_config['pretrain']['learning_rate']

        print("注意：使用状态嵌入式编码器，解码器固定，不使用重建损失")

        for epoch in range(self.edmd_config['pretrain']['num_epochs']):
            train_loss = self._pretrain_epoch(train_loader, optimizer)
            val_loss = self._validate(val_loader)

            scheduler.step(val_loss)
            current_lr = optimizer.param_groups[0]['lr']

            if current_lr != prev_lr:
                print(f"  >>> 学习率降低: {prev_lr:.2e} -> {current_lr:.2e}")
                prev_lr = current_lr

            print(f"Epoch {epoch+1}/{self.edmd_config['pretrain']['num_epochs']}: "
                  f"Train Loss = {train_loss:.6f}, Val Loss = {val_loss:.6f}, LR = {current_lr:.2e}")

            if self.edmd_config['pretrain']['early_stopping']:
                if val_loss < best_val_loss - self.edmd_config['pretrain']['min_delta']:
                    best_val_loss = val_loss
                    patience_counter = 0
                    self._save_checkpoint('pretrain_best.pth')
                else:
                    patience_counter += 1

                if patience_counter >= self.edmd_config['pretrain']['patience']:
                    print(f"早停触发（patience={patience_counter}）")
                    self._load_checkpoint('pretrain_best.pth')
                    break

        best_path = os.path.join(self.config['experiment']['save_dir'], "pretrain_best.pth")
        if os.path.exists(best_path):
            self._load_checkpoint('pretrain_best.pth')
            print(f"  >>> 回载最佳检查点 pretrain_best.pth (val_loss={best_val_loss:.6f})")

        print(f"预训练完成，最佳验证损失: {best_val_loss:.6f}")

    def _pretrain_epoch(self, train_loader, optimizer):
        """预训练的单个epoch（五项损失：单步预测 + 升维空间 + 一致性约束 + 多步物理 + 多步升维）"""
        self.model.train()
        total_loss = None
        loss_pred_total = None
        loss_latent_total = None
        loss_consistency_total = None
        loss_multi_x_total = None
        loss_multi_z_total = None

        loss_weights = self.edmd_config['pretrain'].get('loss_weights',
                                                        {'prediction': 1.0,
                                                         'latent': 0.5,
                                                         'consistency': 0.5})
        w_multi_x = loss_weights.get('multi_step_physical', 0.0)
        w_multi_z = loss_weights.get('multi_step_latent', 0.0)
        use_multi_step = (w_multi_x > 0 or w_multi_z > 0)

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

                L_multi_x = torch.tensor(0.0, device=x_history.device)
                L_multi_z = torch.tensor(0.0, device=x_history.device)

                if use_multi_step:
                    x_future = self._to_device(batch['x_future'])
                    u_future = self._to_device(batch['u_future'])
                    x_history_future = self._to_device(batch['x_history_future'])

                    B, N_L = x_future.shape[0], x_future.shape[1]

                    z_hat_seq = self.model.roll_out_latent(z_t, u_future)

                    if w_multi_x > 0:
                        n_state = self.model.decoder.n
                        x_hat_seq = z_hat_seq[..., :n_state]
                        L_multi_x = F.mse_loss(x_hat_seq, x_future)
                        loss = loss + w_multi_x * L_multi_x

                    if w_multi_z > 0:
                        B, N_L = x_history_future.shape[0], x_history_future.shape[1]
                        P = x_history.shape[1]
                        xhf_flat = x_history_future.reshape(B * N_L, P, -1)
                        z_true_seq = self.model.encoder(xhf_flat).reshape(B, N_L, -1)
                        L_multi_z = F.mse_loss(z_hat_seq, z_true_seq)
                        loss = loss + w_multi_z * L_multi_z

                return loss, L_pred, L_latent, L_consistency, L_multi_x, L_multi_z

            if self.use_amp:
                with torch.amp.autocast("cuda"):
                    loss, L_pred, L_latent, L_consistency, L_multi_x, L_multi_z = _compute_losses()
                self.scaler.scale(loss).backward()
                self.scaler.step(optimizer)
                self.scaler.update()
            else:
                loss, L_pred, L_latent, L_consistency, L_multi_x, L_multi_z = _compute_losses()
                loss.backward()
                optimizer.step()

            total_loss = self._accumulate_loss(total_loss, loss)
            loss_pred_total = self._accumulate_loss(loss_pred_total, L_pred)
            loss_latent_total = self._accumulate_loss(loss_latent_total, L_latent)
            loss_consistency_total = self._accumulate_loss(loss_consistency_total, L_consistency)
            loss_multi_x_total = self._accumulate_loss(loss_multi_x_total, L_multi_x)
            loss_multi_z_total = self._accumulate_loss(loss_multi_z_total, L_multi_z)

        avg_loss = (total_loss / len(train_loader)).item()
        avg_pred = (loss_pred_total / len(train_loader)).item()
        avg_latent = (loss_latent_total / len(train_loader)).item()
        avg_consistency = (loss_consistency_total / len(train_loader)).item()

        if use_multi_step:
            avg_multi_x = (loss_multi_x_total / len(train_loader)).item()
            avg_multi_z = (loss_multi_z_total / len(train_loader)).item()
            print(f"  [损失分解] Pred: {avg_pred:.6f}, Latent: {avg_latent:.6f}, "
                  f"Consistency: {avg_consistency:.6f}, "
                  f"MultiX: {avg_multi_x:.6f}, MultiZ: {avg_multi_z:.6f}")
        else:
            print(f"  [损失分解] Pred: {avg_pred:.6f}, Latent: {avg_latent:.6f}, Consistency: {avg_consistency:.6f}")

        return avg_loss

    def _compute_koopman_with_edmd(self, train_dataset):
        """阶段2：使用EDMD计算Koopman矩阵"""
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

        eigenvalues = np.linalg.eigvals(A)
        spectral_radius = np.max(np.abs(eigenvalues))
        print(f"  谱半径（SVD前）: {spectral_radius:.4f}")

        print("\n步骤3：SVD后处理...")
        if self.edmd_config['compute']['svd_clipping']:
            A_stable = self._apply_svd_clipping(A)
        else:
            A_stable = A
            print("  跳过SVD限制")

        print("\n步骤4：更新模型...")
        dtype = self.model.koopman.A.dtype
        self.model.koopman.A.data = torch.tensor(A_stable, dtype=dtype).to(self.device)
        self.model.koopman.B.data = torch.tensor(B, dtype=dtype).to(self.device)

        print("  Koopman矩阵已更新")

        print("\n步骤5：验证EDMD性能...")
        train_loader = DataLoader(train_dataset, **self._loader_kwargs(batch_size=256))
        val_loss = self._validate(train_loader)
        print(f"  训练集预测RMSE: {np.sqrt(val_loss):.6f}")

    def _encode_dataset(self, dataset):
        """编码所有数据到潜在空间"""
        self.model.eval()

        Z_list = []
        Z_next_list = []
        U_list = []

        batch_size = self.edmd_config['compute'].get('batch_size', 256)
        dataloader = DataLoader(dataset, **self._loader_kwargs(batch_size=batch_size))

        with torch.inference_mode():
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
        """计算EDMD闭式解"""
        ZU = np.concatenate([Z, U], axis=1)
        reg = self.edmd_config['compute']['regularization']

        ZU_T_ZU = ZU.T @ ZU
        reg_matrix = reg * np.eye(ZU_T_ZU.shape[0], dtype=ZU_T_ZU.dtype)
        M = ZU_T_ZU + reg_matrix
        K = np.linalg.solve(M, ZU.T @ Z_next).T

        d = Z.shape[1]
        A = K[:, :d]
        B = K[:, d:]

        if np.any(np.isnan(A)) or np.any(np.isnan(B)) or np.any(np.isinf(A)) or np.any(np.isinf(B)):
            raise RuntimeError(
                "EDMD computed NaN/Inf in Koopman matrices. "
                f"Z stats: mean={Z.mean():.6f} std={Z.std():.6f} "
                f"min={Z.min():.6f} max={Z.max():.6f}. "
                "Try increasing edmd.compute.regularization."
            )

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
        total_loss = None

        with torch.inference_mode():
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
                total_loss = self._accumulate_loss(total_loss, loss)

        return (total_loss / len(val_loader)).item()

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

        precision = self.config['experiment'].get('precision', 'float32')
        if precision == 'float64':
            self.model = self.model.double()
        else:
            self.model = self.model.float()
