# -*- coding: utf-8 -*-
"""Gate 1 model library.

Every model exposes the SAME controlled prediction interface so the comparison
is fair (plan section 3):

    predict(xh, uin, ut) -> x_{k+1}          one-step
    rollout(xh0, uin0, uf) -> (H, n)         autoregressive, no future x

where ``xh`` is the P-measurement history ending at k, ``uin`` the P-1 past
inputs (u_k EXCLUDED), ``ut`` the current input u_k, and ``uf`` the known
future inputs u_{k..k+H-1}.

M5 implements the theory faithfully (Theory_Package/01_Model_Definition.md):
    A(c)   = A_0 + U_A diag(gamma_A(c))   V_A^T
    B(chi) = B_0 + U_B diag(gamma_B(chi)) V_B^T ,  chi_k = C_x z_k = x_k
    gamma_{.,j}(s) = g * pi_j(s) * tanh([W s + b]_j),  pi(s) = softmax(W^pi s + b^pi)
    ||u_j||_2 <= 1 and ||v_j||_2 <= 1  (enforced by column reparameterisation)
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import device as _device            # noqa: E402

DEV = _device.current()

# Device-dependent architecture constants (models/device.py).  The soft platform
# keeps the exact values frozen by configs/modeling_protocol.yaml.
N_STATE = int(DEV["n_state"])
N_CTRL = int(DEV["n_ctrl"])
LATENT = int(DEV["latent_dim"])
HIST = int(DEV["history_P"])
PATCH = int(DEV["patch"])
CTX_DIM = int(DEV["ctx_dim"])
CTX_HID = int(DEV["ctx_hidden"])


# ============================================================ shared encoder
class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 512):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        pos = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
        div = torch.exp(torch.arange(0, d_model, 2, dtype=torch.float32)
                        * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, :x.size(1)]


class PatchTSTEncoder(nn.Module):
    """z = [x_k ; h_k],  d = n + n_psi.  C_x = [I_n | 0]."""

    def __init__(self, P=HIST, patch=PATCH, n=N_STATE, latent_dim=LATENT,
                 d_model=16, n_layers=1, n_heads=2, d_ff=64, dropout=0.1,
                 readout="mean"):
        super().__init__()
        if P % patch:
            raise ValueError("history_length must be divisible by patch_length")
        self.P, self.p, self.n = P, patch, n
        self.n_patches = P // patch
        self.d_hist = latent_dim - n
        self.patch_embedding = nn.Linear(patch * n, d_model)
        self.pos = PositionalEncoding(d_model)
        layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=n_heads,
                                           dim_feedforward=d_ff, dropout=dropout,
                                           batch_first=True, activation="gelu")
        self.transformer = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.readout = readout
        self.projection = nn.Linear(d_model, self.d_hist)

    def forward(self, xh):
        b = xh.shape[0]
        patches = xh.reshape(b, self.n_patches, self.p * self.n)
        h = self.patch_embedding(patches)
        h = self.transformer(self.pos(h))
        if self.readout == "mean":
            h = h.mean(dim=1)
        elif self.readout == "max":
            h = h.max(dim=1).values
        else:
            h = h[:, -1, :]
        return torch.cat([xh[:, -1, :], self.projection(h)], dim=1)


class ContextMap(nn.Module):
    """c_k = C_phi(X_k, U_k^in) -> R^{CTX_DIM}.  u_k is not an input."""

    def __init__(self, P=HIST, n=N_STATE, m=N_CTRL, hidden=CTX_HID, out=CTX_DIM):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(P * n + (P - 1) * m, hidden), nn.Tanh(),
                                 nn.Linear(hidden, out), nn.Tanh())

    def forward(self, xh, uin):
        b = xh.shape[0]
        return self.net(torch.cat([xh.reshape(b, -1), uin.reshape(b, -1)], dim=1))


# ================================================== theory-faithful modulation
class LowRankMod(nn.Module):
    """One low-rank branch: Delta = U diag(gamma(s)) V^T with bounded gamma."""

    def __init__(self, in_dim, rows, cols, r=3, gain=0.1):
        super().__init__()
        self.rows, self.cols, self.r = rows, cols, r
        self.gain = gain
        self.W = nn.Linear(in_dim, r)
        self.W_pi = nn.Linear(in_dim, r)
        self.U_raw = nn.Parameter(torch.randn(rows, r) * 0.1)
        self.V_raw = nn.Parameter(torch.randn(cols, r) * 0.1)

    def columns(self):
        u = self.U_raw / (self.U_raw.norm(dim=0, keepdim=True) + 1e-8)
        v = self.V_raw / (self.V_raw.norm(dim=0, keepdim=True) + 1e-8)
        return u, v

    def gamma(self, s):
        pi = torch.softmax(self.W_pi(s), dim=-1)
        return self.gain * pi * torch.tanh(self.W(s))

    def delta(self, s):
        u, v = self.columns()
        g = self.gamma(s)                                  # (B, r)
        return torch.einsum("ir,br,jr->bij", u, g, v)       # (B, rows, cols)


# ================================================== scheduled Koopman models
class ScheduledKoopman(nn.Module):
    """Variants (E-M3): A0B0, AcB0, A0Bx, AcBx.

    AcBx is M5 (the project's main model); AcB0 is M4 (the key ablation).
    A0B0 is the shared base.  A0Bx is M7.
    """

    def __init__(self, variant="AcBx", P=HIST, r_A=3, r_B=3, g_A=0.1, g_B=0.1,
                 **enc_kw):
        super().__init__()
        if variant not in ("A0B0", "AcB0", "A0Bx", "AcBx"):
            raise ValueError(variant)
        self.variant = variant
        self.encoder = PatchTSTEncoder(P=P, **enc_kw)
        self.ctx = ContextMap(P=P)
        self.A0 = nn.Parameter(torch.eye(LATENT) + torch.randn(LATENT, LATENT) * 0.01)
        self.B0 = nn.Parameter(torch.randn(LATENT, N_CTRL) * 0.1)
        if variant in ("AcB0", "AcBx"):
            self.mod_A = LowRankMod(CTX_DIM, LATENT, LATENT, r=r_A, gain=g_A)
        if variant in ("A0Bx", "AcBx"):
            self.mod_B = LowRankMod(N_STATE, LATENT, N_CTRL, r=r_B, gain=g_B)

    # ---- matrices
    def A_of(self, c):
        if self.variant in ("AcB0", "AcBx"):
            return self.A0.unsqueeze(0) + self.mod_A.delta(c)
        return self.A0.unsqueeze(0).expand(c.shape[0], -1, -1)

    def B_of(self, chi):
        if self.variant in ("A0Bx", "AcBx"):
            return self.B0.unsqueeze(0) + self.mod_B.delta(chi)
        return self.B0.unsqueeze(0).expand(chi.shape[0], -1, -1)

    # ---- interface
    def predict(self, xh, uin, ut):
        z = self.encoder(xh)
        c = self.ctx(xh, uin)
        chi = z[:, :N_STATE]                      # C_x z = x_k
        A, B = self.A_of(c), self.B_of(chi)
        zn = torch.bmm(A, z.unsqueeze(-1)).squeeze(-1) + \
            torch.bmm(B, ut.unsqueeze(-1)).squeeze(-1)
        return zn[:, :N_STATE]

    def rollout(self, xh0, uin0, uf):
        """Autoregressive rollout with LATENT PROPAGATION (Theory_Package/01 4.3).

        ``z_0 = encoder(X_0)`` is computed ONCE; then
        ``z_{i+1} = A(c_i) z_i + B(chi_i) u_i`` with ``X_i`` built from the
        PROPAGATED measurements ``C_x z_j`` (true history for ``j < 0``).  The
        encoder is NOT re-applied inside the horizon and no future true
        measurement is ever read -- this is the theory's rollout, and it is what
        the freezing analysis (06 section 2) assumes.
        """
        H = uf.shape[1]
        z = self.encoder(xh0)
        xbuf = xh0.clone()
        ubuf = uin0.clone()
        outs = []
        for i in range(H):
            c = self.ctx(xbuf, ubuf)
            A, B = self.A_of(c), self.B_of(z[:, :N_STATE])
            u = uf[:, i, :]
            z = torch.bmm(A, z.unsqueeze(-1)).squeeze(-1) + \
                torch.bmm(B, u.unsqueeze(-1)).squeeze(-1)
            outs.append(z[:, :N_STATE])
            xbuf = torch.cat([xbuf[:, 1:, :], z[:, :N_STATE].unsqueeze(1)], dim=1)
            ubuf = torch.cat([ubuf[:, 1:, :], u.unsqueeze(1)], dim=1)
        return torch.stack(outs, dim=1)

    @torch.no_grad()
    def nominal_rollout(self, xh0, uin0, ubar):
        """Nominal rollout on the FULL model driven by ``ubar`` (latent propagation).

        Returns ``(z_bar, A_bar, B_bar)`` where ``z_bar[i]`` is the latent state
        BEFORE applying ``ubar[i]`` (so ``z_bar[0] = z_0``), and ``A_bar[i] =
        A(c_bar_i)``, ``B_bar[i] = B(chi_bar_i)`` are the schedules to freeze
        (Theory_Package/06 section 2).
        """
        H = ubar.shape[1]
        z = self.encoder(xh0)
        xbuf = xh0.clone()
        ubuf = uin0.clone()
        zs, As, Bs = [], [], []
        for i in range(H):
            c = self.ctx(xbuf, ubuf)
            A, B = self.A_of(c), self.B_of(z[:, :N_STATE])
            zs.append(z)
            As.append(A)
            Bs.append(B)
            u = ubar[:, i, :]
            z = torch.bmm(A, z.unsqueeze(-1)).squeeze(-1) + \
                torch.bmm(B, u.unsqueeze(-1)).squeeze(-1)
            xbuf = torch.cat([xbuf[:, 1:, :], z[:, :N_STATE].unsqueeze(1)], dim=1)
            ubuf = torch.cat([ubuf[:, 1:, :], u.unsqueeze(1)], dim=1)
        return torch.stack(zs, dim=1), torch.stack(As, dim=1), torch.stack(Bs, dim=1)

    # ---- diagnostics (E-M5)
    @torch.no_grad()
    def diagnostics(self, xh, uin):
        c = self.ctx(xh, uin)
        z = self.encoder(xh)
        chi = z[:, :N_STATE]
        A, B = self.A_of(c), self.B_of(chi)
        out = {
            "A_dev_fro_mean": float((A - self.A0.unsqueeze(0)).flatten(1).norm(dim=1).mean()),
            "A_dev_fro_max": float((A - self.A0.unsqueeze(0)).flatten(1).norm(dim=1).max()),
            "B_dev_fro_mean": float((B - self.B0.unsqueeze(0)).flatten(1).norm(dim=1).mean()),
            "A_dev_spec_max": float(torch.linalg.matrix_norm(A - self.A0.unsqueeze(0), ord=2).max()),
            "B_dev_spec_max": float(torch.linalg.matrix_norm(B - self.B0.unsqueeze(0), ord=2).max()),
            "rho_A_mean": float(torch.linalg.eigvals(A).abs().max(dim=1).values.mean()),
            "rho_A_max": float(torch.linalg.eigvals(A).abs().max(dim=1).values.max()),
            "rho_A0": float(torch.linalg.eigvals(self.A0).abs().max()),
        }
        if self.variant in ("AcB0", "AcBx"):
            g = self.mod_A.gamma(c)
            out["gamma_A_abs_mean"] = float(g.abs().mean())
            out["gamma_A_abs_max"] = float(g.abs().max())
        if self.variant in ("A0Bx", "AcBx"):
            g = self.mod_B.gamma(chi)
            out["gamma_B_abs_mean"] = float(g.abs().mean())
            out["gamma_B_abs_max"] = float(g.abs().max())
        return out


# ================================================== classical baselines
class DMDc(nn.Module):
    """M0: x_{k+1} = A x_k + B u_k, closed-form least squares."""

    def __init__(self, delay=0):
        super().__init__()
        self.delay = delay
        self.A = None
        self.B = None

    def _stack(self, x, u, delay):
        if delay == 0:
            return x, x
        Xs, Us = [], []
        for k in range(delay, len(x)):
            Xs.append(np.concatenate([x[k - j] for j in range(delay + 1)]))
            Us.append(u[k])
        return np.asarray(Xs), np.asarray(Us)

    def fit(self, x, u, tid, ridge=1e-8):
        Xs, Us, Ys = [], [], []
        for t in np.unique(tid):
            m = tid == t
            xs, us = x[m], u[m]
            d = self.delay
            for k in range(d, len(xs) - 1):
                Xs.append(np.concatenate([xs[k - j] for j in range(d + 1)]))
                Us.append(us[k])
                Ys.append(xs[k + 1])
        Z = np.concatenate([np.asarray(Xs), np.asarray(Us)], axis=1)
        Y = np.asarray(Ys)
        K = np.linalg.solve(Z.T @ Z + ridge * np.eye(Z.shape[1]), Z.T @ Y).T
        self.A = K[:, :Z.shape[1] - N_CTRL]
        self.B = K[:, Z.shape[1] - N_CTRL:]
        self.delay = self.delay
        return self

    def predict(self, xh, uin, ut):
        if isinstance(xh, torch.Tensor):
            xh_t = xh
            b = xh_t.shape[0]
            if self.delay == 0:
                xk = xh_t[:, -1, :]
            else:
                xk = torch.cat([xh_t[:, -1 - j, :] for j in range(self.delay + 1)], dim=1)
            A = torch.as_tensor(self.A, dtype=xh_t.dtype, device=xh_t.device)
            B = torch.as_tensor(self.B, dtype=xh_t.dtype, device=xh_t.device)
            return xk @ A.T + ut @ B.T
        raise TypeError

    def rollout(self, xh0, uin0, uf):
        H = uf.shape[1]
        xh = xh0.clone()
        uin = uin0.clone()
        outs = []
        for h in range(H):
            ut = uf[:, h, :]
            xn = self.predict(xh, uin, ut)
            outs.append(xn)
            xh = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
            uin = torch.cat([uin[:, 1:, :], ut.unsqueeze(1)], dim=1)
        return torch.stack(outs, dim=1)


def poly2(x):
    """[x, upper-triangular quadratic terms] -> measurement-preserving lifting."""
    b = x.shape[0]
    q = []
    for i in range(x.shape[1]):
        for j in range(i, x.shape[1]):
            q.append((x[:, i] * x[:, j]).unsqueeze(1))
    return torch.cat([x] + q, dim=1)


def rbf_features(x, centers, sigma):
    c = centers.to(device=x.device, dtype=x.dtype)
    d = ((x.unsqueeze(1) - c.unsqueeze(0)) ** 2).sum(-1)
    return torch.exp(-d / (2 * sigma ** 2))


class EDMDc(nn.Module):
    """M1: fixed dictionary (identity + poly2 [+ RBF]) with ridge least squares."""

    def __init__(self, n_rbf=0, sigma=1.0, ridge=1e-6, seed=0):
        super().__init__()
        self.n_rbf, self.sigma, self.ridge = n_rbf, sigma, ridge
        self.centers = None
        self.A = self.B = None
        self.seed = seed

    def lift(self, x):
        parts = [poly2(x)]
        if self.n_rbf:
            parts.append(rbf_features(x, self.centers, self.sigma))
        return torch.cat(parts, dim=1)

    def fit(self, x, u, tid):
        if self.n_rbf:
            rng = np.random.default_rng(self.seed)
            idx = rng.choice(len(x), size=min(self.n_rbf, len(x)), replace=False)
            self.centers = torch.as_tensor(x[idx], dtype=torch.float32)
        Xs, Us, Ys = [], [], []
        for t in np.unique(tid):
            m = tid == t
            xs, us = torch.as_tensor(x[m], dtype=torch.float32), torch.as_tensor(u[m], dtype=torch.float32)
            for k in range(HIST - 1, len(xs) - 1):
                Xs.append(self.lift(xs[k:k + 1]))
                Us.append(us[k:k + 1])
                Ys.append(self.lift(xs[k + 1:k + 2]))
        Z = torch.cat([torch.cat(Xs), torch.cat(Us)], dim=1)
        Y = torch.cat(Ys)
        K = torch.linalg.solve(
            Z.T @ Z + self.ridge * torch.eye(Z.shape[1], device=Z.device, dtype=Z.dtype),
            Z.T @ Y).T
        self.A = K[:, :Z.shape[1] - N_CTRL]
        self.B = K[:, Z.shape[1] - N_CTRL:]
        return self

    def predict(self, xh, uin, ut):
        xk = xh[:, -1, :]
        z = self.lift(xk)
        A = self.A.to(xh.device)
        B = self.B.to(xh.device)
        return (z @ A.T + ut @ B.T)[:, :N_STATE]

    def rollout(self, xh0, uin0, uf):
        H = uf.shape[1]
        xh, uin, outs = xh0.clone(), uin0.clone(), []
        for h in range(H):
            ut = uf[:, h, :]
            xn = self.predict(xh, uin, ut)
            outs.append(xn)
            xh = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
            uin = torch.cat([uin[:, 1:, :], ut.unsqueeze(1)], dim=1)
        return torch.stack(outs, dim=1)


class EDMDDL(nn.Module):
    """M2: learnable dictionary psi_theta(x) = [x ; MLP(x)] with linear latent
    dynamics z+ = A z + B u.  Alternating scheme: (a) least-squares fit of A,B on
    the current encoder, (b) gradient steps on the encoder with A,B frozen.
    This controlled extension is project-specific (plan section 3.2)."""

    def __init__(self, d_lift=16, hidden=32, ridge=1e-6, seed=0):
        super().__init__()
        self.mlp = nn.Sequential(nn.Linear(N_STATE, hidden), nn.Tanh(),
                                 nn.Linear(hidden, d_lift - N_STATE))
        self.A = nn.Parameter(torch.zeros(d_lift, d_lift))
        self.B = nn.Parameter(torch.zeros(d_lift, N_CTRL))
        self.ridge = ridge
        self.d_lift = d_lift

    def lift(self, x):
        return torch.cat([x, self.mlp(x)], dim=1)

    @torch.no_grad()
    def refit_linear(self, Z, U, Y):
        M = torch.cat([Z, U], dim=1)
        K = torch.linalg.solve(M.T @ M + self.ridge * torch.eye(M.shape[1], device=M.device, dtype=M.dtype), M.T @ Y).T
        self.A.copy_(K[:, :self.d_lift])
        self.B.copy_(K[:, self.d_lift:])

    def predict(self, xh, uin, ut):
        z = self.lift(xh[:, -1, :])
        return (z @ self.A.T + ut @ self.B.T)[:, :N_STATE]

    def rollout(self, xh0, uin0, uf):
        H = uf.shape[1]
        xh, uin, outs = xh0.clone(), uin0.clone(), []
        for h in range(H):
            ut = uf[:, h, :]
            xn = self.predict(xh, uin, ut)
            outs.append(xn)
            xh = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
            uin = torch.cat([uin[:, 1:, :], ut.unsqueeze(1)], dim=1)
        return torch.stack(outs, dim=1)


class RecurrentPredictor(nn.Module):
    """M3: GRU/LSTM over (x_t, u_t) tokens; hidden state from the past only;
    future control inputs are fed step by step during rollout."""

    def __init__(self, cell="gru", hidden=64, layers=1, dropout=0.0):
        super().__init__()
        cls = nn.GRU if cell == "gru" else nn.LSTM
        self.rnn = cls(input_size=N_STATE + N_CTRL, hidden_size=hidden,
                       num_layers=layers, batch_first=True,
                       dropout=dropout if layers > 1 else 0.0)
        self.head = nn.Sequential(nn.Linear(hidden, hidden), nn.Tanh(),
                                  nn.Linear(hidden, N_STATE))

    def _step(self, h, x, u):
        tok = torch.cat([x, u], dim=-1).unsqueeze(1)
        out, h = self.rnn(tok, h)
        return self.head(out[:, -1, :]), h

    def encode_history(self, xh, uin, ut):
        """Warm the hidden state with the history tokens, then take one step
        with the current input."""
        b = xh.shape[0]
        P = xh.shape[1]
        # tokens: (x_{k-P+1}, u_{k-P+1}) ... (x_{k-1}, u_{k-1})  -> P-1 tokens;
        # u_k is excluded from the warm-up so every model sees the same
        # information set (history ending at k-1 plus u_k applied once).
        toks = torch.cat([xh[:, :-1, :], uin], dim=-1)
        out, h = self.rnn(toks, None)
        return self._step(h, xh[:, -1, :], ut)

    def predict(self, xh, uin, ut):
        return self.encode_history(xh, uin, ut)[0]

    def rollout(self, xh0, uin0, uf):
        H = uf.shape[1]
        xh, uin, outs = xh0.clone(), uin0.clone(), []
        for h in range(H):
            ut = uf[:, h, :]
            xn, _ = self.encode_history(xh, uin, ut)
            outs.append(xn)
            xh = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
            uin = torch.cat([uin[:, 1:, :], ut.unsqueeze(1)], dim=1)
        return torch.stack(outs, dim=1)


class ControlledTransformer(nn.Module):
    """M6: Transformer encoder over history tokens [x_t, u_t] + control-conditioned
    head; rollout appends predicted measurements with the known future inputs.

    The encoder is BIDIRECTIONAL over the history window (no causal mask is passed
    to ``nn.TransformerEncoder``).  This is not a leakage -- every token in the
    window is built from quantities at or before k -- but it is a different
    inductive bias from M3's strictly causal recurrence and is described as such.
    """

    def __init__(self, d_model=32, n_layers=2, n_heads=2, d_ff=64, dropout=0.1,
                 max_len=256):
        super().__init__()
        self.embed = nn.Linear(N_STATE + N_CTRL, d_model)
        self.pos = PositionalEncoding(d_model, max_len=max_len)
        layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=n_heads,
                                           dim_feedforward=d_ff, dropout=dropout,
                                           batch_first=True, activation="gelu")
        self.encoder = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.head = nn.Sequential(nn.Linear(d_model, d_ff), nn.Tanh(),
                                  nn.Linear(d_ff, N_STATE))

    def _tokens(self, xh, uin, ut):
        xs = xh[:, :-1, :]
        us = uin
        return torch.cat([xs, us], dim=-1)

    def predict(self, xh, uin, ut):
        toks = self.embed(self._tokens(xh, uin, ut))
        h = self.encoder(self.pos(toks))
        return self.head(h[:, -1, :])

    def rollout(self, xh0, uin0, uf):
        H = uf.shape[1]
        xh, uin, outs = xh0.clone(), uin0.clone(), []
        for h in range(H):
            ut = uf[:, h, :]
            xn = self.predict(xh, uin, ut)
            outs.append(xn)
            xh = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
            uin = torch.cat([uin[:, 1:, :], ut.unsqueeze(1)], dim=1)
        return torch.stack(outs, dim=1)


# ================================================== factory
def build_model(spec: str, seed: int = 0, **kw):
    torch.manual_seed(seed)
    if spec == "M0":
        return DMDc(delay=kw.get("delay", 0))
    if spec == "M1":
        return EDMDc(n_rbf=kw.get("n_rbf", 0), sigma=kw.get("sigma", 1.0),
                     ridge=kw.get("ridge", 1e-6), seed=seed)
    if spec == "M2":
        return EDMDDL(d_lift=kw.get("d_lift", 16), hidden=kw.get("hidden", 32),
                      ridge=kw.get("ridge", 1e-6), seed=seed)
    if spec == "M3":
        return RecurrentPredictor(cell=kw.get("cell", "gru"), hidden=kw.get("hidden", 64),
                                  layers=kw.get("layers", 1))
    if spec in ("M4", "M5", "M7", "M_base"):
        variant = {"M4": "AcB0", "M5": "AcBx", "M7": "A0Bx", "M_base": "A0B0"}[spec]
        return ScheduledKoopman(variant=variant, r_A=kw.get("r_A", 3), r_B=kw.get("r_B", 3),
                                g_A=kw.get("g_A", 0.1), g_B=kw.get("g_B", 0.1),
                                d_model=kw.get("d_model", 16), n_layers=kw.get("n_layers", 1),
                                n_heads=kw.get("n_heads", 2), d_ff=kw.get("d_ff", 64),
                                dropout=kw.get("dropout", 0.1))
    if spec == "M6":
        return ControlledTransformer(d_model=kw.get("d_model", 32), n_layers=kw.get("n_layers", 2),
                                     n_heads=kw.get("n_heads", 2), d_ff=kw.get("d_ff", 64),
                                     dropout=kw.get("dropout", 0.1))
    raise ValueError("unknown model spec %r" % spec)


def n_params(model) -> int:
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))
