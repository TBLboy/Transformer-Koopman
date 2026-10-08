from pathlib import Path
import json
import numpy as np
import torch

MODEL = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\deploy\algorithms\tk_assets\model_assets\platform2_full_model.pth")
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\p2_observability_diagnostic.json")

obj = torch.load(MODEL, map_location="cpu", weights_only=False)
A = np.asarray(obj["koopman_A"], dtype=float)
B = np.asarray(obj["koopman_B"], dtype=float)
n = A.shape[0]
C = np.zeros((2, n), dtype=float)
C[:, :2] = np.eye(2)

Ctr = np.concatenate([np.linalg.matrix_power(A, i) @ B for i in range(n)], axis=1)
Obs = np.concatenate([C @ np.linalg.matrix_power(A, i) for i in range(n)], axis=0)

eigvals = np.linalg.eigvals(A)
sv_ctr = np.linalg.svd(Ctr, compute_uv=False)
sv_obs = np.linalg.svd(Obs, compute_uv=False)
tol = max(Obs.shape) * np.finfo(float).eps * sv_obs[0]

# PBH detectability check: only eigenvalues outside the unit disk matter.
pbh = []
for lam in eigvals:
    if abs(lam) >= 1.0 - 1e-8:
        pbh.append({
            "eigenvalue_real": float(np.real(lam)),
            "eigenvalue_imag": float(np.imag(lam)),
            "abs": float(abs(lam)),
            "rank_lambdaI_minus_A_stack_C": int(np.linalg.matrix_rank(np.vstack([lam * np.eye(n) - A, C]), tol=1e-8)),
        })

result = {
    "A_shape": list(A.shape),
    "B_shape": list(B.shape),
    "C_shape": list(C.shape),
    "spectral_radius": float(max(abs(eigvals))),
    "controllability_rank": int(np.linalg.matrix_rank(Ctr, tol=1e-8)),
    "controllability_singular_values": sv_ctr.tolist(),
    "observability_rank": int(np.linalg.matrix_rank(Obs, tol=tol)),
    "observability_singular_values": sv_obs.tolist(),
    "observability_matrix_condition_number": float(np.linalg.cond(Obs)),
    "unstable_or_boundary_mode_pbh": pbh,
    "detectability_verdict": "numerically detectable if all listed PBH ranks equal n" if all(x["rank_lambdaI_minus_A_stack_C"] == n for x in pbh) else "not detectable by PBH check",
    "warning": "This is a diagnostic of the exported checkpoint, not evidence that the learned latent coordinates are physically valid.",
}
print(json.dumps(result, indent=2))
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
