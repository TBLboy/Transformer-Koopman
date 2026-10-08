from pathlib import Path
import json
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
P1D = ROOT / "数据备份" / "机械臂数据" / "处理后的数据"
P2D = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\V_P12.json")

def sym_min_eig(J):
    S = 0.5 * (J + J.T)
    return float(np.linalg.eigvalsh(S)[0])

def curl_ratio(J):
    return float(np.linalg.norm(J - J.T) / (np.linalg.norm(J + J.T) + 1e-12))

def global_fit(Phi_u, d):
    X = np.hstack([np.ones((len(d), 1)), Phi_u])
    th, *_ = np.linalg.lstsq(X, d, rcond=None)
    dhat = X @ th
    res = d - dhat
    J = th[1:].T  # (dim_d, dim_u)
    return {"J": J, "rmse": float(np.sqrt((res**2).mean())),
            "sym_min_eig_raw": sym_min_eig(J), "curl_raw": curl_ratio(J)}

def local_fit(phi, u, d, k=300, n_query=600):
    tree = cKDTree(phi)
    idx = np.linspace(0, len(phi) - 1, n_query).astype(int)
    mins, curls, rmse, smins = [], [], [], []
    for i in idx:
        _, nb = tree.query(phi[i], k=k)
        X = np.hstack([np.ones((k, 1)), u[nb]])
        th, *_ = np.linalg.lstsq(X, d[nb], rcond=None)
        J = th[1:].T
        mins.append(sym_min_eig(J)); curls.append(curl_ratio(J))
        smins.append(float(np.linalg.svd(J, compute_uv=False)[-1]))
        rmse.append(float(np.sqrt(((d[nb] - X @ th) ** 2).mean())))
    mins = np.array(mins); curls = np.array(curls); smins = np.array(smins)
    return {"sym_min_eig_median": float(np.median(mins)),
            "sym_min_eig_q05": float(np.quantile(mins, 0.05)),
            "sym_min_eig_q95": float(np.quantile(mins, 0.95)),
            "frac_sym_min_eig_pos": float((mins > 0).mean()),
            "curl_median": float(np.median(curls)),
            "sigma_min_median": float(np.median(smins)),
            "sigma_min_q05": float(np.quantile(smins, 0.05)),
            "local_rmse_median": float(np.median(rmse))}

def ambiguity(phi_u, d, radius_frac=0.01, n_query=400):
    tree = cKDTree(phi_u)
    r = radius_frac * np.mean(phi_u.std(0))
    idx = np.linspace(0, len(phi_u) - 1, n_query).astype(int)
    spreads, counts = [], []
    for i in idx:
        nb = tree.query_ball_point(phi_u[i], r)
        if len(nb) < 5: continue
        dd = d[nb]
        spreads.append(float(np.linalg.norm(dd.std(0))))
        counts.append(len(nb))
    base = float(np.linalg.norm(d.std(0)))
    return {"n_ctx": len(spreads), "ambig_spread_median": float(np.median(spreads)) if spreads else None,
            "baseline_spread": base,
            "ambig_over_baseline": float(np.median(spreads) / base) if spreads else None,
            "mean_neighbors": float(np.mean(counts)) if counts else None}

res = {}

# ---------------- P1 ----------------
z1 = np.load(P1D / "train.npz")
x1 = z1["x"].astype(float); u1 = z1["u"].astype(float); t1 = z1["t"].astype(float)
tid1 = z1["trajectory_id"]
q = x1[:, 0:6:2]; dq = x1[:, 1:6:2]
D1, U1, PHI1 = [], [], []
for t in np.unique(tid1):
    m = np.where(tid1 == t)[0]
    if len(m) < 5: continue
    tt = t1[m]; xx = x1[m]; uu = u1[m]
    order = np.argsort(tt); tt = tt[order]; xx = xx[order]; uu = uu[order]
    dtv = np.diff(tt)
    dtv = np.where(dtv <= 0, np.median(dtv[dtv > 0]) if np.any(dtv > 0) else 0.004, dtv)
    acc = (xx[1:, 1:6:2] - xx[:-1, 1:6:2]) / dtv[:, None]
    D1.append(acc); U1.append(uu[:-1])
    PHI1.append(np.hstack([xx[:-1, 0:6:2], xx[:-1, 1:6:2]]))
D1 = np.concatenate(D1); U1 = np.concatenate(U1); PHI1 = np.concatenate(PHI1)
dt_med = float(np.median(np.diff(np.sort(t1[:len(t1)])))) if len(t1) > 1 else None
res["P1"] = {"n": int(len(D1)), "dt_median_sample": dt_med,
             "d_std": D1.std(0).tolist(), "u_std": U1.std(0).tolist()}
g1 = global_fit(U1, D1)
res["P1"]["T5_A_global"] = {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in g1.items() if k != "J"}
res["P1"]["T5_A_global"]["J"] = g1["J"].tolist()
# normalize both sides for scale-free comparison
Dn = (D1 - D1.mean(0)) / D1.std(0); Un = (U1 - U1.mean(0)) / U1.std(0)
gn1 = global_fit(Un, Dn)
res["P1"]["T5_A_global_normalized"] = {"sym_min_eig": gn1["sym_min_eig_raw"], "curl": gn1["curl_raw"]}
res["P1"]["T5_A_local"] = local_fit(PHI1, U1, D1, k=400, n_query=600)
res["P1"]["T5_E_ambiguity"] = ambiguity(np.hstack([PHI1, U1]), D1, n_query=400)

# ---------------- P2 ----------------
z2 = np.load(P2D / "train.npz")
x2 = z2["x"].astype(float); u2 = z2["u"].astype(float); tid2 = z2["trajectory_id"]
D2, U2, PHI2 = [], [], []
L = 3
for t in np.unique(tid2):
    m = np.where(tid2 == t)[0]
    if len(m) < L + 2: continue
    xx = x2[m]; uu = u2[m]
    for k in range(L, len(xx) - 1):
        D2.append(xx[k + 1] - xx[k]); U2.append(uu[k])
        ctx = []
        for j in range(L): ctx.append(xx[k - j])
        for j in range(1, L + 1):
            if k - j >= 0: ctx.append(uu[k - j])
        PHI2.append(np.concatenate(ctx))
D2 = np.array(D2); U2 = np.array(U2); PHI2 = np.array(PHI2)
res["P2"] = {"n": int(len(D2)), "d_std": D2.std(0).tolist(), "u_std": U2.std(0).tolist()}
g2 = global_fit(U2, D2)
res["P2"]["T5_A_global"] = {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in g2.items() if k != "J"}
res["P2"]["T5_A_global"]["J"] = g2["J"].tolist()
Dn2 = (D2 - D2.mean(0)) / D2.std(0); Un2 = (U2 - U2.mean(0)) / U2.std(0)
gn2 = global_fit(Un2, Dn2)
res["P2"]["T5_A_global_normalized"] = {"sym_min_eig": gn2["sym_min_eig_raw"], "curl": gn2["curl_raw"]}
res["P2"]["T5_AB_local"] = local_fit(PHI2, U2, D2, k=300, n_query=600)
res["P2"]["T5_E_ambiguity"] = ambiguity(np.hstack([PHI2, U2]), D2, n_query=400)

print(json.dumps(res, indent=2))
OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
