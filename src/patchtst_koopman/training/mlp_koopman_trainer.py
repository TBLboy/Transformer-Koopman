"""
MLP-Koopman 训练器

支持两种训练方式，由 config['mlp_koopman']['training_method'] 控制：
  - "edmd"       : 预训练编码器 → EDMD 闭式解求 A、B（与 EDMDTrainer 逻辑一致）
  - "end_to_end" : 编码器 + A + B 全程梯度下降
"""

import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from tqdm import tqdm
import numpy as np


class MLPKoopmanTrainer:

    def __init__(self, model, config):
        self.model  = model
        self.config = config
        self.device = config['experiment']['device']
        self.mlp_cfg = config['mlp_koopman']

    # ════════════════════════════════════════════════════════════
    # 主入口
    # ════════════════════════════════════════════════════════════

    def train(self, train_dataset, val_dataset):
        method = self.mlp_cfg['training_method']
        if method == 'edmd':
            self._train_edmd(train_dataset, val_dataset)
        elif method == 'end_to_end':
            self._train_end_to_end(train_dataset, val_dataset)
        else:
            raise ValueError(f"未知的训练方式: {method}")

    # ════════════════════════════════════════════════════════════
    # EDMD 训练流程
    # ════════════════════════════════════════════════════════════

    def _train_edmd(self, train_dataset, val_dataset):
        edmd_cfg = self.mlp_cfg['edmd']

        # 阶段0：初始 EDMD（用随机初始化的编码器）
        print("\n" + "=" * 60)
        print("阶段0：初始EDMD计算")
        print("=" * 60)
        self._compute_koopman_edmd(train_dataset)

        # 阶段1：预训练编码器
        if edmd_cfg['pretrain']['enabled']:
            print("\n" + "=" * 60)
            print("阶段1：预训练MLP编码器")
            print("=" * 60)
            self._pretrain(train_dataset, val_dataset, edmd_cfg['pretrain'])

        # 阶段2：最终 EDMD
        print("\n" + "=" * 60)
        print("阶段2：最终EDMD优化Koopman矩阵")
        print("=" * 60)
        self._compute_koopman_edmd(train_dataset)

        print("\nEDMD训练完成！")

    def _pretrain(self, train_dataset, val_dataset, pretrain_cfg):
        train_loader = DataLoader(
            train_dataset,
            batch_size=pretrain_cfg['batch_size'],
            shuffle=True,
            num_workers=self.config['training'].get('num_workers', 0)
        )
        val_loader = DataLoader(val_dataset, batch_size=256, shuffle=False)

        optimizer = torch.optim.Adam(
            list(self.model.encoder.parameters()) +
            list(self.model.koopman.parameters()),
            lr=pretrain_cfg['learning_rate']
        )
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=10, min_lr=1e-6
        )

        best_val_loss = float('inf')
        patience_counter = 0
        prev_lr = pretrain_cfg['learning_rate']
        loss_weights = pretrain_cfg.get('loss_weights',
                                        {'prediction': 1.0, 'latent': 0.5, 'consistency': 0.5})

        for epoch in range(pretrain_cfg['num_epochs']):
            train_loss = self._pretrain_epoch(train_loader, optimizer, loss_weights)
            val_loss   = self._validate(val_loader)
            scheduler.step(val_loss)

            current_lr = optimizer.param_groups[0]['lr']
            if current_lr != prev_lr:
                print(f"  >>> 学习率降低: {prev_lr:.2e} -> {current_lr:.2e}")
                prev_lr = current_lr

            print(f"Epoch {epoch+1}/{pretrain_cfg['num_epochs']}: "
                  f"Train={train_loss:.6f}  Val={val_loss:.6f}  LR={current_lr:.2e}")

            if pretrain_cfg['early_stopping']:
                if val_loss < best_val_loss - pretrain_cfg['min_delta']:
                    best_val_loss = val_loss
                    patience_counter = 0
                    self._save_checkpoint('mlp_pretrain_best.pth')
                else:
                    patience_counter += 1
                if patience_counter >= pretrain_cfg['patience']:
                    print(f"早停触发 (patience={patience_counter})")
                    self._load_checkpoint('mlp_pretrain_best.pth')
                    break

        print(f"预训练完成，最佳验证损失: {best_val_loss:.6f}")

    def _pretrain_epoch(self, train_loader, optimizer, loss_weights):
        self.model.train()
        total_loss = 0

        for batch in tqdm(train_loader, desc="预训练"):
            x_history = batch['x_history'].to(self.device)
            u_t       = batch['u_t'].to(self.device)
            x_next    = batch['x_next'].to(self.device)

            x_history_next = torch.cat(
                [x_history[:, 1:, :], x_next.unsqueeze(1)], dim=1
            )

            z_t    = self.model.encoder(x_history)
            z_pred = self.model.koopman(z_t, u_t)
            x_pred = self.model.decoder(z_pred)

            L_pred        = F.mse_loss(x_pred, x_next)
            z_true        = self.model.encoder(x_history_next)
            L_latent      = F.mse_loss(z_pred, z_true)
            L_consistency = F.mse_loss(self.model.encoder(x_history_next), z_true)

            loss = (loss_weights['prediction']  * L_pred +
                    loss_weights['latent']       * L_latent +
                    loss_weights['consistency']  * L_consistency)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        return total_loss / len(train_loader)

    def _compute_koopman_edmd(self, train_dataset):
        precision = self.config['experiment'].get('precision', 'float32')
        if precision == 'float64':
            self.model = self.model.double()
        else:
            self.model = self.model.float()

        print("编码所有训练数据...")
        Z, Z_next, U = self._encode_dataset(train_dataset)
        print(f"  样本数={Z.shape[0]}, 潜在维度={Z.shape[1]}, 控制维度={U.shape[1]}")

        reg = self.mlp_cfg['edmd']['compute']['regularization']
        ZU      = np.concatenate([Z, U], axis=1)
        ZU_T_ZU = ZU.T @ ZU
        K = Z_next.T @ ZU @ np.linalg.inv(ZU_T_ZU + reg * np.eye(ZU_T_ZU.shape[0]))
        d = Z.shape[1]
        A, B = K[:, :d], K[:, d:]

        eigs = np.linalg.eigvals(A)
        print(f"  谱半径: {np.max(np.abs(eigs)):.4f}")

        dtype = self.model.koopman.A.dtype
        self.model.koopman.A.data = torch.tensor(A, dtype=dtype).to(self.device)
        self.model.koopman.B.data = torch.tensor(B, dtype=dtype).to(self.device)
        print("  Koopman矩阵已更新")

    def _encode_dataset(self, dataset):
        batch_size = self.mlp_cfg['edmd']['compute']['batch_size']
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
        Z_list, Z_next_list, U_list = [], [], []

        self.model.eval()
        with torch.no_grad():
            for batch in tqdm(loader, desc="编码数据"):
                x_history = batch['x_history'].to(self.device)
                u_t       = batch['u_t'].to(self.device)
                x_next    = batch['x_next'].to(self.device)

                x_history_next = torch.cat(
                    [x_history[:, 1:, :], x_next.unsqueeze(1)], dim=1
                )

                Z_list.append(self.model.encoder(x_history).cpu().numpy())
                Z_next_list.append(self.model.encoder(x_history_next).cpu().numpy())
                U_list.append(u_t.cpu().numpy())

        return np.vstack(Z_list), np.vstack(Z_next_list), np.vstack(U_list)

    # ════════════════════════════════════════════════════════════
    # 端到端训练流程
    # ════════════════════════════════════════════════════════════

    def _train_end_to_end(self, train_dataset, val_dataset):
        e2e_cfg = self.mlp_cfg['end_to_end']

        train_loader = DataLoader(
            train_dataset,
            batch_size=e2e_cfg['batch_size'],
            shuffle=True,
            num_workers=self.config['training'].get('num_workers', 0)
        )
        val_loader = DataLoader(val_dataset, batch_size=256, shuffle=False)

        optimizer = torch.optim.Adam(
            self.model.parameters(), lr=e2e_cfg['learning_rate']
        )
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=10, min_lr=1e-6
        )

        best_val_loss = float('inf')
        patience_counter = 0
        prev_lr = e2e_cfg['learning_rate']

        print("\n" + "=" * 60)
        print("端到端训练 MLP-Koopman")
        print("=" * 60)

        for epoch in range(e2e_cfg['num_epochs']):
            self.model.train()
            total_loss = 0

            for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}"):
                x_history = batch['x_history'].to(self.device)
                u_t       = batch['u_t'].to(self.device)
                x_next    = batch['x_next'].to(self.device)

                x_pred = self.model(x_history, u_t)
                loss   = F.mse_loss(x_pred, x_next)

                optimizer.zero_grad()
                loss.backward()
                if e2e_cfg.get('grad_clip', 0) > 0:
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), e2e_cfg['grad_clip']
                    )
                optimizer.step()
                total_loss += loss.item()

            train_loss = total_loss / len(train_loader)
            val_loss   = self._validate(val_loader)
            scheduler.step(val_loss)

            current_lr = optimizer.param_groups[0]['lr']
            if current_lr != prev_lr:
                print(f"  >>> 学习率降低: {prev_lr:.2e} -> {current_lr:.2e}")
                prev_lr = current_lr

            print(f"Epoch {epoch+1}/{e2e_cfg['num_epochs']}: "
                  f"Train={train_loss:.6f}  Val={val_loss:.6f}  LR={current_lr:.2e}")

            if e2e_cfg['early_stopping']:
                if val_loss < best_val_loss - e2e_cfg['min_delta']:
                    best_val_loss = val_loss
                    patience_counter = 0
                    self._save_checkpoint('mlp_e2e_best.pth')
                else:
                    patience_counter += 1
                if patience_counter >= e2e_cfg['patience']:
                    print(f"早停触发 (patience={patience_counter})")
                    self._load_checkpoint('mlp_e2e_best.pth')
                    break

        print(f"\n端到端训练完成，最佳验证损失: {best_val_loss:.6f}")

    # ════════════════════════════════════════════════════════════
    # 工具方法
    # ════════════════════════════════════════════════════════════

    def _validate(self, val_loader):
        self.model.eval()
        total_loss = 0
        with torch.no_grad():
            for batch in val_loader:
                x_history = batch['x_history'].to(self.device)
                u_t       = batch['u_t'].to(self.device)
                x_next    = batch['x_next'].to(self.device)
                x_pred    = self.model(x_history, u_t)
                total_loss += F.mse_loss(x_pred, x_next).item()
        return total_loss / len(val_loader)

    def _save_checkpoint(self, filename):
        save_dir = self.config['experiment']['save_dir']
        os.makedirs(save_dir, exist_ok=True)
        torch.save(self.model.state_dict(),
                   os.path.join(save_dir, filename))

    def _load_checkpoint(self, filename):
        path = os.path.join(self.config['experiment']['save_dir'], filename)
        if os.path.exists(path):
            self.model.load_state_dict(torch.load(path, map_location=self.device))
