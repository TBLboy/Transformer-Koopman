from pathlib import Path
from collections import Counter, defaultdict
import json
import numpy as np

ROOT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
DATA = ROOT / "数据备份" / "软体平台数据" / "处理后的数据"

def entropy(counter):
    n = sum(counter.values())
    if not n:
        return 0.0
    p = np.array(list(counter.values()), dtype=float) / n
    return float(-(p * np.log2(p)).sum())

def key(x):
    return tuple(float(v) for v in x)

report = {"splits": {}, "global": {}}
all_actions = Counter()
all_prefix = {1: Counter(), 2: Counter(), 3: Counter()}
for split in ("train", "val", "test"):
    z = np.load(DATA / f"{split}.npz")
    x, u, t, tid = z["x"], z["u"], z["t"], z["trajectory_id"]
    trajectories = []
    for ident in np.unique(tid):
        ix = np.flatnonzero(tid == ident)
        uu = u[ix]
        xx = x[ix]
        dt = np.diff(t[ix])
        trajectories.append({"id": int(ident), "n": int(len(ix)), "dt_min": float(dt.min()) if len(dt) else None, "dt_max": float(dt.max()) if len(dt) else None, "dt_mean": float(dt.mean()) if len(dt) else None})
        for a in uu:
            all_actions[key(a)] += 1
        for h in (1, 2, 3):
            for j in range(len(uu) - h + 1):
                all_prefix[h][tuple(key(a) for a in uu[j:j+h])] += 1
    unique = Counter(key(a) for a in u)
    integer_distance = np.abs(u - np.rint(u))
    report["splits"][split] = {
        "rows": int(len(x)),
        "state_shape": list(x.shape),
        "control_shape": list(u.shape),
        "trajectories": trajectories,
        "n_trajectories": len(trajectories),
        "unique_action_vectors": len(unique),
        "action_entropy_bits": entropy(unique),
        "integer_max_abs_error": float(integer_distance.max()),
        "integer_fraction_exact": float(np.all(integer_distance < 1e-12, axis=1).mean()),
        "action_min": u.min(axis=0).tolist(),
        "action_max": u.max(axis=0).tolist(),
        "action_mean": u.mean(axis=0).tolist(),
        "action_std": u.std(axis=0).tolist(),
    }

report["global"] = {
    "unique_actions_all_splits": len(all_actions),
    "top_actions": [[list(k), int(v)] for k, v in all_actions.most_common(20)],
    "prefixes": {
        str(h): {
            "unique": len(c),
            "count_ge_2": int(sum(v >= 2 for v in c.values())),
            "count_ge_5": int(sum(v >= 5 for v in c.values())),
            "count_ge_10": int(sum(v >= 10 for v in c.values())),
            "max_count": int(max(c.values()) if c else 0),
        } for h, c in all_prefix.items()
    },
}
out = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\audit_p2_psr.json")
print(json.dumps(report, ensure_ascii=False, indent=2))
