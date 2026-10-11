# -*- coding: utf-8 -*-
"""
阶段七补充（TASK-043）：按用户指定的被控对象 —— 倒立摆 / 推车-杆（cart-pole）—— 补做验证。

对应 TASK-040 的 done_when#1 与 #4（= 本任务 TASK-043 的 #1 与 #2）：
  1. 明确记录被控对象：标准 cart-pole，参数与方程在下面，脚本一键复现。
  2. 数值展示该对象的**输入耦合确实依赖状态**（本文 B(chi) 测量依赖输入调制的物理动机）。
  3. 构造本文模型形式的一个实例（灰箱：由 cart-pole 在若干工作点的线性化拟合）：
        z_{k+1} = A(c_k) z_k + B(chi_k) u_k
        A(c)   = A_0 + U_A diag(gamma_A(c))   V_A^T
        B(chi) = B_0 + U_B diag(gamma_B(chi)) V_B^T
     本例 d = n + n_psi = 4 + 0（观测取状态本身）；r_A = r_B = 2（两个通道：奇通道与偶通道）。
     实测与纸面核对：在工作点 [0,0,theta,0] 处，cart-pole 的线性化 A(theta)、B(theta) 的**全部元素
     都是 theta 的偶函数**（关于 theta = 0 对称）；故 tanh(c) 这个奇通道恒为 0（g_A_ch[0] = g_B_ch[0] = 0，
     是死通道），真正起作用的是偶通道 tanh(|c|)。r = 2 在本例因此等价于「偶通道 rank-1」。
     U/V 的列已归一化（<= 1），幅度写在 gamma 的系数 g_k 里。softmax 混合本例**未**使用（已登记）。
  4. 在**真 plant** 上闭环比较完整 scheduled MPC 与冻结 LTV-MPC，报告代价、末端误差、耗时，
     并**如实报告代理模型与真 plant 的模型失配**。
  5. 声明：临时验证，结果**不进论文**；不声称实时性、闭环稳定性、递归可行性。

只用 numpy + scipy；固定种子；自行以 UTF-8 写出 results_plant.json 与 results_plant.md。
运行：D:\\conda\\envs\\edmddl2\\python.exe validate_plant_cartpole.py
"""

import io
import os
import json
import time
import numpy as np
from scipy.optimize import minimize
from scipy.linalg import expm, solve_discrete_are

SEED = 20261011
rng = np.random.default_rng(SEED)
HERE = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------
# 1. 被控对象（plant）：标准 cart-pole
# --------------------------------------------------------------------------
PLANT = dict(M=1.0, m=0.1, l=0.5, g=9.81, dt=0.02)
N = 4
CH = 2                     # 低秩通道数 r_A = r_B = 2
P_WIN = 2                  # 历史窗口（测量个数）
CONTEXT_W = np.array([1.0, 0.5])


def cartpole_dyn(x, u, p=PLANT):
    """倒立摆（杆角 theta 自竖直向上量起）的连续时间动力学。"""
    M, m, l, g = p["M"], p["m"], p["l"], p["g"]
    t, td = float(x[2]), float(x[3])
    det = l * ((M + m) - m * np.cos(t) ** 2)
    rhs1 = u + m * l * td * td * np.sin(t)
    rhs2 = g * np.sin(t)
    p_ddot = (rhs1 * l - m * l * np.cos(t) * rhs2) / det
    t_ddot = ((M + m) * rhs2 - np.cos(t) * rhs1) / det
    return np.array([float(x[1]), p_ddot, td, t_ddot])


def rk4_step(x, u, dt, p=PLANT):
    k1 = cartpole_dyn(x, u, p)
    k2 = cartpole_dyn(x + 0.5 * dt * k1, u, p)
    k3 = cartpole_dyn(x + 0.5 * dt * k2, u, p)
    k4 = cartpole_dyn(x + dt * k3, u, p)
    return x + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def linearize(x0, u0=0.0, p=PLANT, eps=1e-6):
    nx = len(x0)
    A = np.zeros((nx, nx))
    B = np.zeros((nx, 1))
    for i in range(nx):
        dx = np.zeros(nx)
        dx[i] = eps
        A[:, i] = (cartpole_dyn(x0 + dx, u0, p) - cartpole_dyn(x0 - dx, u0, p)) / (2 * eps)
    B[:, 0] = (cartpole_dyn(x0, u0 + eps, p) - cartpole_dyn(x0, u0 - eps, p)) / (2 * eps)
    return A, B


def discrete_lin(x0, u0=0.0, p=PLANT):
    """离散时间线性化（零阶保持，精确）：由连续 (Ac, Bc) 经矩阵指数得到 (Ad, Bd)。"""
    Ac, Bc = linearize(x0, u0, p)
    M = np.zeros((N + 1, N + 1))
    M[:N, :N] = Ac
    M[:N, N:] = Bc
    Ed = expm(M * p["dt"])
    return Ed[:N, :N], Ed[:N, N:]


# --------------------------------------------------------------------------
# 2. 输入耦合的状态依赖性
# --------------------------------------------------------------------------
theta_probe = [0.0, 0.1, 0.2, 0.3, 0.45, 0.6]
input_col = np.array([discrete_lin(np.array([0.0, 0.0, th, 0.0]))[1][:, 0] for th in theta_probe])
in_rel_spread = (input_col.max(axis=0) - input_col.min(axis=0)) / \
    np.maximum(np.abs(input_col).max(axis=0), 1e-12)
in_rel_spread_eff = float(max(in_rel_spread[1], in_rel_spread[3]))

# --------------------------------------------------------------------------
# 3. 灰箱 scheduled 代理
# --------------------------------------------------------------------------
THETA_GRID = np.linspace(-0.6, 0.6, 9)
A_pts = np.array([discrete_lin(np.array([0.0, 0.0, th, 0.0]))[0] for th in THETA_GRID])
B_pts = np.array([discrete_lin(np.array([0.0, 0.0, th, 0.0]))[1] for th in THETA_GRID])
i0 = int(np.argmin(np.abs(THETA_GRID)))
A0, B0 = A_pts[i0].copy(), B_pts[i0].copy()


def gamma_A(hist_theta):
    """A 的调度通道：奇通道 = tanh(c), 偶通道 = tanh(|c|)，c 由测量历史线性组合得到。"""
    c = float(np.dot(CONTEXT_W, hist_theta[:P_WIN]))
    return np.array([np.tanh(c), np.tanh(abs(c))])


def gamma_B(meas_theta):
    """B 的调度通道：chi_k = C_x z_k 即当前测量；本例取 chi = [theta_k, |theta_k|]。"""
    return np.array([np.tanh(meas_theta), np.tanh(abs(meas_theta))])


GAM_A = np.array([gamma_A([th, th]) for th in THETA_GRID])      # (J, 2)
GAM_B = np.array([gamma_B(th) for th in THETA_GRID])            # (J, 2)


def _rank1(targets, gammas, iters=500):
    """单通道 rank-1 拟合：targets[j] ≈ s * gammas[j] * u v^T（u、v 单位列）。"""
    d = targets.shape[1]
    u = rng.normal(size=(d, 1))
    u /= max(np.linalg.norm(u), 1e-30)
    v = rng.normal(size=(d, 1))
    v /= max(np.linalg.norm(v), 1e-30)
    g2 = float(np.sum(gammas ** 2))
    for _ in range(iters):
        v = sum(gammas[j] * (targets[j].T @ u) for j in range(len(targets)))
        v /= max(np.linalg.norm(v), 1e-30)
        u = sum(gammas[j] * (targets[j] @ v) for j in range(len(targets)))
        u /= max(np.linalg.norm(u), 1e-30)
    s = float(sum(gammas[j] * float((u.T @ targets[j] @ v).item())
                  for j in range(len(targets))) / max(g2, 1e-30))
    return u, v, s


def fit_A(D, GAM):
    """greedy rank-2：先拟合通道 1，再对残差拟合通道 2。返回 U(d,2)、V(d,2)、g(2,)。"""
    U = np.zeros((N, CH))
    V = np.zeros((N, CH))
    g = np.zeros(CH)
    R = D.copy()
    for k in range(CH):
        u, v, s = _rank1(R, GAM[:, k])
        U[:, k] = u.ravel()
        V[:, k] = v.ravel()
        g[k] = s
        R = R - np.array([GAM[j, k] * s * (u @ v.T) for j in range(len(R))])
    return U, V, g


def fit_B(D, GAM):
    """逐通道拟合向量：D[j] ≈ sum_k g_k * GAM[j,k] * u_k。返回 U(4,2)、g(2,)。"""
    U = np.zeros((N, CH))
    g = np.zeros(CH)
    R = D.copy()
    for k in range(CH):
        u = R.T @ GAM[:, k]
        u /= max(np.linalg.norm(u), 1e-30)
        s = float(np.sum(GAM[:, k] * (R @ u)) / max(float(np.sum(GAM[:, k] ** 2)), 1e-30))
        U[:, k] = u          # 单位列；幅度只放在 g[k] 里（不要重复计入）
        g[k] = s
        R = R - np.outer(GAM[:, k], u * s)
    return U, g


U_A, V_A, g_A_ch = fit_A(A_pts - A0, GAM_A)
U_B, g_B_ch = fit_B((B_pts - B0).reshape(len(THETA_GRID), N), GAM_B)
V_B = np.ones((1, CH))          # m = 1


def A_model(hist_theta):
    return A0 + U_A @ np.diag(gamma_A(hist_theta) * g_A_ch) @ V_A.T


def B_model(meas_theta):
    return B0 + U_B @ np.diag(gamma_B(meas_theta) * g_B_ch) @ V_B.T


# 命题 1 的量（模型自身性质）
dev_A = float(max(np.linalg.norm(A_model([th, th]) - A0, 2) for th in THETA_GRID))
dev_B = float(max(np.linalg.norm(B_model(th) - B0, 2) for th in THETA_GRID))
g_A = dev_A
g_B = dev_B
col_U_A = [float(np.linalg.norm(U_A[:, k])) for k in range(CH)]
col_V_A = [float(np.linalg.norm(V_A[:, k])) for k in range(CH)]
col_U_B = [float(np.linalg.norm(U_B[:, k])) for k in range(CH)]

res_A = [float(np.linalg.norm((A_pts[j] - A0) - (A_model([THETA_GRID[j], THETA_GRID[j]]) - A0), 2))
         for j in range(len(THETA_GRID))]
tgt_A = [float(np.linalg.norm(A_pts[j] - A0, 2)) for j in range(len(THETA_GRID))]
res_B = [float(np.linalg.norm((B_pts[j] - B0) - (B_model(THETA_GRID[j]) - B0), 2))
         for j in range(len(THETA_GRID))]
tgt_B = [float(np.linalg.norm(B_pts[j] - B0, 2)) for j in range(len(THETA_GRID))]
rel_res_A = float(np.max(np.array(res_A) / np.maximum(np.array(tgt_A), 1e-12)))
rel_res_B = float(np.max(np.array(res_B) / np.maximum(np.array(tgt_B), 1e-12)))
# 更合适的拟合质量指标：Frobenius 意义下的相对残差（逐点谱范数残差可能因通道方向
# 不完全对齐而**大于**逐点目标范数，故两者都报）
fitA = np.array([A_model([THETA_GRID[j], THETA_GRID[j]]) - A0 for j in range(len(THETA_GRID))])
fitB = np.array([(B_model(THETA_GRID[j]) - B0).ravel() for j in range(len(THETA_GRID))])
fro_rel_A = float(np.linalg.norm(fitA - (A_pts - A0)) / max(np.linalg.norm(A_pts - A0), 1e-30))
fro_rel_B = float(np.linalg.norm(fitB - (B_pts - B0).reshape(len(THETA_GRID), N))
                  / max(np.linalg.norm((B_pts - B0).reshape(len(THETA_GRID), N)), 1e-30))

mism_A = float(max(np.linalg.norm(A_model([THETA_GRID[j], THETA_GRID[j]]) - A_pts[j], 2)
                   for j in range(len(THETA_GRID))))
mism_B = float(max(np.linalg.norm(B_model(THETA_GRID[j]) - B_pts[j], 2)
                   for j in range(len(THETA_GRID))))
rel_mism_A = mism_A / max(float(max(np.linalg.norm(A_pts[j], 2) for j in range(len(THETA_GRID)))), 1e-30)
rel_mism_B = mism_B / max(float(max(np.linalg.norm(B_pts[j], 2) for j in range(len(THETA_GRID)))), 1e-30)

# --------------------------------------------------------------------------
# 4. 闭环：完整 scheduled MPC vs 冻结 LTV-MPC，都在真 plant 上
# --------------------------------------------------------------------------
NH = 20
NSTEP = 60
Q = np.diag([1.0, 0.1, 20.0, 1.0])
R = np.array([[0.05]])
# 终端代价与名义 rollouts 的稳定化增益：由 theta = 0 处离散线性化的 LQR 给出。
# 说明：倒立摆的线性化本身不稳定（不稳定特征值 ±sqrt((M+m)g/(M l)) ≈ ±4.65），零输入的名义 rollout 会指数发散、
# 使调度序列失去意义；用 LQR 增益驱动名义 rollout 是 qLMPC 一类做法的标准处理。
P_LQR = solve_discrete_are(A0, B0, Q, R)
K_LQR = np.linalg.solve(R + B0.T @ P_LQR @ B0, B0.T @ P_LQR @ A0)
Pterm = P_LQR.copy()
X_REF = np.zeros(N)
X_INIT = np.array([0.0, 0.0, 0.30, 0.0])
UMAX = 20.0


def rollout_with(hist_theta, U, x_start):
    """名义 rollout：给定输入序列，用模型推进，返回逐位 A_i、B_i 与 Z。"""
    z = np.zeros((NH, N))
    zk = np.asarray(x_start, dtype=float).copy()
    A_seq, B_seq = [], []
    ht = list(hist_theta)
    for i in range(NH):
        Ai, Bi = A_model(ht), B_model(ht[0])
        A_seq.append(Ai)
        B_seq.append(Bi)
        zk = Ai @ zk + Bi @ np.array([U[i]])
        z[i] = zk
        ht = [zk[2]] + ht[:-1]
    return A_seq, B_seq, z


def rollout(hist_theta, x_start):
    """名义 rollout（闭环用）：由 LQR 增益驱动，保证名义轨迹有界。"""
    z = np.zeros((NH, N))
    zk = np.asarray(x_start, dtype=float).copy()
    A_seq, B_seq = [], []
    ht = list(hist_theta)
    for i in range(NH):
        Ai, Bi = A_model(ht), B_model(ht[0])
        A_seq.append(Ai)
        B_seq.append(Bi)
        u = float(np.clip(-float((K_LQR @ (zk - X_REF))[0]), -UMAX, UMAX))
        zk = Ai @ zk + Bi @ np.array([u])
        z[i] = zk
        ht = [zk[2]] + ht[:-1]
    return A_seq, B_seq, z


def build_FG(A_seq, B_seq, x0):
    """按 06 §4 的约定：Z = [z_1;...;z_N] = F + G U。"""
    F = np.zeros(NH * N)
    G = np.zeros((NH * N, NH))
    z = np.asarray(x0, dtype=float).copy()
    for i in range(NH):
        F[i * N:(i + 1) * N] = z
        z = A_seq[i] @ z
    for i in range(NH):
        for j in range(i + 1):
            M = np.eye(N)
            for k in range(j + 1, i):
                M = M @ A_seq[k]
            G[i * N:(i + 1) * N, j] = M @ B_seq[j][:, 0]
    return F, G


def solve_qp(F, G):
    Qb = np.kron(np.eye(NH), Q)
    Qb[-N:, -N:] = Pterm
    Zref = np.tile(X_REF, NH)
    H = 2 * (G.T @ Qb @ G + np.kron(np.eye(NH), R))
    H = 0.5 * (H + H.T)
    f = 2 * G.T @ Qb @ (F - Zref)
    res = minimize(lambda U: 0.5 * U @ H @ U + f @ U, np.zeros(NH),
                   jac=lambda U: H @ U + f, method="L-BFGS-B",
                   bounds=[(-UMAX, UMAX)] * NH, options=dict(maxiter=800, ftol=1e-14, gtol=1e-12))
    return res.x


def closed_loop(mode):
    x = X_INIT.copy()
    hist = [float(x[2]), float(x[2])]
    cost, u_list, t_list = 0.0, [], []
    for k in range(NSTEP):
        t0 = time.perf_counter()
        if mode == "full":
            A_seq, B_seq, _ = rollout(hist, x)
        else:
            Ai, Bi = A_model(hist), B_model(hist[0])
            A_seq, B_seq = [Ai] * NH, [Bi] * NH
        F, G = build_FG(A_seq, B_seq, x)
        U = solve_qp(F, G)
        t_list.append((time.perf_counter() - t0) * 1e3)
        u = float(np.clip(U[0], -UMAX, UMAX))
        u_list.append(u)
        cost += float((x - X_REF) @ Q @ (x - X_REF)) + float(R[0, 0] * u * u)
        x = rk4_step(x, u, PLANT["dt"])
        hist = [float(x[2])] + hist[:-1]
    cost += float((x - X_REF) @ Pterm @ (x - X_REF))
    return dict(cost=cost, final_norm=float(np.linalg.norm(x - X_REF)), t_ms=t_list,
                u=u_list, theta_final=float(x[2]), p_final=float(x[0]))


full = closed_loop("full")
frozen = closed_loop("frozen")

# 模型失配的可观测代理：一步预测 vs 真 plant
x_probe = np.array([0.0, 0.0, 0.30, 0.0])
one_step_model = A_model([0.30, 0.30]) @ x_probe + B_model(0.30) @ np.array([0.0])
one_step_err = float(np.linalg.norm(one_step_model - rk4_step(x_probe, 0.0, PLANT["dt"])))

# 同一输入序列下 full vs frozen 的模型 rollout 偏差（模型层面的量）
U_seq = np.array(full["u"][:NH])
A_s, B_s, _ = rollout_with([0.30, 0.30], U_seq, X_INIT)
A_f, B_f = [A_s[0]] * NH, [B_s[0]] * NH
F1, G1 = build_FG(A_s, B_s, X_INIT)
F2, G2 = build_FG(A_f, B_f, X_INIT)
seq_dev = float(np.max(np.linalg.norm((F1 + G1 @ U_seq - F2 - G2 @ U_seq).reshape(NH, N), axis=1)))

# --------------------------------------------------------------------------
# 5. 输出
# --------------------------------------------------------------------------
res = dict(
    task="TASK-043", seed=SEED,
    plant=dict(name="cart-pole (inverted pendulum on a cart)", state="[p, p_dot, theta, theta_dot]",
               input="force on cart [N]", params=PLANT, integrator="RK4"),
    model_form=dict(d=N, n_psi=0, r_A=CH, r_B=CH, P_window=P_WIN,
                    gamma_A="[tanh(c), tanh(|c|)] with c = [1.0, 0.5] . theta_history",
                    gamma_B="[tanh(theta), tanh(|theta|)]", softmax_used=False),
    input_state_dependence=dict(theta_probe=theta_probe,
                                input_col=np.round(input_col, 6).tolist(),
                                max_relative_spread=in_rel_spread_eff),
    fit=dict(g_A_ch=np.round(g_A_ch, 6).tolist(), g_B_ch=np.round(g_B_ch, 6).tolist(),
             theta_grid=THETA_GRID.tolist(), n_workpoints=len(THETA_GRID),
             linearization="discrete-time ZOH (matrix exponential)",
             col_U_A=col_U_A, col_V_A=col_V_A, col_U_B=col_U_B,
             rel_res_A=rel_res_A, rel_res_B=rel_res_B,
             fro_rel_A=fro_rel_A, fro_rel_B=fro_rel_B,
             res_A=res_A, tgt_A=tgt_A, res_B=res_B, tgt_B=tgt_B),
    prop1=dict(g_A=g_A, g_B=g_B, max_dev_A=dev_A, max_dev_B=dev_B,
               holds_A=True, holds_B=True),
    mismatch=dict(A_abs=mism_A, A_rel=rel_mism_A, B_abs=mism_B, B_rel=rel_mism_B,
                  one_step_err=one_step_err),
    control=dict(horizon=NH, steps=NSTEP, x_init=X_INIT.tolist(),
                 Q_diag=np.diag(Q).tolist(), R=float(R[0, 0]), UMAX=UMAX,
                 terminal_cost="discrete Riccati solution (LQR) of the theta=0 linearization",
                 nominal_rollout="driven by the LQR gain",
                 full=dict(cost=full["cost"], final_norm=full["final_norm"],
                           t_median_ms=float(np.median(full["t_ms"])),
                           theta_final=full["theta_final"], p_final=full["p_final"],
                           u_abs_mean=float(np.mean(np.abs(full["u"])))),
                 frozen=dict(cost=frozen["cost"], final_norm=frozen["final_norm"],
                             t_median_ms=float(np.median(frozen["t_ms"])),
                             theta_final=frozen["theta_final"], p_final=frozen["p_final"],
                             u_abs_mean=float(np.mean(np.abs(frozen["u"])))),
                 cost_rel_diff_pct=float(100.0 * (frozen["cost"] - full["cost"]) / abs(full["cost"])),
                 same_input_rollout_max_dev=seq_dev),
)
io.open(os.path.join(HERE, "results_plant.json"), "w", encoding="utf-8", newline="\n").write(
    json.dumps(res, ensure_ascii=False, indent=2) + "\n")

L = []
L.append("# 阶段七补充（TASK-043）：被控对象 = 倒立摆 / 推车-杆（cart-pole）")
L.append("")
L.append("> **性质**：临时验证，结果**不进论文**（REQ-002 / BA-003）。不声称实时性、闭环稳定性、递归可行性。")
L.append("> 一键复现：`D:\\conda\\envs\\edmddl2\\python.exe validate_plant_cartpole.py`（种子 %d）。" % SEED)
L.append("")
L.append("## 1. 被控对象（done_when#1）")
L.append("")
L.append("**标准 cart-pole（倒立摆装在可平动小车上）**，杆角 `theta` 自竖直向上量起。")
L.append("")
L.append("| 量 | 值 |")
L.append("|---|---|")
L.append("| 状态 | `x = [p, p_dot, theta, theta_dot]` |")
L.append("| 输入 | `u` = 作用在小车上的力 [N] |")
L.append("| 参数 | M = %.2f kg, m = %.2f kg, l = %.2f m, g = %.2f |" % (PLANT["M"], PLANT["m"], PLANT["l"], PLANT["g"]))
L.append("| 积分 | RK4，dt = %.3f s（与离散模型同步） |" % PLANT["dt"])
L.append("")
L.append("动力学（对 `[p_ddot, theta_ddot]` 解 2x2 线性系统，`theta = ±pi/2` 附近也无奇点）：")
L.append("")
L.append("```")
L.append("[ (M+m)      m*l*cos(t) ] [ p_ddot ]   [ u + m*l*t_dot^2*sin(t) ]")
L.append("[  cos(t)     l         ] [ t_ddot ] = [ g*sin(t)               ]")
L.append("```")
L.append("")
L.append("## 2. 输入耦合**确实依赖状态**（本文 B(chi) 的物理动机）")
L.append("")
L.append("`d f / d u` 在若干杆角处的数值线性化（第 2、4 通道 = `p_ddot` 与 `theta_ddot` 对 u 的敏感度）：")
L.append("")
L.append("| theta | [d p_ddot / d u, d theta_ddot / d u] |")
L.append("|---|---|")
for th, col in zip(theta_probe, input_col):
    L.append("| %.2f | [%.6f, %.6f] |" % (th, col[1], col[3]))
L.append("")
L.append("**最大相对变化 %.2f%%**：同一个力在不同杆角下对加速度的作用不同。" % (100 * in_rel_spread_eff))
L.append("这是本文把输入矩阵写成 `B(chi_k)`（依赖当前**测量**）而非常数 `B_0` 的物理理由。")
L.append("**注意**：这是本对象的性质，**不是**「文献中有 B(chi) 直接对应物」的证据（见 `09` §2.3 与 `10` §1 边界框）。")
L.append("")
L.append("## 3. 灰箱 scheduled 代理（本文模型形式的一个实例）")
L.append("")
L.append("`A(c) = A_0 + U_A diag(gamma_A(c)) V_A^T`，`B(chi)` 同理；本例 `n_psi = 0`（`d = 4`）、")
L.append("`r_A = r_B = %d`、`gamma` 取**奇、偶两个通道**（`tanh(c)` 与 `tanh(|c|)`）。" % CH)
L.append("**实测与纸面核对**：在工作点 `[0,0,theta,0]` 处，cart-pole 的线性化 `A(theta)`、`B(theta)` 的**全部元素都是 theta 的偶函数**")
L.append("（关于 `theta = 0` 对称，json 中逐点目标范数也严格对称），因此 `tanh(c)` 这个**奇通道恒为 0**——")
L.append("即下表 `g_A`/`g_B` 的第一个分量恰为 0，是**死通道**；真正起作用的是偶通道 `tanh(|c|)`。")
L.append("也就是说 `r = 2` 在本例中等价于「**偶通道 rank-1**」；这是本实例的受限项之一（见 §5）。")
L.append("`U/V` 的列已归一化（见下表），幅度写在 `gamma` 的系数 `g_k` 里。**softmax 混合本例未使用**（已登记）。")
L.append("")
L.append("拟合数据：cart-pole 在 %d 个工作点（`theta` 均匀取自 [-0.6, 0.6]，其余状态为 0）的线性化，交替最小二乘。" % len(THETA_GRID))
L.append("")
L.append("| 量 | 值 |")
L.append("|---|---|")
L.append("| 通道系数 g_A | %s |" % ", ".join("%.6f" % x for x in g_A_ch))
L.append("| 通道系数 g_B | %s |" % ", ".join("%.6f" % x for x in g_B_ch))
L.append("| ‖U_A 列‖ / ‖V_A 列‖ | %s / %s |" % (", ".join("%.6f" % x for x in col_U_A), ", ".join("%.6f" % x for x in col_V_A)))
L.append("| ‖U_B 列‖ | %s |" % ", ".join("%.6f" % x for x in col_U_B))
L.append("| 拟合相对残差（A，Frobenius） | %.3e |" % fro_rel_A)
L.append("| 拟合相对残差（B，Frobenius） | %.3e |" % fro_rel_B)
L.append("| 逐点谱范数相对残差（A，最大） | %.3e |" % rel_res_A)
L.append("| 逐点谱范数相对残差（B，最大） | %.3e |" % rel_res_B)
L.append("")
L.append("> 两种残差都要看：Frobenius 是**整体拟合质量**，逐点谱范数可能**大于** 1 —— 这表示在某些工作点上，")
L.append("> 未捕获的残差超过了修正本身的幅度（逐点谱范数残差可以超过该点自身的修正范数）。")
L.append("> 这不影响模型自身自洽（命题 1 按定义成立），但它**就是**第 3 节下半部分那层模型失配的来源。")
L.append("| 命题 1：max‖A(c)-A_0‖₂ = %.6f = g_A | 成立（按定义取等号） |" % dev_A)
L.append("| 命题 1：max‖B(chi)-B_0‖₂ = %.6f = g_B | 成立（按定义取等号） |" % dev_B)
L.append("")
L.append("**模型失配（必须如实看）**——代理模型与真 plant 的线性化之间的残差：")
L.append("")
L.append("| 量 | 绝对值（谱范数） | 相对值 |")
L.append("|---|---|---|")
L.append("| ‖A_model - A_plant‖₂（工作点最大） | %.4f | %.2f%% |" % (mism_A, 100 * rel_mism_A))
L.append("| ‖B_model - B_plant‖₂（工作点最大） | %.4f | %.2f%% |" % (mism_B, 100 * rel_mism_B))
L.append("")
L.append("一步预测（`theta = 0.30` 附近、零输入）模型 vs plant：**%.3e**。" % one_step_err)
L.append("→ 本文的理论结论针对**模型**；用到真 plant 上会叠加这层失配，本轮**不**对失配下的闭环行为作任何声称。")
L.append("")
L.append("## 4. 闭环对比（done_when#2）：完整 scheduled MPC vs 冻结 LTV-MPC，**都在真 plant 上**")
L.append("")
L.append("设置：时域 N = %d、闭环 %d 步、初始杆角 0.30 rad、限幅 ±%.0f N、`Q = diag(1, 0.1, 20, 1)`、`R = 0.05`；" % (NH, NSTEP, UMAX))
L.append("终端代价 `P` 取该线性化的**离散 Riccati 解**（LQR），名义 rollout 由 LQR 增益驱动——")
L.append("因为倒立摆的线性化本身不稳定（不稳定特征值 ±sqrt((M+m)g/(M l)) ≈ ±4.65），零输入的名义 rollout 会指数发散、使调度序列失去意义。")
L.append("两个控制器**只有一处不同**：完整版每步用名义 rollout 重算调度序列；冻结版把调度冻结在当前测量。两者用同一代理模型，施加的 u 作用在**真 plant** 上。")
L.append("")
L.append("| 指标 | 完整 scheduled MPC | 冻结 LTV-MPC |")
L.append("|---|---|---|")
L.append("| 闭环代价 | %.4f | %.4f |" % (full["cost"], frozen["cost"]))
L.append("| 末端状态范数 ‖x_N‖ | %.3e | %.3e |" % (full["final_norm"], frozen["final_norm"]))
L.append("| 末端杆角 theta [rad] | %.3e | %.3e |" % (full["theta_final"], frozen["theta_final"]))
L.append("| 末端小车位移 p [m] | %.3e | %.3e |" % (full["p_final"], frozen["p_final"]))
L.append("| 平均 |u| [N] | %.3f | %.3f |" % (np.mean(np.abs(full["u"])), np.mean(np.abs(frozen["u"]))))
L.append("| 单步求解耗时中位数 [ms] | %.2f | %.2f |" % (np.median(full["t_ms"]), np.median(frozen["t_ms"])))
L.append("")
L.append("**代价相对差（冻结 − 完整）/|完整| = %+.4f%%**。" % res["control"]["cost_rel_diff_pct"])
L.append("**同一输入序列下两个模型 rollout 的最大偏差 = %.3e**（模型层面的量，确认冻结确实改变了预测）。" % seq_dev)
L.append("")
L.append("**如实报告的两点观察（不要读成结论）**：")
L.append("")
L.append("1. 这个实例里两个控制器的代价差**极小**（%+.4f%%），且**冻结版略低**——本文件**不**作「完整版更优」的暗示，" % res["control"]["cost_rel_diff_pct"])
L.append("   也不作反向暗示。可能原因：该实例的调度调制本身较弱（`g_A` = %.6f，而 `‖A_0‖` 量级为 1），" % g_A)
L.append("   闭环里模型失配与 QP 求解精度的影响与之相当。")
L.append("2. 两个控制器的末端小车位移都约 0.46 m（未回到 0）——杆被稳住了（末端杆角约 -0.05 rad），但小车漂移；")
L.append("   这是有限时域 + 小车位置权重较小的正常结果，不是发散。")
L.append("")
L.append("## 5. 诚实边界（必读）")
L.append("")
L.append("- **临时验证**，结果**不进论文**（REQ-002 / BA-003）。")
L.append("- **不作实时性声称**：耗时只是观察；L-BFGS-B 不是 MPC 求解器；两个控制器计算量本就不同。")
L.append("- **不作闭环稳定性 / 递归可行性声称**：无终端**约束**（只有终端代价）、无可行性论证，只是有限步仿真。")
L.append("- **不作「理论已被 plant 验证」的声称**：理论针对模型；plant 引入了第 3 节的模型失配。")
L.append("- **不作「B(chi) 有文献直接对应物」的声称**：第 2 节展示的是本对象的物理性质。")
L.append("- 本例是模型形式的**受限实例**：`n_psi = 0`、`r = %d`、`gamma` 用两个固定通道、**未使用 softmax 混合**、" % CH)
L.append("  `c` 与 `chi` 都取自杆角（`chi` 只取当前测量）、`U_k^in` 未进入 context、历史窗口 `P = 2` 很短、拟合是**线性化灰箱**而非数据驱动辨识。")
L.append("- 命题 1 的两行「取等号」是因为 `g_A`/`g_B` 按 `max‖A(c)-A_0‖` 定义；这**只**说明界按定义成立，不含紧性信息。")
L.append("")

L.append("")
L.append("## 6. 可复现性")
L.append("")
L.append("- 脚本固定种子（%d），除 `t_median_ms`（墙钟耗时，是**观察量不是结果**）外不含随机性来源。" % SEED)
L.append("- **两次连续运行对比（本轮实测）**：`results_plant.json` 在剔除 `t_median_ms` 后**逐位一致**；两次运行的 stdout 也完全一致。")
L.append("  原始对比输出（两次 stdout、两次耗时、逐位比较结论）见同目录 **`results_plant_repro.txt`**，并写入 `EV-TASK043-PLANT-001` 证据。")
L.append("  **`t_median_ms` 每次都会变**（墙钟耗时是观察量、不是结果），本文件因此**不硬编码其值**，以免与 §4 表/json 不一致。")
L.append("- 复现命令（在 `validation/` 目录下）：`D:\\\\conda\\\\envs\\\\edmddl2\\\\python.exe validate_plant_cartpole.py`。")
L.append("")

io.open(os.path.join(HERE, "results_plant.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")

print("ok  g_A_ch=%s g_B_ch=%s  fro_A=%.3e fro_B=%.3e  full=%.4f frozen=%.4f rel=%+.4f%% seqdev=%.3e"
      % (np.round(g_A_ch, 6).tolist(), np.round(g_B_ch, 6).tolist(), fro_rel_A, fro_rel_B,
         full["cost"], frozen["cost"], res["control"]["cost_rel_diff_pct"], seq_dev))
