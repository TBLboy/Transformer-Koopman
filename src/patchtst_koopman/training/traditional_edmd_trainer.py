"""
传统EDMD训练器（对照组，无神经网络）
"""
import os
import numpy as np
from torch.utils.data import DataLoader
from tqdm import tqdm

from patchtst_koopman.lifting import PolynomialLifting, RBFLifting, RobotLifting, ThreeLinkLifting


class TraditionalEDMDTrainer:
    """
    传统EDMD训练器

    训练流程：
        1. 初始化并拟合升维函数 ψ
        2. 对所有训练数据升维，得到 Z、Z_next、U
        3. 闭式最小二乘求解 Koopman 矩阵 A、B
        4. 由升维函数直接构造降维矩阵 C = [I_n | 0]
        5. 保存 A、B、C 及升维函数元数据

    预测流程（由调用方执行）：
        z_t   = ψ(x_t)
        z_t+1 = A @ z_t + B @ u_t
        x_t+1 = C @ z_t+1
    """

    def __init__(self, config):
        self.config = config
        self.lifting_fn = None
        self.A = None   # [d, d]
        self.B = None   # [d, m]
        self.C = None   # [n, d]

    # ════════════════════════════════════════════════════════════
    # 训练主流程
    # ════════════════════════════════════════════════════════════

    def train(self, train_dataset, val_dataset=None):
        print("\n" + "=" * 60)
        print("传统EDMD训练（对照组）")
        print("=" * 60)

        # 步骤 1：初始化并拟合升维函数
        print("\n步骤1：初始化升维函数...")
        self._init_lifting_function(train_dataset)

        # 步骤 2：升维所有训练数据
        print("\n步骤2：升维训练数据...")
        Z, Z_next, U = self._encode_dataset(train_dataset)
        print(f"  升维完成：{Z.shape[0]} 个样本")
        print(f"  原始状态维度 n = {train_dataset.x.shape[1]}")
        print(f"  升维后维度   d = {Z.shape[1]}")
        print(f"  控制维度     m = {U.shape[1]}")

        # 步骤 3：闭式求解 A、B
        print("\n步骤3：计算EDMD闭式解...")
        self.A, self.B = self._compute_edmd(Z, Z_next, U)
        print(f"  Koopman矩阵 A: {self.A.shape}")
        print(f"  控制矩阵    B: {self.B.shape}")

        eigs = np.linalg.eigvals(self.A)
        print(f"  谱半径: {np.max(np.abs(eigs)):.4f}")

        # 步骤 4：构造降维矩阵 C
        print("\n步骤4：构造降维矩阵C...")
        self.C = self.lifting_fn.get_C_matrix()   # [n, d]，精确，无需拟合
        print(f"  降维矩阵    C: {self.C.shape}  (C = [I_n | 0]，精确成立)")

        # 步骤 5：验证
        if val_dataset is not None:
            print("\n步骤5：验证性能...")
            self._validate(val_dataset)

        print("\n传统EDMD训练完成！")

    # ════════════════════════════════════════════════════════════
    # 内部方法
    # ════════════════════════════════════════════════════════════

    def _init_lifting_function(self, train_dataset):
        cfg = self.config['training']['traditional_edmd']
        lifting_type = cfg['lifting_function']['type']
        params = cfg['lifting_function']['params']

        if lifting_type == 'polynomial':
            degree = params.get('degree', 2)
            self.lifting_fn = PolynomialLifting(degree=degree)
            print(f"  使用多项式升维函数 (degree={degree})")

        elif lifting_type == 'rbf':
            n_centers = params.get('n_centers', 10)
            sigma = params.get('sigma', 1.0)
            self.lifting_fn = RBFLifting(n_centers=n_centers, sigma=sigma)
            print(f"  使用RBF升维函数 (n_centers={n_centers}, sigma={sigma})")

        elif lifting_type == 'robot':
            self.lifting_fn = RobotLifting()
            print(f"  使用机械臂物理驱动升维函数 (d={self.lifting_fn.n_features})")

        elif lifting_type == 'threelink':
            self.lifting_fn = ThreeLinkLifting()
            print(f"  使用三连杆完备升维函数 (d={self.lifting_fn.n_features})")

        else:
            raise ValueError(f"未知的升维函数类型: {lifting_type}")

        # fit：记录维度信息（使用前 1000 个样本即可）
        X_sample = train_dataset.x[:1000]
        self.lifting_fn.fit(X_sample)
        print(f"  升维函数已拟合，输入维度 n={self.lifting_fn.n_input}，"
              f"输出维度 d={self.lifting_fn.n_features}")

    def _encode_dataset(self, dataset):
        """
        对数据集中每条 (x_t, u_t, x_{t+1}) 样本做升维。

        返回:
            Z      [N, d]  当前时刻升维状态
            Z_next [N, d]  下一时刻升维状态
            U      [N, m]  控制输入
        """
        Z_list, Z_next_list, U_list = [], [], []

        batch_size = self.config['training']['traditional_edmd']['compute']['batch_size']
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        for batch in tqdm(dataloader, desc="升维数据"):
            x_history = batch['x_history'].numpy()   # [B, P, n]
            u_t       = batch['u_t'].numpy()          # [B, m]
            x_next    = batch['x_next'].numpy()       # [B, n]

            x_t = x_history[:, -1, :]                # [B, n] 取最后一个时刻

            Z_list.append(self.lifting_fn.transform(x_t))          # [B, d]
            Z_next_list.append(self.lifting_fn.transform(x_next))  # [B, d]
            U_list.append(u_t)

        return np.vstack(Z_list), np.vstack(Z_next_list), np.vstack(U_list)

    def _compute_edmd(self, Z, Z_next, U):
        """
        EDMD 闭式解：
            [A, B] = Z_next.T @ [Z, U] @ ([Z, U].T @ [Z, U] + λI)^{-1}

        返回:
            A [d, d], B [d, m]
        """
        reg = self.config['training']['traditional_edmd']['compute']['regularization']

        ZU = np.concatenate([Z, U], axis=1)          # [N, d+m]
        ZU_T_ZU = ZU.T @ ZU                           # [d+m, d+m]
        reg_mat = reg * np.eye(ZU_T_ZU.shape[0])
        K = Z_next.T @ ZU @ np.linalg.inv(ZU_T_ZU + reg_mat)  # [d, d+m]

        d = Z.shape[1]
        return K[:, :d], K[:, d:]                     # A [d,d], B [d,m]

    def _validate(self, val_dataset):
        """在升维空间做一步预测误差评估"""
        Z, Z_next, U = self._encode_dataset(val_dataset)
        Z_pred = (self.A @ Z.T + self.B @ U.T).T      # [N, d]
        rmse = np.sqrt(np.mean((Z_pred - Z_next) ** 2))
        print(f"  验证集升维空间 RMSE: {rmse:.6f}")

    # ════════════════════════════════════════════════════════════
    # 保存 / 加载
    # ════════════════════════════════════════════════════════════

    def save_model(self, save_dir):
        """
        保存 A、B、C 矩阵及升维函数元数据到 save_dir。

        文件列表：
            A_matrix.npy
            B_matrix.npy
            C_matrix.npy
            lifting_meta.npz   (n_input, n_features, lifting_type 等)
        """
        os.makedirs(save_dir, exist_ok=True)

        np.save(os.path.join(save_dir, 'A_matrix.npy'), self.A)
        np.save(os.path.join(save_dir, 'B_matrix.npy'), self.B)
        np.save(os.path.join(save_dir, 'C_matrix.npy'), self.C)

        lifting_cfg = self.config['training']['traditional_edmd']['lifting_function']
        np.savez(
            os.path.join(save_dir, 'lifting_meta.npz'),
            lifting_type=lifting_cfg['type'],
            n_input=self.lifting_fn.n_input,
            n_features=self.lifting_fn.n_features,
            degree=lifting_cfg['params'].get('degree', 0),  # robot 类型填 0
        )

        print(f"  模型已保存到: {save_dir}")
        print(f"    A {self.A.shape}, B {self.B.shape}, C {self.C.shape}")

    def load_model(self, save_dir):
        """
        从 save_dir 加载 A、B、C 矩阵及升维函数元数据。
        加载完成后 trainer 可直接用于预测，无需重新 fit。
        """
        self.A = np.load(os.path.join(save_dir, 'A_matrix.npy'))
        self.B = np.load(os.path.join(save_dir, 'B_matrix.npy'))
        self.C = np.load(os.path.join(save_dir, 'C_matrix.npy'))

        meta = np.load(os.path.join(save_dir, 'lifting_meta.npz'), allow_pickle=True)
        lifting_type = str(meta['lifting_type'])
        n_input      = int(meta['n_input'])
        n_features   = int(meta['n_features'])
        degree       = int(meta['degree'])

        if lifting_type == 'polynomial':
            self.lifting_fn = PolynomialLifting(degree=degree)
        elif lifting_type == 'rbf':
            cfg = self.config['training']['traditional_edmd']['lifting_function']['params']
            self.lifting_fn = RBFLifting(
                n_centers=cfg.get('n_centers', 10),
                sigma=cfg.get('sigma', 1.0),
            )
        elif lifting_type == 'robot':
            self.lifting_fn = RobotLifting()
        elif lifting_type == 'threelink':
            self.lifting_fn = ThreeLinkLifting()
        else:
            raise ValueError(f"未知的升维函数类型: {lifting_type}")

        # 直接恢复维度信息，无需重新 fit
        self.lifting_fn.n_input    = n_input
        self.lifting_fn.n_features = n_features

        print(f"  模型已从 {save_dir} 加载")
        print(f"    A {self.A.shape}, B {self.B.shape}, C {self.C.shape}")
        print(f"    升维函数: {lifting_type}, n={n_input}, d={n_features}")