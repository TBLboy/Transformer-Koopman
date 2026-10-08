from pathlib import Path
import json
import numpy as np
import torch

MODEL = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\deploy\algorithms\tk_assets\model_assets\platform2_full_model.pth")
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\spike_a2_relative_degree.json")

obj = torch.load(MODEL, map_location="cpu", weights_only=False)
A = np.asarray(obj["koopman_A"], float)
B = np.asarray(obj["koopman_B"], float)
n = A.shape[0]

# Candidate output map: measured light-point position only, C = [I2 0].
C = np.zeros((2, n))
C[:, :2] = np.eye(2)

# Linear relative degree: find the first r >= 1 with rank(C A^{r-1} B) = number of outputs.
steps = []
r = None
for k in range(n):
    M = C @ np.linalg.matrix_power(A, k) @ B
    sv = np.linalg.svd(M, compute_uv=False)
    rank = int(np.linalg.matrix_rank(M, tol=1e-8))
    steps.append({
        "r": k + 1,
        "matrix": "C A^%d B" % k,
        "rank": rank,
        "singular_values": sv.tolist(),
        "condition_number": float(np.linalg.cond(M)) if sv[-1] > 0 else None,
        "full_rank": rank == C.shape[0],
    })
    if rank == C.shape[0] and r is None:
        r = k + 1

# Also test the physically more direct map: does u enter the measured position block?
B_pos_block = B[:2, :]
sv_pos = np.linalg.svd(B_pos_block, compute_uv=False)

result = {
    "output_map": "C = [I2, 0] (measured light point)",
    "input_block_on_output": B_pos_block.tolist(),
    "input_block_on_output_rank": int(np.linalg.matrix_rank(B_pos_block, tol=1e-8)),
    "input_block_on_output_singular_values": sv_pos.tolist(),
    "first_full_rank_relative_degree": r,
    "relative_degree_steps": steps,
    "warning": "Relative degree of the exported linear checkpoint; not evidence that the learned latent is physically valid or that a nonlinear relative degree is preserved.",
}
print(json.dumps(result, indent=2))
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
