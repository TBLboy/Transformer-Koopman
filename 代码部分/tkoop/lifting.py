"""特征映射 ψ：提升状态是 z = col(x_k, ψ(X_k))，这里只负责 ψ。

统一接口：forward(X) 的输入是测量窗口 X [B, P_h, n]（最后一行是当前测量 x_k），输出 [B, d-n]。
五种映射都只读测量，不读过去输入。
"""
from __future__ import annotations

import math

import torch
from torch import nn


def mlp(sizes: list[int]) -> nn.Sequential:
    layers: list[nn.Module] = []
    for i in range(len(sizes) - 1):
        layers.append(nn.Linear(sizes[i], sizes[i + 1]))
        if i < len(sizes) - 2:
            layers.append(nn.GELU())
    return nn.Sequential(*layers)


def tps(x: torch.Tensor, centers: torch.Tensor) -> torch.Tensor:
    """薄板样条径向基 r^2 log r。x [B, n]，centers [K, n]，输出 [B, K]。"""
    r2 = (x[:, None, :] - centers[None, :, :]).pow(2).sum(-1)
    return 0.5 * torch.xlogy(r2, r2)


def kmeans(x: torch.Tensor, k: int, seed: int, iters: int = 100) -> torch.Tensor:
    """k 均值聚类（k-means++ 初始化），返回中心 [k, n]。"""
    x = x.double()
    gen = torch.Generator().manual_seed(seed)
    centers = x[torch.randint(len(x), (1,), generator=gen)]
    for _ in range(k - 1):
        d2 = torch.cdist(x, centers).pow(2).min(1).values
        probs = d2 / d2.sum() if d2.sum() > 0 else torch.full_like(d2, 1.0 / len(d2))
        centers = torch.cat([centers, x[torch.multinomial(probs, 1, generator=gen)]])
    for _ in range(iters):
        assign = torch.cdist(x, centers).argmin(1)
        new = centers.clone()
        for j in range(k):
            members = x[assign == j]
            if len(members):
                new[j] = members.mean(0)
        if torch.allclose(new, centers):
            break
        centers = new
    return centers


class _Fitted(nn.Module):
    """由训练集拟合、之后固定的映射。未拟合就使用时报错。"""

    def __init__(self):
        super().__init__()
        self.register_buffer("fitted", torch.tensor(False))

    def _check(self):
        if not bool(self.fitted):
            raise RuntimeError(f"{type(self).__name__} 尚未用训练集拟合")


class RBFLift(_Fitted):
    """EDMDc 的字典：ψ(x_k) = col(薄板样条径向基 × (d-n-1), 1)。中心是训练集测量的聚类结果。"""

    def __init__(self, n: int, d: int):
        super().__init__()
        if d - n - 1 < 1:
            raise ValueError("RBF 字典要求 d >= n + 2")
        self.register_buffer("centers", torch.zeros(d - n - 1, n))

    def fit(self, X: torch.Tensor, seed: int) -> None:
        self.centers.copy_(kmeans(X[:, -1], self.centers.shape[0], seed).float())
        self.fitted.fill_(True)

    def forward(self, X: torch.Tensor) -> torch.Tensor:
        self._check()
        x = X[:, -1]
        return torch.cat([tps(x, self.centers), torch.ones_like(x[:, :1])], -1)


class DelayPCALift(_Fitted):
    """延迟坐标：ψ 是测量历史的线性投影。

    延迟量取相对当前测量的差 x_{k-j} - x_k（j = 1..P_h-1），与 x_k 合起来张成整个延迟向量；
    对它做不去均值的主成分分解并按奇异值缩放，取前 n_pca 个方向。历史维数不够时用薄板样条径向基补足。
    """

    def __init__(self, n: int, d: int, P_h: int, n_rbf: int = 0):
        super().__init__()
        q_max = n * (P_h - 1)
        self.n_pca = min(d - n - n_rbf, q_max)
        self.n_rbf = d - n - self.n_pca
        if self.n_pca < 0:
            raise ValueError("n_rbf 不能超过 d - n")
        self.register_buffer("W", torch.zeros(q_max, self.n_pca))
        self.register_buffer("centers", torch.zeros(self.n_rbf, n))

    @staticmethod
    def _delays(X: torch.Tensor) -> torch.Tensor:
        return (X[:, :-1] - X[:, -1:]).flatten(1)

    def fit(self, X: torch.Tensor, seed: int) -> None:
        D = self._delays(X).double()
        if self.n_pca:
            _, S, Vh = torch.linalg.svd(D, full_matrices=False)
            # With a small fitting batch, the requested number of components can
            # exceed the available SVD rank.  Keep the configured output width and
            # leave the unavailable directions at zero instead of failing on copy.
            rank = min(self.n_pca, Vh.shape[0])
            W = torch.zeros_like(self.W)
            if rank:
                scale = (S[:rank] / math.sqrt(len(D))).clamp_min(1e-12)
                W[:, :rank] = Vh[:rank].T / scale
            self.W.copy_(W.float())
        if self.n_rbf:
            self.centers.copy_(kmeans(X[:, -1], self.n_rbf, seed).float())
        self.fitted.fill_(True)

    def forward(self, X: torch.Tensor) -> torch.Tensor:
        self._check()
        feats = [self._delays(X) @ self.W]
        if self.n_rbf:
            feats.append(tps(X[:, -1], self.centers))
        return torch.cat(feats, -1)


class MLPLift(nn.Module):
    """Deep Koopman 的提升：ψ = MLP(x_k)。"""

    def __init__(self, n: int, d: int, hidden: int, layers: int):
        super().__init__()
        self.net = mlp([n] + [hidden] * layers + [d - n])

    def forward(self, X: torch.Tensor) -> torch.Tensor:
        return self.net(X[:, -1])


class LSTMLift(nn.Module):
    """LSTM-Koopman 的提升：LSTM 按时间顺序读入测量窗口，末步隐状态经线性层得到 ψ。"""

    def __init__(self, n: int, d: int, hidden: int, layers: int):
        super().__init__()
        self.lstm = nn.LSTM(n, hidden, layers, batch_first=True)
        self.head = nn.Linear(hidden, d - n)

    def forward(self, X: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(X)
        return self.head(out[:, -1])


def sinusoidal(length: int, dim: int) -> torch.Tensor:
    pos = torch.arange(length, dtype=torch.float32)[:, None]
    div = torch.exp(-math.log(10000.0) * torch.arange(0, dim, 2, dtype=torch.float32) / dim)
    pe = torch.zeros(length, dim)
    pe[:, 0::2] = torch.sin(pos * div)
    pe[:, 1::2] = torch.cos(pos * div)[:, : dim // 2]
    return pe


class HistoryEncoder(nn.Module):
    """测量历史编码器：patch 嵌入、正弦位置编码、Transformer 编码器、平均池化。

    对应论文式 eq:patch_embedding、eq:transformer_encoder、eq:pooled_history_feature，输出 e^x [B, d_model]。
    """

    def __init__(self, n: int, P_h: int, patch: int, d_model: int, n_heads: int, n_layers: int,
                 d_ff: int, dropout: float = 0.0):
        super().__init__()
        if P_h % patch != 0:
            raise ValueError("patch 长度必须整除 P_h")
        self.n_patches, self.patch_dim, self.d_model = P_h // patch, patch * n, d_model
        self.embed = nn.Linear(self.patch_dim, d_model)
        self.register_buffer("pe", sinusoidal(self.n_patches, d_model))
        layer = nn.TransformerEncoderLayer(d_model, n_heads, d_ff, dropout, batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, n_layers, enable_nested_tensor=False)

    def forward(self, X: torch.Tensor) -> torch.Tensor:
        tokens = self.embed(X.reshape(X.shape[0], self.n_patches, self.patch_dim)) + self.pe
        return self.encoder(tokens).mean(1)


class TransformerLift(nn.Module):
    """本文的历史提升：ψ = W_h e^x + b_h（论文式 eq:lifting_head）。encode 给出与调度上下文共用的 e^x。"""

    def __init__(self, n: int, d: int, P_h: int, **encoder_kwargs):
        super().__init__()
        self.encoder = HistoryEncoder(n, P_h, **encoder_kwargs)
        self.head = nn.Linear(self.encoder.d_model, d - n)

    def encode(self, X: torch.Tensor) -> torch.Tensor:
        return self.encoder(X)

    def forward(self, X: torch.Tensor) -> torch.Tensor:
        return self.head(self.encode(X))


def build_lifting(cfg: dict, n: int, d: int, P_h: int) -> nn.Module:
    kw = {k: v for k, v in cfg.items() if k != "kind"}
    kind = cfg["kind"]
    if kind == "rbf":
        return RBFLift(n, d)
    if kind == "delay_pca":
        return DelayPCALift(n, d, P_h, **kw)
    if kind == "mlp":
        return MLPLift(n, d, **kw)
    if kind == "lstm":
        return LSTMLift(n, d, **kw)
    if kind == "transformer":
        return TransformerLift(n, d, P_h, **kw)
    raise ValueError(f"未知的提升类型：{kind}")
