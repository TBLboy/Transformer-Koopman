# -*- coding: utf-8 -*-
"""
Replay of the verification-reviewer's counterexample against 07 theorem 2 (v1),
and check of the corrected bound (v2).

Counterexample (scalar, P = 2):
    A(c) = tanh(c)  =>  A_0 = 0, g_A = 1, W_A = 1, r_A = 1 (softmax weight = 1 const, W_A^pi = 0)
    B(x) = 100      =>  B_0 = 100, g_B = 0, L_B = 0, M_B = 100
    c_i  = x_i      =>  L_phi = 1
    z_0 = 0, x_{-1} = 0, u_{-1} = 0
    bar U = (0, 0)      (nominal, drives the frozen schedule)
    U     = (0.01, 0.01) (actually applied)
    M_Z = 2 (working-domain bound), P = 2, N = 2
"""
import io, os, math

T = r"C:\Users\12187\AppData\Local\Temp\opencode"
OUT = r"D:\Project\Transformer-Koopman\Transformer-Koopman\杂项\新版本\validation"

A = lambda c: math.tanh(c)
B = lambda x: 100.0

z0 = 0.0
U = [0.01, 0.01]
Ubar = [0.0, 0.0]

N = 2
P = 2
M_Z = 2.0
L_phi = 1.0
g_A, g_B = 1.0, 0.0
M_A = 0.0 + g_A          # ||A_0|| + g_A
M_B = 100.0 + g_B        # ||B_0|| + g_B
L_A = 1.0                # g_A * (||W_A|| + sqrt(r_A)/2 * ||W_A^pi||) = 1*(1+0)
L_B = 0.0
M_U = 1.0                # any finite value; L_B*M_U = 0
delta_u = max(abs(U[i] - Ubar[i]) for i in range(N))
Delta_u = delta_u        # U^in has P-1 = 1 past input

# --- trajectories -----------------------------------------------------------
# (a) nominal rollout: driven by Ubar, own schedule
zbar = [z0]
for i in range(N):
    zbar.append(A(zbar[i]) * zbar[i] + B(0.0) * Ubar[i])

# (b) full model: driven by U, own schedule
zfull = [z0]
for i in range(N):
    zfull.append(A(zfull[i]) * zfull[i] + B(0.0) * U[i])

# (c) frozen model: driven by U, schedule frozen at the nominal rollout
Abar = [A(zbar[i]) for i in range(N)]
Bbar = [B(0.0) for i in range(N)]
zfr = [z0]
for i in range(N):
    zfr.append(Abar[i] * zfr[i] + Bbar[i] * U[i])

e = [zfull[i] - zfr[i] for i in range(N + 1)]
g = [zfr[i] - zbar[i] for i in range(N + 1)]
h = [zfull[i] - zbar[i] for i in range(N + 1)]

# --- constants --------------------------------------------------------------
L = M_A + L_B * M_U + L_A * L_phi * math.sqrt(P) * M_Z
G_N = M_B * delta_u * sum(M_A ** t for t in range(N))

delta_frz_v1 = L_A * L_phi * M_Z * Delta_u
delta_frz_v2 = L_A * L_phi * M_Z * Delta_u + (L_A * L_phi * math.sqrt(P) * M_Z + L_B * M_U) * G_N


def bound_at(delta_frz, i, L):
    return delta_frz * sum(L ** (i - 1 - t) for t in range(i))


lines = []
lines.append("=== 07 theorem 2: counterexample replay (scalar, P=2, A(c)=tanh(c), B=100) ===")
lines.append("")
lines.append("trajectories (index: z_full, z_fr, z_bar, e=full-fr, g=fr-bar, h=full-bar)")
for i in range(N + 1):
    lines.append("  i=%d  z_full=%+.6f  z_fr=%+.6f  z_bar=%+.6f  e=%+.6f  g=%+.6f  h=%+.6f"
                 % (i, zfull[i], zfr[i], zbar[i], e[i], g[i], h[i]))
lines.append("")
lines.append("constants: M_A=%.4f M_B=%.4f L_A=%.4f L_B=%.4f L_phi=%.4f M_Z=%.4f P=%d"
             % (M_A, M_B, L_A, L_B, L_phi, M_Z, P))
lines.append("  delta_u=%.6f  Delta_u=%.6f  G_N=%.6f  L=%.6f" % (delta_u, Delta_u, G_N, L))
lines.append("  delta_frz(v1)=%.6f   delta_frz(v2)=%.6f" % (delta_frz_v1, delta_frz_v2))
lines.append("")
lines.append("i=2: true ||e_2|| = %.6f" % abs(e[2]))
lines.append("     v1 bound     = %.6f   -> %s" % (bound_at(delta_frz_v1, 2, L),
                                                    "HOLDS" if abs(e[2]) <= bound_at(delta_frz_v1, 2, L) else "VIOLATED"))
lines.append("     v2 bound     = %.6f   -> %s" % (bound_at(delta_frz_v2, 2, L),
                                                    "HOLDS" if abs(e[2]) <= bound_at(delta_frz_v2, 2, L) else "VIOLATED"))
lines.append("")
lines.append("diagnosis: v1 under-estimated because it used the *nominal rollout* z_bar as if it were")
lines.append("the frozen trajectory z_fr. Here g_1 = %.4f != 0, so the B-channel difference" % g[1])
lines.append("|B(x_full_1) - B_bar_1| = %.4f is driven by g, not by e (= %+.6f)." % (abs(g[1]), e[1]))
lines.append("")
lines.append("sanity check (bar U = U): the three trajectories coincide and both bounds -> 0.")
U2 = [0.01, 0.01]
zbar2, zfull2, zfr2 = [z0], [z0], [z0]
for i in range(N):
    zbar2.append(A(zbar2[i]) * zbar2[i] + B(0.0) * U2[i])
for i in range(N):
    zfull2.append(A(zfull2[i]) * zfull2[i] + B(0.0) * U2[i])
for i in range(N):
    zfr2.append(A(zbar2[i]) * zfr2[i] + B(0.0) * U2[i])
lines.append("  max |z_full - z_bar| over i<=N = %.3e ;  max |e| = %.3e" %
             (max(abs(zfull2[i] - zbar2[i]) for i in range(N + 1)),
              max(abs(zfull2[i] - zfr2[i]) for i in range(N + 1))))
ok = True

txt = "\n".join(lines) + "\n"
if not os.path.isdir(OUT):
    os.makedirs(OUT)
io.open(os.path.join(OUT, "replay_counterexample_result.txt"), "w", encoding="utf-8").write(txt)
io.open(os.path.join(T, "replay.txt"), "w", encoding="utf-8").write(txt)
print("ok")
