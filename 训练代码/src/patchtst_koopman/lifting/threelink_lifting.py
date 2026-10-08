"""
三连杆机械臂完备物理升维函数 (ThreeLinkLifting)
================================================

直接翻译自 MATLAB lift_function.m，保留全部 6 组特征。

状态定义：
    x = [q1, dq1, q2, dq2, q3, dq3]
        索引:  0    1    2    3    4    5

升维结构（共 57 维）：

    a1 [0 :7 ]  — 原始状态 + 常数项 (7维)
                  q1, dq1, q2, dq2, q3, dq3, 1

    a2 [7 :13]  — 各关节角的 sin/cos (6维)
                  sin(q1), cos(q1), sin(q2), cos(q2), sin(q3), cos(q3)

    a3 [13:21]  — q2/q3 的二次三角项 (8维)
                  sin²(q2), sin²(q3), cos²(q2), cos²(q3),
                  cos(q2)cos(q3), sin(q2)sin(q3),
                  cos(q2)sin(q3), sin(q2)cos(q3)

    a4 [21:30]  — 角速度 × 三角函数交叉项 (9维)
                  dq1*sin(q2), dq2*sin(q2), dq3*sin(q2),
                  dq1*sin(q3), dq2*sin(q3), dq3*sin(q3),
                  dq1*sin(q2+q3), dq2*sin(q2+q3), dq3*sin(q2+q3)

    a5 [30:36]  — 跨关节三角乘积项 (6维)
                  sin(q1)cos(q2), cos(q1)sin(q2),
                  sin(q1)cos(q2)cos(q3), sin(q1)sin(q2)sin(q3),
                  cos(q1)sin(q2)sin(q3), cos(q1)cos(q2)cos(q3)

    a6 [36:57]  — 所有状态变量的二次多项式项 (21维)
                  q1², q2², q3², dq1², dq2², dq3²,
                  q1*q2, q1*q3, q1*dq1, q1*dq2, q1*dq3,
                  q2*q3, q2*dq1, q2*dq2, q2*dq3,
                  q3*dq1, q3*dq2, q3*dq3,
                  dq1*dq2, dq1*dq3, dq2*dq3

    总维度 d = 57

注意：a1 的前 6 维精确等于原始状态 x，
因此降维矩阵 C = [I_6 | 0_{6×51}] 严格成立，无需最小二乘拟合。
"""

import numpy as np


class ThreeLinkLifting:
    """
    三连杆机械臂完备物理升维函数。

    完整翻译自 MATLAB lift_function.m，包含全部 6 组特征（57维）。

    用法：
        lifting = ThreeLinkLifting()
        lifting.fit(X_train)       # 仅做维度检查，无可训练参数
        Z = lifting.transform(X)   # [N, 57]
        C = lifting.get_C_matrix() # [6, 57]
    """

    def __init__(self):
        self.n_input    = 6
        self.n_features = 57

    # ── 公开接口 ────────────────────────────────────────────────

    def fit(self, X):
        """记录维度（与其他升维函数接口兼容）。"""
        assert X.shape[1] == self.n_input, \
            f"输入状态维度应为 6，实际为 {X.shape[1]}"
        return self

    def transform(self, X):
        """
        升维变换。

        参数:
            X: ndarray, shape [N, 6]，每行为 [q1, dq1, q2, dq2, q3, dq3]

        返回:
            Z: ndarray, shape [N, 57]
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        N = X.shape[0]

        q1  = X[:, 0];  dq1 = X[:, 1]
        q2  = X[:, 2];  dq2 = X[:, 3]
        q3  = X[:, 4];  dq3 = X[:, 5]

        c1 = np.cos(q1);  c2 = np.cos(q2);  c3 = np.cos(q3)
        s1 = np.sin(q1);  s2 = np.sin(q2);  s3 = np.sin(q3)

        # a1 [0:7] — 原始状态 + 常数项
        a1 = np.column_stack([q1, dq1, q2, dq2, q3, dq3, np.ones(N)])

        # a2 [7:13] — 各关节角的 sin/cos
        a2 = np.column_stack([s1, c1, s2, c2, s3, c3])

        # a3 [13:21] — q2/q3 的二次三角项
        a3 = np.column_stack([
            s2**2, s3**2, c2**2, c3**2,
            c2*c3, s2*s3, c2*s3, s2*c3
        ])

        # a4 [21:30] — 角速度 × 三角函数交叉项
        a4 = np.column_stack([
            dq1*s2, dq2*s2, dq3*s2,
            dq1*s3, dq2*s3, dq3*s3,
            dq1*np.sin(q2+q3), dq2*np.sin(q2+q3), dq3*np.sin(q2+q3)
        ])

        # a5 [30:36] — 跨关节三角乘积项
        a5 = np.column_stack([
            s1*c2, c1*s2,
            s1*c2*c3, s1*s2*s3,
            c1*s2*s3, c1*c2*c3
        ])

        # a6 [36:57] — 所有状态变量的二次多项式项
        a6 = np.column_stack([
            q1**2, q2**2, q3**2, dq1**2, dq2**2, dq3**2,
            q1*q2, q1*q3, q1*dq1, q1*dq2, q1*dq3,
            q2*q3, q2*dq1, q2*dq2, q2*dq3,
            q3*dq1, q3*dq2, q3*dq3,
            dq1*dq2, dq1*dq3, dq2*dq3
        ])

        return np.concatenate([a1, a2, a3, a4, a5, a6], axis=1)

    def fit_transform(self, X):
        self.fit(X)
        return self.transform(X)

    def get_C_matrix(self):
        """
        返回降维矩阵 C ∈ R^{6×57}，满足 x = C @ z 严格成立。

        C = [I_6 | 0_{6×51}]
        """
        C = np.zeros((self.n_input, self.n_features))
        C[:, :self.n_input] = np.eye(self.n_input)
        return C

    def get_lifted_dim(self):
        return self.n_features
