"""预测器：特征映射加矩阵来源，以及唯一的滚动预测实现（论文定义 1）。"""
from __future__ import annotations

import torch
from torch import nn

from .dynamics import FixedDynamics, Nominal, build_dynamics
from .lifting import build_lifting


class Predictor(nn.Module):
    def __init__(self, lifting: nn.Module, dynamics: nn.Module, n: int):
        super().__init__()
        self.lifting, self.dynamics, self.n = lifting, dynamics, n

    def lift(self, X: torch.Tensor, e: torch.Tensor | None = None) -> torch.Tensor:
        """z = col(x_k, ψ(X))。前 n 维恒等于当前测量，C_x = [I_n 0]。e 是已算好的 e^x，可省一次编码。"""
        psi = self.lifting(X) if e is None else self.lifting.head(e)
        return torch.cat([X[:, -1], psi], -1)

    def rollout(self, X0: torch.Tensor, v0: torch.Tensor, U: torch.Tensor, return_matrices: bool = False):
        """从真实历史 (X0, v0) 出发，在输入序列 U 下自由滚动 H 步。

        X0 [B, P_h, n]，v0 [B, P_h-1, m]，U [B, H, m]。
        返回预测测量 xhat [B, H, n] 和提升状态 z [B, H, d]；return_matrices 为真时再返回
        每步的 A [B, H, d, d] 和 B [B, H, d, m]。

        提升状态只在起点编码一次，之后由矩阵递推；调度上下文按预测出的测量历史更新。
        """
        dyn, n = self.dynamics, self.n
        scheduled = dyn.scheduled
        shared_encoder = scheduled and dyn.encoder is None
        e = self.lifting.encode(X0) if shared_encoder else None
        z = self.lift(X0, e)
        X, v, c = X0, v0, None
        factors = dyn.factors() if scheduled else None
        A0, B0 = dyn.nominal.A0, dyn.nominal.B0
        xs, zs, As, Bs = [], [], [], []
        for i in range(U.shape[1]):
            u = U[:, i]
            if scheduled:
                if c is None or dyn.ctx_update == "every_step":
                    if e is None:
                        e = self.lifting.encode(X) if shared_encoder else dyn.encoder(X)
                    c, e = dyn.context(e, v), None
                A, B = dyn.matrices(c, factors)
                z = torch.einsum("bij,bj->bi", A, z) + torch.einsum("bij,bj->bi", B, u)
                X = torch.cat([X[:, 1:], z[:, None, :n]], 1)
                v = torch.cat([v[:, 1:], u[:, None]], 1)
            else:
                A, B = A0, B0
                z = z @ A0.T + u @ B0.T
            xs.append(z[:, :n])
            zs.append(z)
            if return_matrices:
                As.append(A if A.dim() == 3 else A.expand(len(z), -1, -1))
                Bs.append(B if B.dim() == 3 else B.expand(len(z), -1, -1))
        out = (torch.stack(xs, 1), torch.stack(zs, 1))
        if return_matrices:
            out += (torch.stack(As, 1), torch.stack(Bs, 1))
        return out


def build_predictor(cfg: dict, n: int, m: int, nominal_only: bool = False) -> Predictor:
    """按配置组装预测器。nominal_only 为真时关闭调度，得到阶段一训练的名义模型。"""
    d, P_h = cfg["shared"]["d"], cfg["shared"]["P_h"]
    lifting = build_lifting(cfg["lifting"], n, d, P_h)
    nominal = Nominal(d, m)
    if nominal_only:
        return Predictor(lifting, FixedDynamics(nominal), n)
    return Predictor(lifting, build_dynamics(cfg["dynamics"], nominal, n, d, m, P_h, cfg["lifting"]), n)
