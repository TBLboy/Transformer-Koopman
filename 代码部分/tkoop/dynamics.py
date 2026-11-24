"""转移矩阵的来源：固定的 (A_0, B_0)，或随调度上下文变化的 (A(c), B(c))。

本模块不保存滚动状态；滚动由 predictor.Predictor.rollout 负责。
"""
from __future__ import annotations

import torch
from torch import nn
from torch.nn.utils import parametrizations

from .lifting import HistoryEncoder, mlp


class Nominal(nn.Module):
    """名义矩阵 A_0 [d, d] 与 B_0 [d, m]。初值取 A_0 = I、B_0 = 0，即"下一步等于当前"。"""

    def __init__(self, d: int, m: int):
        super().__init__()
        self.A0 = nn.Parameter(torch.eye(d))
        self.B0 = nn.Parameter(torch.zeros(d, m))


class FixedDynamics(nn.Module):
    scheduled = False
    encoder = None

    def __init__(self, nominal: Nominal):
        super().__init__()
        self.nominal = nominal


class _Orth(nn.Module):
    """列正交的矩阵 [rows, cols]（rows >= cols），由 PyTorch 的正交参数化保证。"""

    def __init__(self, rows: int, cols: int):
        super().__init__()
        self.weight = nn.Parameter(torch.randn(rows, cols))
        parametrizations.orthogonal(self, "weight")


class ScheduledDynamics(nn.Module):
    """调度矩阵（论文式 eq:fused_context、eq:scheduled_A、eq:scheduled_B、eq:scheduling_function）。

    A(c) = A_0 + U_A diag(γ_A(c)) V_A^T，B(c) = B_0 + U_B diag(γ_B(c)) V_B^T，
    γ_{χ,j}(c) = g_χ · softmax(W_χ^π c + b_χ^π)_j · tanh([W_χ c + b_χ]_j)。
    低秩因子列正交，因此修正的 2-范数等于 max_j |γ_{χ,j}|，不超过 g_χ。

    三个开关对应消融：
      use_input_ctx  上下文是否包含过去输入特征 e^u = M_η(v)；
      ctx_update     every_step 沿预测历史逐步重算上下文，once 只在起点算一次；
      encoder        给出时调度自带历史编码器，否则与提升映射共用。
    """

    scheduled = True

    def __init__(self, nominal: Nominal, n: int, d: int, m: int, P_h: int, d_model: int | None, *,
                 r_A: int, r_B: int, g_A: float, g_B: float, d_u: int, d_c: int, hidden: int,
                 use_input_ctx: bool = True, ctx_update: str = "every_step", encoder: dict | None = None):
        super().__init__()
        if not 1 <= r_A <= d:
            raise ValueError(f"要求 1 <= r_A <= d，当前 r_A = {r_A}，d = {d}")
        if not 1 <= r_B <= min(d, m):
            raise ValueError(f"要求 1 <= r_B <= min(d, m)，当前 r_B = {r_B}，min(d, m) = {min(d, m)}")
        self.nominal = nominal
        self.use_input_ctx, self.ctx_update = use_input_ctx, ctx_update
        self.encoder = HistoryEncoder(n, P_h, **encoder) if encoder else None
        e_dim = encoder["d_model"] if encoder else d_model
        self.input_enc = mlp([(P_h - 1) * m, hidden, d_u]) if use_input_ctx else None  # M_η
        self.fusion = mlp([e_dim + (d_u if use_input_ctx else 0), hidden, d_c])  # H_φ
        self.pi_A, self.amp_A = nn.Linear(d_c, r_A), nn.Linear(d_c, r_A)
        self.pi_B, self.amp_B = nn.Linear(d_c, r_B), nn.Linear(d_c, r_B)
        for amp in (self.amp_A, self.amp_B):  # 幅值头置零：训练起点恰好是名义模型
            nn.init.zeros_(amp.weight)
            nn.init.zeros_(amp.bias)
        self.U_A, self.V_A = _Orth(d, r_A), _Orth(d, r_A)
        self.U_B, self.V_B = _Orth(d, r_B), _Orth(m, r_B)
        self.register_buffer("g_A", torch.tensor(float(g_A)))
        self.register_buffer("g_B", torch.tensor(float(g_B)))

    def factors(self):
        """低秩因子。每次访问都会重算正交参数化，所以一次滚动只取一次。"""
        return self.U_A.weight, self.V_A.weight, self.U_B.weight, self.V_B.weight

    def context(self, e_x: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
        """c = H_φ(col(e^x, e^u))。v 是过去输入窗口 [B, P_h-1, m]。"""
        feats = [e_x]
        if self.use_input_ctx:
            feats.append(self.input_enc(v.flatten(1)))
        return self.fusion(torch.cat(feats, -1))

    def gamma(self, c: torch.Tensor):
        gA = self.g_A * torch.softmax(self.pi_A(c), -1) * torch.tanh(self.amp_A(c))
        gB = self.g_B * torch.softmax(self.pi_B(c), -1) * torch.tanh(self.amp_B(c))
        return gA, gB

    def matrices(self, c: torch.Tensor, factors):
        """返回 A(c) [B, d, d] 与 B(c) [B, d, m]。"""
        U_A, V_A, U_B, V_B = factors
        gA, gB = self.gamma(c)
        A = self.nominal.A0 + torch.einsum("ir,br,jr->bij", U_A, gA, V_A)
        B = self.nominal.B0 + torch.einsum("ir,br,jr->bij", U_B, gB, V_B)
        return A, B

    def scheduling_parameters(self) -> list[nn.Parameter]:
        """阶段二"仅调度"时更新的参数：除名义矩阵外的全部参数。"""
        return [p for name, p in self.named_parameters() if not name.startswith("nominal.")]


def build_dynamics(cfg: dict, nominal: Nominal, n: int, d: int, m: int, P_h: int, lifting_cfg: dict) -> nn.Module:
    if cfg["kind"] == "fixed":
        return FixedDynamics(nominal)
    kw = {k: v for k, v in cfg.items() if k != "kind"}
    return ScheduledDynamics(nominal, n, d, m, P_h, lifting_cfg.get("d_model"), **kw)
