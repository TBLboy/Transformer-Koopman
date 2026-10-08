"""Single closed-form EDMD solve shared by every trainer (ALN-010).

The regularised least-squares problem is

    ``[A, B] = Z_next.T @ [Z, U] @ ([Z, U].T @ [Z, U] + λI)^{-1}``

The legacy tree carried three copies of this computation; two used
``np.linalg.inv`` (forming the inverse explicitly, which is less stable) and one
used ``np.linalg.solve``. Keeping one implementation removes the drift risk and
standardises on the more robust formulation.
"""
import numpy as np


def solve_koopman_operator(Z, Z_next, U, regularization):
    """Return ``(A, B)`` for the regularised least-squares EDMD problem.

    Parameters
    ----------
    Z, Z_next : array-like, shape [N, d]
        Lifted states at ``t`` and ``t+1``.
    U : array-like, shape [N, m]
        Controls.
    regularization : float
        Ridge coefficient λ.

    Returns
    -------
    A : ndarray, shape [d, d]
    B : ndarray, shape [d, m]
    """
    Z = np.asarray(Z)
    Z_next = np.asarray(Z_next)
    U = np.asarray(U)

    ZU = np.concatenate([Z, U], axis=1)
    ZU_T_ZU = ZU.T @ ZU
    reg_matrix = regularization * np.eye(ZU_T_ZU.shape[0], dtype=ZU_T_ZU.dtype)
    M = ZU_T_ZU + reg_matrix

    # ``solve`` avoids forming the inverse explicitly. M is symmetric, so the
    # transpose in ``K = (M^{-1} @ ZU.T @ Z_next).T`` is a no-op.
    K = np.linalg.solve(M, ZU.T @ Z_next).T

    d = Z.shape[1]
    return K[:, :d], K[:, d:]
