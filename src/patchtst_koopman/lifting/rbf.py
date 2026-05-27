"""
RBF升维函数
"""
import numpy as np


class RBFLifting:
    """
    RBF升维函数

    使用高斯RBF基函数将状态向量升维
    z = [1, exp(-||x-c1||^2/sigma^2), exp(-||x-c2||^2/sigma^2), ...]
    """

    def __init__(self, n_centers=10, sigma=1.0, centers=None):
        """
        参数:
            n_centers: RBF中心点数量
            sigma: RBF宽度参数
            centers: 预定义的中心点 [n_centers, n]
        """
        self.n_centers = n_centers
        self.sigma = sigma
        self.centers = centers
        self.n_features = None

    def fit(self, X):
        """
        拟合升维函数（选择RBF中心点）

        参数:
            X: 输入数据 [N, n]
        """
        N, n = X.shape

        # 如果没有预定义中心点，则从数据中随机选择
        if self.centers is None:
            indices = np.random.choice(N, self.n_centers, replace=False)
            self.centers = X[indices, :]

        self.n_features = 1 + self.n_centers  # 1个常数项 + n_centers个RBF基函数
        return self

    def transform(self, X):
        """
        升维变换

        参数:
            X: 输入数据 [N, n]

        返回:
            升维后的数据 [N, d]
        """
        if self.centers is None:
            self.fit(X)

        N = X.shape[0]
        Z = np.ones((N, self.n_features))

        # 计算RBF基函数
        for i in range(self.n_centers):
            dist_sq = np.sum((X - self.centers[i, :]) ** 2, axis=1)
            Z[:, i + 1] = np.exp(-dist_sq / (self.sigma ** 2))

        return Z

    def fit_transform(self, X):
        """拟合并变换"""
        self.fit(X)
        return self.transform(X)

    def get_lifted_dim(self):
        """获取升维后的维度"""
        return self.n_features
