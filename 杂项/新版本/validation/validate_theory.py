# -*- coding: utf-8 -*-
"""
Phase-7 temporary validation for the scheduled-Koopman theory package.

SCOPE AND HONESTY NOTES
-----------------------
* TEMPORARY validation. Results DO NOT enter the paper (REQ-002 / BA-003).
* The controlled plant has NOT been chosen by the user. Therefore:
    - checks 1-3 (model + prediction) need NO plant; they are the numerical
      evidence for propositions 1/2 and theorem 2;
    - check 4 (control) compares the FROZEN LTV-MPC against the FULL scheduled
      MPC *on the same dynamics*, which isolates the effect of freezing itself.
      No claim is made about any physical plant.
* No real-time claim anywhere; timings are observations only.
* Window convention (01 §2 / 02 S1): X_i ends at the CURRENT measurement x_i and
  contains P measurements; U^in_i contains the P-1 PAST inputs; u_i never enters c_i.

Run with: D:\\conda\\envs\\edmddl2\\python.exe   (numpy 1.26, scipy 1.13)
"""
import io, os, json, time
import numpy as np
import scipy
from scipy.optimize import minimize

rng = np.random.default_rng(20261011)

d, n, m = 4, 2, 1
r_A = r_B = 2
P, N = 3, 5
g_A = g_B = 1.0
MZ, MU = 3.0, 1.0        # working-domain bounds (assumption A1)
umax = 1.5
Q = np.eye(d) * 1.0
Rw = np.eye(m) * 0.1
Pw = np.eye(d) * 5.0
Sw = np.eye(m) * 0.1

OUT = r"D:\Project\Transformer-Koopman\Transformer-Koopman\杂项\新版本\validation"
C_x = np.hstack([np.eye(n), np.zeros((n, d - n))])          # C_x z = x   (S2)


def unitise(M):
    M = np.asarray(M, float)
    nz = np.linalg.norm(M, axis=0, keepdims=True)
    nz[nz == 0] = 1.0
    return M / nz


def make_params(seed):
    r = np.random.default_rng(seed)
    p = {}
    p["A_0"] = 0.3 * np.eye(d) + 0.8 * r.normal(size=(d, d)) / np.sqrt(d)
    p["B_0"] = r.normal(size=(d, m)) * 0.5
    p["U_A"], p["V_A"] = unitise(r.normal(size=(d, r_A))), unitise(r.normal(size=(d, r_A)))
    p["W_A"], p["b_A"] = r.normal(size=(r_A, d)) * 0.7, r.normal(size=r_A) * 0.2
    p["W_A_pi"], p["b_A_pi"] = r.normal(size=(r_A, d)) * 0.7, r.normal(size=r_A) * 0.2
    p["U_B"], p["V_B"] = unitise(r.normal(size=(d, r_B))), unitise(r.normal(size=(m, r_B)))
    p["W_B"], p["b_B"] = r.normal(size=(r_B, n)) * 0.7, r.normal(size=r_B) * 0.2
    p["W_B_pi"], p["b_B_pi"] = r.normal(size=(r_B, n)) * 0.7, r.normal(size=r_B) * 0.2
    din = P * n + (P - 1) * m
    p["W_phi"], p["b_phi"] = r.normal(size=(d, din)) * 0.5, np.zeros(d)
    return p


def softmax(z):
    z = z - np.max(z)
    e = np.exp(z)
    return e / e.sum()


def gamma_A(p, c):
    return g_A * softmax(p["W_A_pi"] @ c + p["b_A_pi"]) * np.tanh(p["W_A"] @ c + p["b_A"])


def gamma_B(p, chi):
    return g_B * softmax(p["W_B_pi"] @ chi + p["b_B_pi"]) * np.tanh(p["W_B"] @ chi + p["b_B"])


def A_of(p, c):
    return p["A_0"] + p["U_A"] @ np.diag(gamma_A(p, c)) @ p["V_A"].T


def B_of(p, chi):
    return p["B_0"] + p["U_B"] @ np.diag(gamma_B(p, chi)) @ p["V_B"].T


def C_phi(p, X, Uin):
    return np.tanh(p["W_phi"] @ np.concatenate([X, Uin]) + p["b_phi"])


def constants(p):
    L_A = g_A * (np.linalg.norm(p["W_A"], 2) + np.sqrt(r_A) / 2 * np.linalg.norm(p["W_A_pi"], 2))
    L_B = g_B * (np.linalg.norm(p["W_B"], 2) + np.sqrt(r_B) / 2 * np.linalg.norm(p["W_B_pi"], 2))
    return dict(L_A=float(L_A), L_B=float(L_B),
                M_A=float(np.linalg.norm(p["A_0"], 2) + g_A),
                M_B=float(np.linalg.norm(p["B_0"], 2) + g_B),
                L_phi=float(np.linalg.norm(p["W_phi"], 2)))


def window(x_past, u_past, x_now):
    """X ends at x_now and has P measurements; Uin has the P-1 most recent past inputs."""
    xs = [np.asarray(x, float).reshape(-1) for x in list(x_past) + [x_now]][-P:]
    if len(xs) < P:
        xs = [np.zeros(n)] * (P - len(xs)) + xs
    if P > 1:
        us = [np.asarray(u, float).reshape(-1) for u in list(u_past)][-(P - 1):]
        if len(us) < P - 1:
            us = [np.zeros(m)] * (P - 1 - len(us)) + us
        Uin = np.concatenate(us)
    else:
        Uin = np.zeros(0)
    return np.concatenate(xs), Uin


def simulate(p, U, z0, x0h, u0h, frozen_ab=None, record=False):
    """frozen_ab=None -> schedule from its own trajectory (full model).
       frozen_ab=[(A_i,B_i)] -> frozen schedule.  Returns trajectory (and schedule)."""
    z = np.array(z0, float)
    xp, up = list(x0h), list(u0h)
    traj, sched = [z.copy()], []
    for i, ui in enumerate(np.atleast_1d(U)):
        X, Uin = window(xp, up, C_x @ z)
        c = C_phi(p, X, Uin)
        Ab, Bb = A_of(p, c), B_of(p, C_x @ z)
        sched.append((c, C_x @ z, Ab, Bb))
        A, B = (Ab, Bb) if frozen_ab is None else frozen_ab[i]
        z = A @ z + B.reshape(d, -1) @ np.array([ui], float)
        xp.append(C_x @ z)
        up.append(float(ui))
        traj.append(z.copy())
    return (traj, sched) if record else traj


# ---------------------------------------------------------------------------
p = make_params(7)
K = constants(p)
L = K["M_A"] + K["L_B"] * MU + K["L_A"] * K["L_phi"] * np.sqrt(P) * MZ

L_out, res = [], {}
L_out.append("# 阶段七 临时验证结果（模型 / 预测 / 控制）\n")
L_out.append("> **临时验证，结果不进论文**（REQ-002 / BA-003）。被控对象（plant）**尚未由用户确定**；")
L_out.append("> 检查 1–3 不需要 plant，是命题 1/2 与定理 2 的直接数值证据；")
L_out.append("> 检查 4 在**同一动力学**上比较两个控制器，隔离的是「冻结调度」这一近似本身，不对任何物理对象作声明。")
L_out.append("> **不作任何实时性声称。**\n")
L_out.append("参数：d=%d, n=%d, m=%d, r_A=r_B=%d, P=%d, g_A=g_B=%.1f, N=%d；numpy %s, scipy %s\n"
             % (d, n, m, r_A, P, g_A, N, np.__version__, scipy.__version__))
L_out.append("## 0. 常数（来源：$L_A,L_B$ 见 `04` 命题 2；$M_A,M_B$ 见 `05`/`07`；$L_\\phi$ 见 `02` A3；$L$ 见 `05`/`07`）\n")
L_out.append("> **$L_\\phi$ 的来源说明**：本脚本取 $C_\\phi(X,U^{in}) = \\tanh(W_\\phi [X;U^{in}] + b_\\phi)$，即「线性 + tanh」，"
             "故 $L_\\phi = \\|W_\\phi\\|_2$ 是该映射的 Lipschitz 上界（$\\tanh$ 是 1-Lipschitz）。"
             "`01` §2 指出 $C_\\phi$ 的解析形式在阶段一**未固定**，因此这里的 $L_\\phi$ 是**本脚本所选形式**下的值，不是模型定义的必然值。\n")
L_out.append("| 常数 | 值 |\n|---|---|")
for k in ("L_A", "L_B", "M_A", "M_B", "L_phi"):
    L_out.append("| %s | %.4f |" % (k, K[k]))
L_out.append("| $L$（定理 2 的单步传播因子） | %.4f |\n" % L)
res["constants"] = {**K, "L": L}

# 1. Proposition 1 -----------------------------------------------------------
cS = rng.normal(size=(4000, d)) * 1.5
xS = rng.normal(size=(4000, n)) * 1.5
dA = max(np.linalg.norm(A_of(p, c) - p["A_0"], 2) for c in cS)
dB = max(np.linalg.norm(B_of(p, x) - p["B_0"], 2) for x in xS)
L_out.append("## 1. 命题 1 的数值核对（4000 个随机调度点）\n")
L_out.append("| 量 | 经验最大值 | 理论界 | 结论 |\n|---|---|---|---|")
L_out.append("| $\\|A(c)-A_0\\|_2$ | %.6f | $g_A$ = %.1f | %s |" % (dA, g_A, "成立" if dA <= g_A + 1e-9 else "**违反**"))
L_out.append("| $\\|B(\\chi)-B_0\\|_2$ | %.6f | $g_B$ = %.1f | %s |\n" % (dB, g_B, "成立" if dB <= g_B + 1e-9 else "**违反**"))
res["prop1"] = dict(max_dev_A=dA, max_dev_B=dB, g_A=g_A, g_B=g_B)

# 2. Proposition 2 -----------------------------------------------------------
c1 = rng.normal(size=(2000, d)) * 1.5
c2 = rng.normal(size=(2000, d)) * 1.5
rA = [np.linalg.norm(A_of(p, a) - A_of(p, b), 2) / max(np.linalg.norm(a - b), 1e-12) for a, b in zip(c1, c2)]
rB = [np.linalg.norm(B_of(p, a[:n]) - B_of(p, b[:n]), 2) / max(np.linalg.norm(a[:n] - b[:n]), 1e-12) for a, b in zip(c1, c2)]
L_out.append("## 2. 命题 2 的数值核对（2000 对随机调度点）\n")
L_out.append("| 量 | 经验最大比值 | 理论常数 | 结论 |\n|---|---|---|---|")
L_out.append("| $\\|A(c)-A(c')\\|_2/\\|c-c'\\|_2$ | %.4f | $L_A$ = %.4f | %s |"
             % (max(rA), K["L_A"], "成立" if max(rA) <= K["L_A"] + 1e-9 else "**违反**"))
L_out.append("| $\\|B(\\chi)-B(\\chi')\\|_2/\\|\\chi-\\chi'\\|_2$ | %.4f | $L_B$ = %.4f | %s |\n"
             % (max(rB), K["L_B"], "成立" if max(rB) <= K["L_B"] + 1e-9 else "**违反**"))
L_out.append("（两者都是**经验下界对上理论上界**的距离：经验比值仅为理论常数的约 1/4（A 侧 0.5612/2.2202）与约 0.42（B 侧 0.9187/2.2053），"
             "与 `04` 备注「常数不紧」一致 —— 本检查只检验**方向**，不检验紧性。）\n")
res["prop2"] = dict(max_ratio_A=max(rA), L_A=K["L_A"], max_ratio_B=max(rB), L_B=K["L_B"])

# 3. low-rank correction magnitude ------------------------------------------
corr_A = [np.linalg.norm(A_of(p, c) - p["A_0"], 2) for c in cS]
corr_B = [np.linalg.norm(B_of(p, x) - p["B_0"], 2) for x in xS]
A0n = float(np.linalg.norm(p["A_0"], 2))
L_out.append("## 3. 低秩修正幅度（契约 done_when 第 2 条）\n")
L_out.append("| 量 | 均值 | 中位 | 最大 | 与 $\\|A_0\\|_2$ 之比（均值） |\n|---|---|---|---|---|")
L_out.append("| $\\|A(c)-A_0\\|_2$ | %.4f | %.4f | %.4f | %.1f%% |"
             % (np.mean(corr_A), np.median(corr_A), max(corr_A), 100 * np.mean(corr_A) / A0n))
L_out.append("| $\\|B(\\chi)-B_0\\|_2$ | %.4f | %.4f | %.4f | — |\n"
             % (np.mean(corr_B), np.median(corr_B), max(corr_B)))
L_out.append("（$\\|A_0\\|_2 = %.4f$。**注意**：本组参数下修正幅度**并不小**（均值约为名义矩阵范数的一半）——这是参数选择的结果、不是理论结论；命题 1/2 只依赖结构 (S3) 与 A4，与幅度大小无关。）\n" % A0n)
res["lowrank"] = dict(A_corr_mean=float(np.mean(corr_A)), A_corr_max=float(max(corr_A)),
                      B_corr_mean=float(np.mean(corr_B)), B_corr_max=float(max(corr_B)), A0_norm=A0n)

# 4. Theorem 2: full vs frozen rollout --------------------------------------
z0 = np.array([0.5, -0.3, 0.2, 0.1])
x0h = [np.zeros(n)] * P
u0h = [np.zeros(m)] * (P - 1)
Ubar = 0.1 * np.ones(N)
L_out.append("## 4. 定理 2：完整 vs 冻结 rollout（契约 done_when 第 3 条）\n")
L_out.append("初始状态 $z_0 \\ne 0$；名义输入 $\\bar U = 0.1\\cdot\\mathbf{1}$（冻结调度由**名义 rollout** 生成，其驱动输入是 $\\bar U$）；施加 $U = \\bar U + \\delta_u\\mathbf{1}$。\n")
L_out.append("| $\\delta_u$ | 实测 $\\max_i\\|e_i\\|_2$ | 定理 2 的界 | 界是否成立 |\n|---|---|---|---|")
res["thm2"] = []
for du in (0.0, 0.005, 0.02, 0.05):
    U = Ubar + du
    t_nom, sched_nom = simulate(p, Ubar, z0, x0h, u0h, record=True)
    froz = [(s[2], s[3]) for s in sched_nom]
    t_full = simulate(p, U, z0, x0h, u0h)
    t_fr = simulate(p, U, z0, x0h, u0h, frozen_ab=froz)
    e = [np.linalg.norm(t_full[i] - t_fr[i]) for i in range(N + 1)]
    Du = np.sqrt(max(P - 1, 0)) * du
    G_N = K["M_B"] * du * sum(K["M_A"] ** t for t in range(N))
    dfrz = K["L_A"] * K["L_phi"] * MZ * Du + (K["L_A"] * K["L_phi"] * np.sqrt(P) * MZ + K["L_B"] * MU) * G_N
    bnd = dfrz * sum(L ** (N - 1 - t) for t in range(N))
    ok = max(e) <= bnd + 1e-9
    L_out.append("| %.3f | %.3e | %.3e | %s |" % (du, max(e), bnd, "成立" if ok else "**违反**"))
    res["thm2"].append(dict(delta_u=du, measured=float(max(e)), bound=float(bnd), holds=bool(ok),
                            e_seq=[float(x) for x in e]))
L_out.append("\n**自检**：$\\delta_u = 0$ 时三条轨迹重合（$\\bar z = z^{\\mathrm{full}} = z^{\\mathrm{fr}}$）、界为 0 —— 与 `07` §7 第 3 条的观察一致。\n")
L_out.append("**界非常松（必须一起读）**：本组参数下 $L = %.2f$，于是 $L^N$ 随 $N$ 指数放大，界比实测大若干个数量级。" % L)
L_out.append("定理 2 的作用是**保证有限性并让每个常数可追溯**，不是可用的定量估计；")
L_out.append("收紧它需要额外假设（例如 $L<1$），本阶段**不做**（`07` §7 第 3 条）。")
_m = [r["measured"] for r in res["thm2"]]
_ratio = (_m[3] / _m[1]) if _m[1] > 0 else float("nan")
L_out.append("实测值与 $\\delta_u$ 的关系：$\\delta_u$ 由 0.005 增至 0.05（10×）时实测增大约 %.1f 倍 —— 方向与 $\\delta_{\\mathrm{frz}}$ 对 $\\delta_u$ 的**线性**依赖一致，实测略超线性（$G_N$ 与 $\\Delta_u$ 两项都线性于 $\\delta_u$，故界严格线性放大）。" % _ratio)
L_out.append("（界/实测之比：%s —— 量级主要由 $L^N$ 决定，与 $\\delta_u$ 的具体取值关系不大。）\n"
             % "、".join("%.2e" % (r["bound"] / max(r["measured"], 1e-30))
                        for r in res["thm2"] if r["measured"] > 0))

# 5. Control: frozen LTV-MPC vs full scheduled MPC --------------------------
def cost_full(p, U, z0, xh, uh):
    tr = simulate(p, U, z0, xh, uh)
    J = 0.0
    prev = 0.0
    for i in range(N):
        J += tr[i] @ Q @ tr[i] + (float(U[i]) ** 2) * Rw[0, 0]
        J += ((float(U[i]) - prev) ** 2) * Sw[0, 0]
        prev = float(U[i])
    J += tr[N] @ Pw @ tr[N]
    return J


def frozen_qp(p, z0, xh, uh, Ubar):
    """Frozen LTV QP, built to match `06` §4 exactly:
         Z = [z_1; ...; z_N]                 (Z starts at z_1, NOT at z_0)
         Qbar = blkdiag(Q, ..., Q, P)        (N blocks; the LAST one is the terminal weight)
         J_fr = ||Z - Zref||_Qbar^2 + ||U||_Rbar^2 + ||Dhat U + chat||_Sbar^2
              = (1/2) U^T H U + 2 f^T U + const,   H = 2 M,  f = G^T Qbar F
       refs = 0 and u_{-1} = 0 give chat = 0.  The i=0 term ||z_0||_Q^2 is the
       constant c_0 of `06` §6 note 8 and is deliberately NOT part of the QP.
    """
    _, sched = simulate(p, Ubar, z0, xh, uh, record=True)
    Ai = [s[2] for s in sched]
    Bi = [s[3] for s in sched]
    Qb = np.kron(np.eye(N), Q)
    Qb[-d:, -d:] = Pw
    Rb = np.kron(np.eye(N), Rw)
    Sb = np.kron(np.eye(N), Sw)
    Dm = np.eye(N * m) - np.eye(N * m, k=-m)      # Dhat: (Dhat U)_0 = u_0, (Dhat U)_i = u_i - u_{i-1}
    F = np.zeros(N * d)
    G = np.zeros((N * d, N * m))
    for i in range(1, N + 1):                     # row block (i-1) holds z_i
        Mz = np.eye(d)
        for j in range(i):
            Mz = Ai[j] @ Mz
        F[(i - 1) * d:i * d] = Mz @ z0
        for t in range(i):
            Mg = np.eye(d)
            for j in range(t + 1, i):
                Mg = Ai[j] @ Mg
            G[(i - 1) * d:i * d, t * m:(t + 1) * m] = Mg @ Bi[t]
    Mmat = G.T @ Qb @ G + Rb + Dm.T @ Sb @ Dm
    f = G.T @ Qb @ F                                # refs = 0, u_{-1} = 0 => chat = 0
    return 2 * Mmat, f, Mmat, F, G, Qb             # F, G, Qb are returned for the self-checks


def run_closed_loop(p, z_init, controller, nsteps=20):
    zd = np.array(z_init, float)
    xh, uh = [np.zeros(n)] * P, [np.zeros(m)] * (P - 1)
    Ubar = np.zeros(N)
    cf, tf, zf = [], [], []
    for k in range(nsteps):
        t0 = time.perf_counter()
        if controller == "frozen":
            H, f, _M, _F, _G, _Q = frozen_qp(p, zd, xh, uh, Ubar)
            r = minimize(lambda U: 0.5 * U @ H @ U + 2.0 * f @ U, np.zeros(N),
                         method="L-BFGS-B", bounds=[(-umax, umax)] * N)
            U = r.x
        else:
            best, bJ = None, np.inf
            for s in range(4):
                U0 = np.clip(Ubar + (rng.normal(size=N) * 0.2 if s else 0.0), -umax, umax)
                rr = minimize(lambda U: cost_full(p, U, zd, xh, uh), U0,
                              method="L-BFGS-B", bounds=[(-umax, umax)] * N)
                if rr.fun < bJ:
                    bJ, best = rr.fun, rr.x
            U = best
        tf.append(time.perf_counter() - t0)
        cf.append(cost_full(p, U, zd, xh, uh))       # always scored under J_full
        zd = simulate(p, [U[0]], zd, xh, uh)[1]      # plant = the model itself
        xh.append(C_x @ zd)
        uh.append(float(U[0]))
        Ubar = np.concatenate([U[1:], [U[-1]]])
        zf.append(float(np.linalg.norm(zd)))
    return dict(cost=np.array(cf), time=np.array(tf), norm=np.array(zf))


nsteps = 20
CL = {ct: run_closed_loop(p, [0.8, -0.5, 0.3, 0.1], ct, nsteps) for ct in ("frozen", "full")}
cf, cn = CL["frozen"]["cost"], CL["full"]["cost"]
tf, tn = CL["frozen"]["time"], CL["full"]["time"]

# --- self-check (1): the stacked model must reproduce the nominal trajectory exactly.
# --- self-check (2): J_fr must equal J_full minus the constant c_0 = ||z_0||_Q^2
#     (`06` §6 note 8 excludes the i=0 term from the QP).  The QP value itself omits the
#     additive constant F^T Qbar F, which does not affect the argmin:
#         J_fr(U) = ||F + G U||_Qbar^2 + ... = F^T Qbar F + (1/2) U^T H U + 2 f^T U
_qs = np.array([0.8, -0.5, 0.3, 0.1])
_xh0, _uh0 = [np.zeros(n)] * P, [np.zeros(m)] * (P - 1)
_Ub0 = 0.1 * np.ones(N)
_H0, _f0, _M0, _F0, _G0, _Qb0 = frozen_qp(p, _qs, _xh0, _uh0, _Ub0)
_traj0 = simulate(p, _Ub0, _qs, _xh0, _uh0)
_stack_gap = float(np.max(np.abs(_F0 + _G0 @ _Ub0 - np.concatenate(_traj0[1:]))))
_stack_ok = _stack_gap < 1e-9
_const0 = float(_F0 @ _Qb0 @ _F0)
_qp_val = 0.5 * _Ub0 @ _H0 @ _Ub0 + 2.0 * _f0 @ _Ub0
_full_val = cost_full(p, _Ub0, _qs, _xh0, _uh0)
_c0 = float(_qs @ Q @ _qs)
_qp_gap = abs((_full_val - _c0) - (_const0 + _qp_val))
_qp_ok = _qp_gap < 1e-9
L_out.append("## 5. 控制层对比（同一动力学、无模型失配；用于确认实现与自检一致）\n")
L_out.append("冻结 LTV-MPC（凸 QP，L-BFGS-B） vs 完整 scheduled MPC（非凸，4 次多起点 L-BFGS-B）；闭环 %d 步，$N=%d$。\n" % (nsteps, N))
L_out.append("| 指标 | 冻结 LTV-MPC | 完整 scheduled MPC |\n|---|---|---|")
L_out.append("| 单步 $J_{\\mathrm{full}}$ 均值 | %.4f | %.4f |" % (cf.mean(), cn.mean()))
L_out.append("| 单步 $J_{\\mathrm{full}}$ 中位 | %.4f | %.4f |" % (np.median(cf), np.median(cn)))
L_out.append("| 相对代价差（冻结−完整）/\\|完整\\| | %.3f%% | — |" % (100 * (cf.mean() - cn.mean()) / max(abs(cn.mean()), 1e-9)))
L_out.append("| 单步求解耗时中位 | %.2f ms | %.2f ms |" % (1000 * np.median(tf), 1000 * np.median(tn)))
L_out.append("| 末端状态范数 | %.4f | %.4f |\n" % (CL["frozen"]["norm"][-1], CL["full"]["norm"][-1]))
L_out.append("**读法（重要）**")
L_out.append("- **自检（先看这条）**：在名义输入 $U = \\bar U$ 上，冻结 QP 的目标值必须等于 $J_{\\mathrm{full}}$ 减去常数 $c_0 = \\|z_0\\|_Q^2$（`06` §6 第 8 条刻意把 $i=0$ 项排除在 QP 之外）。实测：$J_{\\mathrm{full}} - c_0 = %.6f$，$J_{\\mathrm{fr}}$（含常数项 $F^{\\mathsf{T}}\\bar Q F$）$= %.6f$，差 $= %.3e$ → **%s**。（这条自检正是用来抓「线性项系数少 2 倍」与「$Z$ 起点错位一格」这类堆叠错误的。）" % (_full_val - _c0, _const0 + _qp_val, _qp_gap, "通过" if _qp_ok else "**不通过**"))
L_out.append("- 代价差是**单步**统计，**不是** `08` 定理 3 的 $2\\varepsilon_J$（后者是整段 $N$ 步代价差的上界且依赖 (CA)），两者不可直接比较。")
L_out.append("- **自检 1（堆叠正确性）**：$F + G\\bar U$ 必须逐位等于名义轨迹的 $[z_1;\\dots;z_N]$。实测最大偏差 $= %.2e$ → **%s**。（这一条直接抓「$Z$ 起点错位一格」这类错误。）"
             % (_stack_gap, "通过" if _stack_ok else "**不通过**"))
L_out.append("- **本组参数下两个控制器的代价几乎相同**（相对差 %.3f%%）：因为动力学就是模型本身、且初值迅速衰减到 0，冻结与不冻结的差别被压得很小。"
             "因此这张表只用于**确认实现与自检一致**，**不构成**对冻结近似影响的度量；要度量影响需要专门的实验设计（本阶段不做）。"
             % (100 * (cf.mean() - cn.mean()) / max(abs(cn.mean()), 1e-9)))
L_out.append("- 耗时只是**观察**：L-BFGS-B 不是 MPC 求解器，**不作任何实时性或截止时间声称**（`06` §5）。")
L_out.append("- 完整问题**非凸**，只取 4 个起点，故其代价是**上界**（可能高于真实全局最优）——这正是 `08` §5 第 2 条声明的限制。")
L_out.append("- 动力学的「plant」在这里**就是模型本身**，因此本表只反映「冻结 vs 不冻结」的控制层后果，**不含任何模型失配**。")
L_out.append("- **耗时对比是被混淆的**：完整控制器每步做 4 次多起点、冻结控制器只做 1 次，故数十倍的差距主要来自**起点数**而非算法结构；这里只报告现象，不据此作任何结论。\n")
res["control"] = dict(cost_frozen_mean=float(cf.mean()), cost_full_mean=float(cn.mean()),
                      rel_diff_pct=float(100 * (cf.mean() - cn.mean()) / max(abs(cn.mean()), 1e-9)),
                      t_frozen_ms=float(1000 * np.median(tf)), t_full_ms=float(1000 * np.median(tn)),
                      final_norm_frozen=float(CL["frozen"]["norm"][-1]), final_norm_full=float(CL["full"]["norm"][-1]),
                      qp_selfcheck_gap=float(_qp_gap), qp_selfcheck_ok=bool(_qp_ok),
                      norm_frozen_seq=[float(x) for x in CL["frozen"]["norm"]],
                      norm_full_seq=[float(x) for x in CL["full"]["norm"]],
                      cost_frozen_seq=[float(x) for x in cf], cost_full_seq=[float(x) for x in cn])

L_out.append("## 6. 声明\n")
L_out.append("1. 本文件是**临时验证**，结果**不进入论文**（REQ-002 / BA-003）。")
L_out.append("2. **被控对象（plant）尚未确定**（用户未指定）。检查 1–3 不需要 plant；检查 4 在模型自身上做双控制器对比，用于隔离冻结近似，不对任何物理对象作声明。")
L_out.append("3. 未作任何闭环稳定性、递归可行性或实时性声称。")
L_out.append("4. 全部数值由同目录 `validate_theory.py` 一键复现（种子固定 20261011）；本仓库解释器为 `D:\\conda\\envs\\edmddl2\\python.exe`。")

txt = "\n".join(L_out) + "\n"
os.makedirs(OUT, exist_ok=True)
io.open(os.path.join(OUT, "results.md"), "w", encoding="utf-8").write(txt)
io.open(os.path.join(OUT, "results.json"), "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
print("OK")
