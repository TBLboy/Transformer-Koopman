"""
面向3自由度机械臂的物理驱动升维函数 — 不完备版 (RobotLifting)
=============================================================

对照实验用途：故意删去块5（角度-角速度耦合）和块6（高阶三角耦合），
使升维函数缺失部分 Koopman 闭包信息，用于与完备版对比。

状态定义（与 robot.m 一致）：
    x = [q1, dq1, q2, dq2, q3, dq3]
        索引:  0    1    2    3    4    5

升维结构（共 d 维，前 6 维精确等于 x）：

    块0 [0:6]    — 原始状态 x（保证 C = [I_6 | 0] 精确成立）

    块1 [6:11]   — 重力/惯性相关三角项
                   cos(q1), cos(q2), cos(q3),
                   cos(q2+q3), cos(q1+q2+q3)

    块2 [11:16]  — 科氏力 / 离心力三角项
                   sin(q2), sin(q3), sin(2q2+q3),
                   cos(q2)*sin(q2), cos(q3)*sin(q3)

    块3 [16:22]  — 速度与三角函数的乘积（科氏/离心力载体）
                   dq1*cos(q1),   dq1*sin(q1),
                   dq2*cos(q2),   dq2*cos(q2+q3),
                   dq3*cos(q2+q3),dq3*cos(q3)

    块4 [22:28]  — 纯速度二次项（动能相关）
                   dq1², dq2², dq3², dq1*dq2, dq1*dq3, dq2*dq3

    （已删去）块5 — 角度-角速度耦合
    （已删去）块6 — 高阶三角耦合

    总维度 d = 28
"""

import numpy as np


class RobotLifting:
    """
    物理驱动升维函数，专为 robot.m 所描述的3DOF机械臂设计。

    保证：
        前 n=6 个分量精确等于原始状态 x，
        因此降维矩阵 C = [I_6 | 0] 严格成立，无需最小二乘拟合。

    用法：
        lifting = RobotLifting()
        lifting.fit(X_train)          # 仅记录维度，无可训练参数
        Z = lifting.transform(X)      # [N, 38]
        C = lifting.get_C_matrix()    # [6, 38]
    """

    def __init__(self):
        self.n_input    = 6
        self.n_features = 28          # 见上方文档
        self.feature_names = None     # 可选，调试用

    # ── 公开接口 ────────────────────────────────────────────────

    def fit(self, X):
        """记录维度（与 PolynomialLifting 接口兼容）。"""
        assert X.shape[1] == self.n_input, \
            f"输入状态维度应为 6，实际为 {X.shape[1]}"
        self.feature_names = self._build_feature_names()
        return self

    def transform(self, X):
        """
        升维变换。

        参数:
            X: ndarray, shape [N, 6]，每行为 [q1,dq1,q2,dq2,q3,dq3]

        返回:
            Z: ndarray, shape [N, 38]
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        N = X.shape[0]
        Z = np.zeros((N, self.n_features))

        # 拆分变量（与 robot.m 中 x(1)~x(6) 对应）
        q1  = X[:, 0];  dq1 = X[:, 1]
        q2  = X[:, 2];  dq2 = X[:, 3]
        q3  = X[:, 4];  dq3 = X[:, 5]

        # ── 块0 [0:6]：原始状态 ──────────────────────────────
        Z[:, 0:6] = X

        # ── 块1 [6:11]：重力/惯性三角项 ─────────────────────
        Z[:, 6]  = np.cos(q1)
        Z[:, 7]  = np.cos(q2)
        Z[:, 8]  = np.cos(q3)
        Z[:, 9]  = np.cos(q2 + q3)
        Z[:, 10] = np.cos(q1 + q2 + q3)

        # ── 块2 [11:16]：科氏/离心三角项 ────────────────────
        Z[:, 11] = np.sin(q2)
        Z[:, 12] = np.sin(q3)
        Z[:, 13] = np.sin(2*q2 + q3)
        Z[:, 14] = np.cos(q2) * np.sin(q2)          # = 0.5*sin(2q2)
        Z[:, 15] = np.cos(q3) * np.sin(q3)          # = 0.5*sin(2q3)

        # ── 块3 [16:22]：速度×三角函数（科氏力载体） ────────
        Z[:, 16] = dq1 * np.cos(q1)
        Z[:, 17] = dq1 * np.sin(q1)
        Z[:, 18] = dq2 * np.cos(q2)
        Z[:, 19] = dq2 * np.cos(q2 + q3)
        Z[:, 20] = dq3 * np.cos(q2 + q3)
        Z[:, 21] = dq3 * np.cos(q3)

        # ── 块4 [22:28]：纯速度二次项（动能相关） ───────────
        Z[:, 22] = dq1 * dq1
        Z[:, 23] = dq2 * dq2
        Z[:, 24] = dq3 * dq3
        Z[:, 25] = dq1 * dq2
        Z[:, 26] = dq1 * dq3
        Z[:, 27] = dq2 * dq3

        # 块5（角度-角速度耦合）和块6（高阶三角耦合）已删去

        return Z

    def fit_transform(self, X):
        self.fit(X)
        return self.transform(X)

    def get_C_matrix(self):
        """
        返回降维矩阵 C ∈ R^{6×38}，满足 x = C @ z 严格成立。

        C = [I_6 | 0_{6×32}]
        """
        C = np.zeros((self.n_input, self.n_features))
        C[:, :self.n_input] = np.eye(self.n_input)
        return C

    def get_lifted_dim(self):
        return self.n_features

    # ── 内部工具 ────────────────────────────────────────────────

    def _build_feature_names(self):
        names = ['q1','dq1','q2','dq2','q3','dq3',
                 'cos(q1)','cos(q2)','cos(q3)','cos(q2+q3)','cos(q1+q2+q3)',
                 'sin(q2)','sin(q3)','sin(2q2+q3)','cos(q2)sin(q2)','cos(q3)sin(q3)',
                 'dq1*cos(q1)','dq1*sin(q1)','dq2*cos(q2)','dq2*cos(q2+q3)',
                 'dq3*cos(q2+q3)','dq3*cos(q3)',
                 'dq1^2','dq2^2','dq3^2','dq1*dq2','dq1*dq3','dq2*dq3']
        return names