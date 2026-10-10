"""ALN-010 regression guard: one EDMD solve, shared by every trainer.

The legacy tree had three copies of the closed-form EDMD solve; two used
``np.linalg.inv`` and one used ``np.linalg.solve``. These tests pin the single
shared implementation and its numerical behaviour.
"""
import re
from pathlib import Path

import numpy as np
import pytest

from conftest import SRC_DIR

from patchtst_koopman.utils.koopman_solve import solve_koopman_operator


def closed_form_inv(Z, Z_next, U, reg):
    """The legacy ``inv``-based formulation, kept here as the reference."""
    ZU = np.concatenate([Z, U], axis=1)
    ZU_T_ZU = ZU.T @ ZU
    reg_mat = reg * np.eye(ZU_T_ZU.shape[0], dtype=ZU_T_ZU.dtype)
    K = Z_next.T @ ZU @ np.linalg.inv(ZU_T_ZU + reg_mat)
    d = Z.shape[1]
    return K[:, :d], K[:, d:]


def make_problem(n=200, d=6, m=3, seed=0):
    rng = np.random.default_rng(seed)
    Z = rng.normal(size=(n, d))
    U = rng.normal(size=(n, m))
    A_true = rng.normal(size=(d, d)) * 0.3
    B_true = rng.normal(size=(d, m)) * 0.3
    Z_next = Z @ A_true.T + U @ B_true.T + rng.normal(size=(n, d)) * 0.01
    return Z, Z_next, U


def test_solve_matches_closed_form():
    Z, Z_next, U = make_problem()
    A, B = solve_koopman_operator(Z, Z_next, U, 1e-6)
    A_ref, B_ref = closed_form_inv(Z, Z_next, U, 1e-6)
    np.testing.assert_allclose(A, A_ref, rtol=1e-8, atol=1e-10)
    np.testing.assert_allclose(B, B_ref, rtol=1e-8, atol=1e-10)


def test_shapes_and_recovery():
    Z, Z_next, U = make_problem(n=500, d=6, m=3, seed=1)
    A, B = solve_koopman_operator(Z, Z_next, U, 1e-8)
    assert A.shape == (6, 6)
    assert B.shape == (6, 3)
    # the recovered operator should predict the next state well
    residual = np.linalg.norm(Z_next - (Z @ A.T + U @ B.T)) / np.linalg.norm(Z_next)
    assert residual < 0.05, f"relative residual too high: {residual}"


def test_solve_is_at_least_as_stable_as_inv():
    """On an ill-conditioned normal matrix, ``solve`` must not be worse."""
    rng = np.random.default_rng(2)
    n, d, m = 40, 8, 2
    Z = rng.normal(size=(n, d))
    U = rng.normal(size=(n, m))
    Z_next = rng.normal(size=(n, d))
    # a tiny ridge makes ZU.T @ ZU nearly singular
    reg = 1e-14

    A, B = solve_koopman_operator(Z, Z_next, U, reg)
    A_ref, B_ref = closed_form_inv(Z, Z_next, U, reg)

    ZU = np.concatenate([Z, U], axis=1)
    M = ZU.T @ ZU + reg * np.eye(ZU.shape[1])
    rhs = ZU.T @ Z_next
    res_solve = np.linalg.norm(M @ np.linalg.solve(M, rhs) - rhs)
    res_inv = np.linalg.norm(M @ (np.linalg.inv(M) @ rhs) - rhs)
    assert res_solve <= res_inv * 10 + 1e-12, (
        f"solve residual {res_solve} unexpectedly worse than inv {res_inv}"
    )
    assert np.all(np.isfinite(A)) and np.all(np.isfinite(B))


def test_no_linalg_inv_remains_in_src():
    """The fragile formulation must not creep back in."""
    # koopman_solve.py documents the legacy formulation in its docstring, so it
    # is the one module allowed to mention np.linalg.inv.
    allowed = {SRC_DIR / "patchtst_koopman" / "utils" / "koopman_solve.py"}
    offenders = []
    for path in sorted(SRC_DIR.rglob("*.py")):
        if "__pycache__" in path.parts or path in allowed:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"linalg\.inv\b", line):
                offenders.append(f"{path.relative_to(SRC_DIR)}:{lineno}: {line.strip()}")
    assert not offenders, (
        "np.linalg.inv found in src/; use utils/koopman_solve.solve_koopman_operator "
        "instead (ALN-010):\n  " + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("module", [
    "patchtst_koopman.training.edmd_trainer",
    "patchtst_koopman.training.mlp_koopman_trainer",
    "patchtst_koopman.training.traditional_edmd_trainer",
])
def test_trainers_use_the_shared_solver(module):
    import importlib
    mod = importlib.import_module(module)
    assert hasattr(mod, "solve_koopman_operator"), (
        f"{module} does not import the shared solver"
    )
