"""
多项式升维函数
"""
import numpy as np
from itertools import combinations_with_replacement


class PolynomialLifting:
    """
    多项式升维函数

    将状态向量 x ∈ R^n 升维到多项式特征空间。

    升维结构（保证前 n 个分量就是 x 本身）：
        z = [x_0, x_1, ..., x_{n-1},  x_0^2, x_0*x_1, ..., x_{n-1}^degree]

    不包含常数项，前 n 维精确等于 x，因此降维矩阵：
        C = [I_n | 0_{n×(d-n)}]   ∈ R^{n×d}
    满足 x = C @ z 严格成立，无需最小二乘拟合。
    """

    def __init__(self, degree=2):
        assert degree >= 1, "degree 必须 >= 1"
        self.degree = degree
        self.n_input = None     # 原始状态维度 n
        self.n_features = None  # 升维后总维度 d
        self.feature_names = None

    def fit(self, X):
        """
        记录输入维度，计算输出维度。

        参数:
            X: [N, n]，每行是一个时刻的状态
        """
        n = X.shape[1]
        self.n_input = n
        self.n_features = self._compute_feature_dim(n)
        self.feature_names = self._generate_feature_names(n)
        return self

    def transform(self, X):
        """
        升维变换。

        参数:
            X: [N, n]，每行是一个时刻的状态

        返回:
            Z: [N, d]，前 n 列精确等于 X，后续列为 2 阶及以上多项式特征
        """
        if self.n_features is None:
            self.fit(X)

        N, n = X.shape
        Z = np.zeros((N, self.n_features))

        # 前 n 列：原始状态（1 阶项）
        Z[:, :n] = X

        # 后续列：2 阶及以上
        col_idx = n
        for d in range(2, self.degree + 1):
            for indices in combinations_with_replacement(range(n), d):
                Z[:, col_idx] = np.prod(X[:, indices], axis=1)
                col_idx += 1

        return Z

    def fit_transform(self, X):
        self.fit(X)
        return self.transform(X)

    def get_C_matrix(self):
        """
        返回降维矩阵 C ∈ R^{n×d}，满足 x = C @ z（精确，无需拟合）。

        返回:
            C: ndarray, shape [n, d]
        """
        assert self.n_features is not None, "请先调用 fit() 或 transform()"
        C = np.zeros((self.n_input, self.n_features))
        C[:, :self.n_input] = np.eye(self.n_input)
        return C

    def get_lifted_dim(self):
        return self.n_features

    # ── 内部工具 ────────────────────────────────────────────────

    def _compute_feature_dim(self, n):
        from math import comb
        dim = n  # 1 阶：x 本身
        for d in range(2, self.degree + 1):
            dim += comb(n + d - 1, d)
        return dim

    def _generate_feature_names(self, n):
        names = [f'x{i}' for i in range(n)]
        for d in range(2, self.degree + 1):
            for indices in combinations_with_replacement(range(n), d):
                names.append('*'.join(f'x{i}' for i in indices))
        return names