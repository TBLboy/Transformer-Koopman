from pathlib import Path
import json
import numpy as np
import torch

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
DATA = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
MODEL = ROOT / "训练代码" / "deploy" / "algorithms" / "tk_assets" / "model_assets" / "platform2_full_model.pth"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\spike_a2_a7.json")

def pairs(file, horizon=1):
    z = np.load(DATA / file)
    x, u, tid = z["x"].astype(float), z["u"].astype(float), z["trajectory_id"]
    good = tid[:-horizon] == tid[horizon:]
    return x[:-horizon][good], u[:-horizon][good], x[horizon:][good]

def ridge(Phi, y, lam=1e-5):
    return np.linalg.solve(Phi.T @ Phi + lam * np.eye(Phi.shape[1]), Phi.T @ y)

def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))

def relative_degree_spike():
    xt, ut, yt = pairs("train.npz", 1)
    xv, uv, yv = pairs("val.npz", 1)
    # History-only predictor vs current-input predictor. The comparison is diagnostic,
    # not a theorem: it tests whether u_k adds stable one-step information.
    p0t = np.c_[np.ones(len(xt)), xt]
    p1t = np.c_[p0t, ut]
    p0v = np.c_[np.ones(len(xv)), xv]
    p1v = np.c_[p0v, uv]
    w0, w1 = ridge(p0t, yt), ridge(p1t, yt)
    return {
        "one_step_no_current_u_rmse": rmse(p0v @ w0, yv),
        "one_step_with_current_u_rmse": rmse(p1v @ w1, yv),
        "one_step_incremental_rmse_reduction": rmse(p0v @ w0, yv) - rmse(p1v @ w1, yv),
        "one_step_current_u_coef_norm": float(np.linalg.norm(w1[-2:, :], 2)),
        "one_step_samples": int(len(xv)),
    }

def multi_step_input_effect():
    out = {}
    for h in [1, 2, 3]:
        xt, ut, yt = pairs("train.npz", h)
        xv, uv, yv = pairs("val.npz", h)
        # Compare x-only and x plus current u_h regression at each horizon.
        p0t, p0v = np.c_[np.ones(len(xt)), xt], np.c_[np.ones(len(xv)), xv]
        p1t, p1v = np.c_[p0t, ut], np.c_[p0v, uv]
        w0, w1 = ridge(p0t, yt), ridge(p1t, yt)
        out[str(h)] = {
            "no_u_rmse": rmse(p0v @ w0, yv),
            "with_u_rmse": rmse(p1v @ w1, yv),
            "incremental_rmse_reduction": rmse(p0v @ w0, yv) - rmse(p1v @ w1, yv),
        }
    return out

def controllability_spectrum():
    obj = torch.load(MODEL, map_location="cpu", weights_only=False)
    A, B = np.asarray(obj["koopman_A"], float), np.asarray(obj["koopman_B"], float)
    n = A.shape[0]
    Ctr = np.concatenate([np.linalg.matrix_power(A, i) @ B for i in range(n)], axis=1)
    sv = np.linalg.svd(Ctr, compute_uv=False)
    # ratios are a crude spectrum-gap diagnostic; no threshold is declared as a theorem.
    return {
        "controllability_rank": int(np.linalg.matrix_rank(Ctr, tol=1e-8)),
        "singular_values": sv.tolist(),
        "sigma_min_over_sigma_max": float(sv[-1] / sv[0]),
        "adjacent_ratios": (sv[1:] / sv[:-1]).tolist(),
        "interpretation": "full rank with no predeclared control-relevant spectral cutoff; selection requires a task-error criterion, not rank alone.",
    }

result = {
    "a2_relative_degree_diagnostic": relative_degree_spike(),
    "a2_multi_horizon_input_effect": multi_step_input_effect(),
    "a7_controllability_spectrum_diagnostic": controllability_spectrum(),
    "warning": "These are regression diagnostics on exported/processed data; they do not establish relative-degree preservation, a Koopman theorem, or a valid controller.",
}
print(json.dumps(result, indent=2))
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
