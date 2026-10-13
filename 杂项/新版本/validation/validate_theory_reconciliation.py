"""TASK-048 synthetic algebra + current-control integration, no training.

Checks the DEC-093 measurement objective, 05/07 recurrences, and 08 cost
bound on bounded synthetic cases. This does not certify real-device domains
or residual constants and does not prove solver outputs are exact argmins.
"""
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np

NEW = Path(__file__).resolve().parent.parent
ROOT = NEW.parents[2]
PATH = NEW / 'Temporary_Experiments' / 'controllers' / 'ltv_mpc.py'
spec = importlib.util.spec_from_file_location('task048_ltv', PATH)
ltv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ltv)
rng = np.random.default_rng(48)
results = []


def check(name, value, limit):
    passed = bool(value <= limit)
    results.append({'name': name, 'value': float(value), 'limit': float(limit), 'passed': passed})
    assert passed, (name, value, limit)


def blockdiag(blocks):
    sizes = [b.shape[0] for b in blocks]
    out = np.zeros((sum(sizes), sum(sizes)))
    idx = 0
    for b, size in zip(blocks, sizes):
        out[idx:idx+size, idx:idx+size] = b
        idx += size
    return out


def psd(n):
    a = rng.normal(size=(n, n))
    return a.T @ a


for n, m, d in [(2, 2, 10), (6, 3, 14)]:
    for N in [1, 3, 6]:
        A = rng.normal(scale=.1, size=(N, d, d)) + np.eye(d)*.7
        B = rng.normal(scale=.2, size=(N, d, m))
        z0 = rng.normal(size=d)
        U = rng.normal(size=(N, m))
        xref = rng.normal(size=(N+1, n))
        uref = rng.normal(size=(N, m))
        uprev = rng.normal(size=m)
        Q, Pt, R, S = [psd(k) for k in (n, n, m, m)]
        C = np.eye(d)[:n]
        # Build F,G independently by causal impulses, including noncommuting A.
        F, G = [], np.zeros((N*d, N*m))
        z = z0.copy()
        for i in range(N):
            z = A[i] @ z
            F.append(z.copy())
        F = np.array(F).reshape(-1)
        for j in range(N*m):
            z = np.zeros(d)
            for i in range(N):
                uj = np.zeros(m)
                if i == j // m:
                    uj[j % m] = 1.
                z = A[i] @ z + B[i] @ uj
                G[i*d:(i+1)*d, j] = z
        Cbar = np.kron(np.eye(N), C)
        Qbar = blockdiag([Q]*(N-1)+[Pt])
        Rbar, Sbar = np.kron(np.eye(N), R), np.kron(np.eye(N), S)
        D = np.eye(N*m)
        for i in range(1, N):
            D[i*m:(i+1)*m, (i-1)*m:i*m] = -np.eye(m)
        chat = np.r_[-uprev, np.zeros((N-1)*m)]
        W = Cbar @ F - xref[1:].reshape(-1)
        M = G.T @ Cbar.T @ Qbar @ Cbar @ G + Rbar + D.T @ Sbar @ D
        f = G.T @ Cbar.T @ Qbar @ W - Rbar @ uref.reshape(-1) + D.T @ Sbar @ chat
        const = W @ Qbar @ W + uref.reshape(-1) @ Rbar @ uref.reshape(-1) + chat @ Sbar @ chat
        Fc, Gc = ltv.prediction_matrices(A, B, z0)
        Mc, fc, cc = ltv.cost_matrices(Fc, Gc, xref, uref, Q, Pt, R, S, uprev, n_state=n)
        direct, z = 0., z0.copy()
        for i in range(N):
            z = A[i] @ z + B[i] @ U[i]
            e = C @ z - xref[i+1]
            weight = Q if i < N-1 else Pt
            du = U[i]-uref[i]
            dr = U[i]-(uprev if i == 0 else U[i-1])
            direct += e @ weight @ e + du @ R @ du + dr @ S @ dr
        quad = U.reshape(-1) @ M @ U.reshape(-1) + 2*f @ U.reshape(-1) + const
        prefix = f'n{n}_N{N}'
        check(prefix+'_prediction_F', np.max(abs(F-Fc.reshape(-1))), 1e-12)
        check(prefix+'_prediction_G', np.max(abs(G-Gc.reshape(N*d, N*m))), 1e-12)
        check(prefix+'_M_f_const', max(np.max(abs(M-Mc)), np.max(abs(f-fc)), abs(const-cc)), 1e-9)
        actual = ltv.cost_value(U.reshape(-1), Fc, Gc, xref, uref, Q, Pt, R, S, uprev, n_state=n)
        check(prefix+'_direct_quad_current', max(abs(direct-quad), abs(direct-actual)), 1e-9*max(1., abs(direct)))
        check(prefix+'_Hessian_PSD', max(0., -np.linalg.eigvalsh(2*M).min()), 1e-10)
        Qz = C.T @ Q @ C
        # Output residual equals any lifted extension with correct first n coordinates.
        zr = rng.normal(size=d)
        zr[:n] = xref[N]
        check(prefix+'_effective_lifted_weight', abs((z-zr)@Qz@(z-zr)-(C@z-xref[N])@Q@(C@z-xref[N])), 1e-10)

# Toy low-rank scheduled model: n=1,d=2,m=1,P=2, globally Lipschitz context.
P, N = 2, 3
A0 = np.array([[.6, .1], [.05, .55]])
B0 = np.array([.2, .1])
gA, gB = .05, .04
uf = np.array([1., 0.])
vf = np.array([0., 1.])
context_weights = np.array([.2, .2, .1])
Lphi = np.linalg.norm(context_weights)
MA, MB = np.linalg.norm(A0, 2)+gA, np.linalg.norm(B0)+gB
LA, LB, MU = gA, gB, 1.
z0, history_x, history_u = np.array([.3, -.1]), .25, .15
ubar = np.array([.1, -.2, .3])


def schedule(xh, uh, z):
    c = context_weights @ np.r_[xh, uh]
    return A0 + gA*np.tanh(c)*np.outer(uf, vf), B0 + gB*np.tanh(z[0])*uf


def rollout(U, frozen=None):
    z, xh, uh = z0.copy(), np.array([history_x, z0[0]]), history_u
    zs, As, Bs = [z.copy()], [], []
    for i, ui in enumerate(U):
        a, b = schedule(xh, uh, z) if frozen is None else (frozen[0][i], frozen[1][i])
        z = a @ z + b*ui
        zs.append(z.copy()); As.append(a); Bs.append(b)
        xh, uh = np.array([xh[-1], z[0]]), ui
    return np.array(zs), np.array(As), np.array(Bs)


nom, an, bn = rollout(ubar)
fr_nom, _, _ = rollout(ubar, (an, bn))
check('same_input_zero_freezing_error', np.max(abs(nom-fr_nom)), 1e-14)
state_bound = [np.linalg.norm(z0)]
for _ in range(N):
    state_bound.append(MA*state_bound[-1]+MB*MU)
MZ = max(state_bound)
L = MA + LB*MU + LA*Lphi*np.sqrt(P)*MZ
du_uniform = np.max(1.+abs(ubar))
delta_frz = LA*Lphi*MZ*np.sqrt(P-1)*du_uniform + (LA*Lphi*np.sqrt(P)*MZ+LB*MU)*MB*du_uniform*sum(MA**t for t in range(N))
K = np.array([0.]+[delta_frz*sum(L**t for t in range(i)) for i in range(1, N+1)])
xref = np.array([.9, -.4, .2, .1])
Q, Pt = 1.3, 2.1
epsilon = 2*(MZ+max(abs(xref[1:])))*(Q*sum(K[1:-1])+Pt*K[-1])+Q*sum(K[1:-1]**2)+Pt*K[-1]**2


def cost(zs, U):
    state = Q*sum((zs[1:-1, 0]-xref[1:-1])**2)+Pt*(zs[-1, 0]-xref[-1])**2
    input_cost = .2*sum(U**2)+.1*sum(np.diff(np.r_[history_u, U])**2)
    return state+input_cost


full_costs, fr_costs, max_error, max_diff = [], [], 0., 0.
for items in itertools.product(np.linspace(-1., 1., 9), repeat=N):
    U = np.array(items)
    full, af, bf = rollout(U)
    fr, _, _ = rollout(U, (an, bn))
    err, drift = full-fr, fr-nom
    exact = np.array([an[i]@err[i]+(af[i]-an[i])@full[i]+(bf[i]-bn[i])*U[i] for i in range(N)])
    assert np.max(abs(exact-err[1:])) < 1e-14
    assert np.max(np.linalg.norm(full, axis=1)-MZ) <= 1e-12
    assert np.max(np.linalg.norm(err, axis=1)-K) <= 1e-12
    max_error = max(max_error, float(np.linalg.norm(err, axis=1).max()))
    jf, jr = cost(full, U), cost(fr, U)
    full_costs.append(jf); fr_costs.append(jr)
    max_diff = max(max_diff, abs(jf-jr))
check('toy_freezing_recurrence_and_bound_729_candidates', 0., 0.)
check('toy_measurement_uniform_cost_bound', max_diff, epsilon)
ufr = int(np.argmin(fr_costs)); ustar = int(np.argmin(full_costs))
gap = full_costs[ufr]-full_costs[ustar]
check('toy_common_grid_2epsilon_suboptimality', gap, 2*epsilon)
# These grid argmins are exact only on this finite common candidate set.

# 05 finite reference residual check, with shared real past slots and same inputs.
truth = np.r_[z0[None], rng.normal(scale=.3, size=(N, 2))]
U = np.array([.5, -.2, .7])
prop, _, _ = rollout(U)
residuals, xh, uh = [], np.array([history_x, z0[0]]), history_u
for i in range(N):
    a, b = schedule(xh, uh, truth[i])
    residuals.append(truth[i+1]-a@truth[i]-b*U[i])
    xh, uh = np.array([xh[-1], truth[i+1, 0]]), U[i]
delta = np.max(np.linalg.norm(residuals, axis=1))
MZ_pred = max(MZ, np.linalg.norm(truth, axis=1).max())
Lp = MA+LB*MU+LA*Lphi*np.sqrt(P)*MZ_pred
prediction_bound = np.array([0.]+[delta*sum(Lp**t for t in range(i)) for i in range(1, N+1)])
check('toy_prediction_zero_initial_uniform_residual_bound', max(0., (np.linalg.norm(truth-prop, axis=1)-prediction_bound).max()), 1e-12)
for factor in [0., .25, 1., 1.5]:
    S = [0.]
    W = 0.
    for _ in range(12):
        S.append(.2+factor*S[-1]); W = max(W, .2+factor*W)
        assert W <= S[-1]+1e-12
check('comparison_sequence_L_branches', 0., 0.)

data = {'task': 'TASK-048', 'passed': all(r['passed'] for r in results), 'checks': results,
        'toy_observations': {'max_freezing_error': max_error, 'max_cost_diff': max_diff, 'epsilon': epsilon, 'common_grid_gap': gap},
        'limits': ['synthetic cases only; not real-device uniform certification', '729 finite candidates, not continuous full global optimizer', 'no solver exact-argmin certificate', 'no training or plant experiment']}
output = ROOT / '.project-log' / 'docs' / 'task048-reconciliation-tests.json'
output.write_text(json.dumps(data, indent=2), encoding='utf-8')
print(f'TASK048 reconciliation checks: {len(results)}/{len(results)} PASS')
