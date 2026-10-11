# -*- coding: utf-8 -*-
"""Gate 0 data audit for the soft-platform (Platform 2) dataset.

Read-only with respect to the source data: this script only reads
``数据备份/软体平台数据/**`` and writes audit artifacts under
``杂项/新版本/Temporary_Experiments/results/audit/``.

Outputs
-------
* ``results/audit/data_audit_raw.json`` -- per-recording facts + split mapping
* ``results/audit/data_audit_summary.txt`` -- human-readable summary

Run (from anywhere):
    D:\\conda\\envs\\edmddl2\\python.exe scripts/audit_data.py
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXP_DIR = os.path.dirname(HERE)                       # Temporary_Experiments/
REPO = os.path.dirname(os.path.dirname(os.path.dirname(EXP_DIR)))  # Transformer-Koopman/
DATA_ROOT = os.path.join(REPO, "数据备份", "软体平台数据")
RAW_DIR = os.path.join(DATA_ROOT, "原始数据")
PROC_DIR = os.path.join(DATA_ROOT, "处理后的数据")
OUT_DIR = os.path.join(EXP_DIR, "results", "audit")

SPLIT_PLAN = {"train": 70, "val": 20, "test": 10}

lines: list[str] = []


def p(s: str = "") -> None:
    lines.append(s)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rng(a: np.ndarray) -> dict:
    a = np.asarray(a, dtype=np.float64)
    return {
        "min": np.nanmin(a, axis=0).round(6).tolist(),
        "max": np.nanmax(a, axis=0).round(6).tolist(),
        "mean": np.nanmean(a, axis=0).round(6).tolist(),
        "std": np.nanstd(a, axis=0).round(6).tolist(),
    }


def audit_raw() -> dict:
    files = sorted(f for f in os.listdir(RAW_DIR) if f.endswith(".npz"))
    p("=" * 78)
    p("A. RAW RECORDINGS  (%s)" % RAW_DIR)
    p("=" * 78)
    p("  files found: %d" % len(files))

    recs = {}
    dt_all = []
    for fn in files:
        fp = os.path.join(RAW_DIR, fn)
        z = np.load(fp, allow_pickle=True)
        keys = sorted(z.files)
        t = np.asarray(z["t"], dtype=np.float64).reshape(-1)
        x = np.asarray(z["x"], dtype=np.float64)
        u = np.asarray(z["u"], dtype=np.float64)
        dt = np.diff(t)
        # discontinuity / reset detection on the state
        dx = np.abs(np.diff(x, axis=0))
        rec = {
            "file": fn,
            "sha256": sha256(fp),
            "bytes": os.path.getsize(fp),
            "keys": keys,
            "n": int(len(t)),
            "t0": float(t[0]),
            "t_end": float(t[-1]),
            "t_monotonic": bool(np.all(dt > 0)),
            "dt_min": float(dt.min()),
            "dt_max": float(dt.max()),
            "dt_mean": float(dt.mean()),
            "dt_std": float(dt.std()),
            "n_dt_off_nominal": int(np.sum(np.abs(dt - dt.mean()) > 1e-9)),
            "n_duplicate_t": int(len(t) - len(np.unique(t))),
            "x_nan": int(np.sum(~np.isfinite(x))),
            "u_nan": int(np.sum(~np.isfinite(u))),
            "t_nan": int(np.sum(~np.isfinite(t))),
            "x": rng(x),
            "u": rng(u),
            "max_abs_dx": float(dx.max()),
            "argmax_abs_dx": int(dx.max(axis=1).argmax()),
            "x_start": x[0].round(6).tolist(),
            "x_end": x[-1].round(6).tolist(),
            "u_absmax": float(np.abs(u).max()),
            "u_unique_frac": float(len(np.unique(u.round(6))) / u.size),
        }
        recs[fn] = rec
        dt_all.append(dt)

    dt_cat = np.concatenate(dt_all)
    p("  n samples per recording: %s (all equal: %s)"
      % (sorted({r["n"] for r in recs.values()}), len({r["n"] for r in recs.values()}) == 1))
    p("  dt over ALL recordings: min=%.9f max=%.9f mean=%.9f std=%.3e"
      % (dt_cat.min(), dt_cat.max(), dt_cat.mean(), dt_cat.std()))
    p("  dt off-nominal count (|dt-mean|>1e-9): %d / %d"
      % (sum(r["n_dt_off_nominal"] for r in recs.values()), dt_cat.size))
    p("  duplicate timestamps: %d total" % sum(r["n_duplicate_t"] for r in recs.values()))
    p("  non-monotonic t: %d recordings" % sum(1 for r in recs.values() if not r["t_monotonic"]))
    p("  NaN/Inf: x=%d u=%d t=%d"
      % (sum(r["x_nan"] for r in recs.values()), sum(r["u_nan"] for r in recs.values()),
         sum(r["t_nan"] for r in recs.values())))
    p("  t range per recording: [%s, %s]"
      % (min(r["t0"] for r in recs.values()), max(r["t_end"] for r in recs.values())))
    allx = np.concatenate([np.load(os.path.join(RAW_DIR, f))["x"] for f in files], 0)
    allu = np.concatenate([np.load(os.path.join(RAW_DIR, f))["u"] for f in files], 0)
    p("  pooled x: %s" % json.dumps(rng(allx)))
    p("  pooled u: %s" % json.dumps(rng(allu)))
    p("  max |dx| between consecutive samples across all recordings: %.4f (at %s)"
      % (max(r["max_abs_dx"] for r in recs.values()),
         max(recs.items(), key=lambda kv: kv[1]["max_abs_dx"])[0]))
    return {"files": recs, "order_string_sorted": files,
            "pooled_x": rng(allx), "pooled_u": rng(allu)}


def audit_split(raw: dict) -> dict:
    """Reproduce the documented split (string sort -> 70/20/10) and compare bytes."""
    files = raw["order_string_sorted"]
    n_tr, n_va = SPLIT_PLAN["train"], SPLIT_PLAN["val"]
    groups = {"train": files[:n_tr], "val": files[n_tr:n_tr + n_va],
              "test": files[n_tr + n_va:]}
    p()
    p("=" * 78)
    p("B. SPLIT (string-sorted filename order, %s)" % SPLIT_PLAN)
    p("=" * 78)
    for k, g in groups.items():
        p("  %-5s %2d recordings: %s ... %s" % (k, len(g), g[0], g[-1]))
    p("  NOTE string order: 01..09,10,100,11..99 (100 sorts right after 10)")

    out = {"groups": groups}
    for split, g in groups.items():
        fp = os.path.join(PROC_DIR, "%s.npz" % split)
        z = np.load(fp, allow_pickle=True)
        x_p = z["x"].astype(np.float64)
        u_p = z["u"].astype(np.float64)
        t_p = z["t"].astype(np.float64).reshape(-1)
        tid = z["trajectory_id"]
        # rebuild from raw exactly as prepare_data.py documents
        xs, us, ts, ids = [], [], [], []
        for i, fn in enumerate(g):
            zz = np.load(os.path.join(RAW_DIR, fn), allow_pickle=True)
            xr = zz["x"].astype(np.float64)
            ur = zz["u"].astype(np.float64)
            tr = zz["t"].astype(np.float64).reshape(-1)
            tr = tr - tr[0]
            xs.append(xr); us.append(ur); ts.append(tr)
            ids.append(np.full(len(xr), i, dtype=np.int32))
        x_r = np.concatenate(xs, 0); u_r = np.concatenate(us, 0)
        t_r = np.concatenate(ts, 0); id_r = np.concatenate(ids, 0)
        same = {
            "x": bool(x_p.shape == x_r.shape and np.array_equal(x_p, x_r)),
            "u": bool(u_p.shape == u_r.shape and np.array_equal(u_p, u_r)),
            "t": bool(t_p.shape == t_r.shape and np.array_equal(t_p, t_r)),
            "trajectory_id": bool(id_r.shape == tid.shape and np.array_equal(id_r, tid)),
        }
        lens = [int(np.sum(tid == i)) for i in range(len(g))]
        out[split] = {
            "path": os.path.relpath(fp, REPO),
            "sha256": sha256(fp),
            "bytes": os.path.getsize(fp),
            "x_shape": list(x_p.shape),
            "u_shape": list(u_p.shape),
            "n_traj": int(tid.max()) + 1,
            "traj_lengths": lens,
            "traj_lengths_unique": sorted(set(lens)),
            "x": rng(x_p), "u": rng(u_p),
            "reproduces_from_raw": same,
        }
        p("  %-5s x=%s u=%s trajs=%d lengths=%s"
          % (split, tuple(x_p.shape), tuple(u_p.shape), out[split]["n_traj"],
             out[split]["traj_lengths_unique"]))
        p("        reproduces from raw: %s" % json.dumps(same))
        # within-trajectory dt
        dts = []
        for i in range(out[split]["n_traj"]):
            tt = t_p[tid == i]
            dts.append(np.diff(tt))
        dts = np.concatenate(dts)
        out[split]["dt_within_traj"] = {
            "min": float(dts.min()), "max": float(dts.max()),
            "mean": float(dts.mean()), "std": float(dts.std()),
            "n_off_nominal": int(np.sum(np.abs(dts - dts.mean()) > 1e-9)),
        }
        p("        within-traj dt: min=%.9f max=%.9f std=%.3e off-nominal=%d"
          % (dts.min(), dts.max(), dts.std(), out[split]["dt_within_traj"]["n_off_nominal"]))
    return out


def audit_alignment(raw: dict) -> dict:
    """Check x_k / u_k / x_{k+1} alignment and input saturation evidence."""
    p()
    p("=" * 78)
    p("C. ALIGNMENT & SATURATION EVIDENCE")
    p("=" * 78)
    res = {}
    allu = []
    for fn in raw["order_string_sorted"]:
        z = np.load(os.path.join(RAW_DIR, fn), allow_pickle=True)
        allu.append(np.asarray(z["u"], dtype=np.float64))
    U = np.concatenate(allu, 0)
    for j in range(U.shape[1]):
        col = U[:, j]
        vals, cnt = np.unique(col.round(6), return_counts=True)
        top = np.argsort(-cnt)[:4]
        res["u%d_top_values" % j] = [
            {"value": float(vals[i]), "count": int(cnt[i])} for i in top]
        p("  u[%d]: |u|max=%.4f  top repeated values: %s"
          % (j, np.abs(col).max(),
             ", ".join("%.3f x%d" % (vals[i], cnt[i]) for i in top)))
    # crude saturation test: count of samples at >= 99% of the global max
    gmax = np.abs(U).max(axis=0)
    sat = np.sum(np.abs(U) >= 0.99 * gmax, axis=0)
    res["n_at_99pct_of_max"] = sat.tolist()
    p("  samples within 1%% of |u|max per channel: %s" % sat.tolist())

    # alignment: correlation between u_k and (x_{k+1}-x_k) is a weak but useful signal
    cors = []
    for fn in raw["order_string_sorted"][:25]:
        z = np.load(os.path.join(RAW_DIR, fn), allow_pickle=True)
        x = np.asarray(z["x"], dtype=np.float64)
        u = np.asarray(z["u"], dtype=np.float64)
        dx = np.diff(x, axis=0)
        for j in range(x.shape[1]):
            for i in range(u.shape[1]):
                a = u[:-1, i]; b = dx[:, j]
                if a.std() > 1e-9 and b.std() > 1e-9:
                    cors.append(float(np.corrcoef(a, b)[0, 1]))
    res["corr_u_to_dx_absmax"] = float(np.max(np.abs(cors))) if cors else None
    p("  max |corr(u_k, x_{k+1}-x_k)| over 25 recordings x channels: %.4f"
      % res["corr_u_to_dx_absmax"])
    p("  (weak evidence only: this is a nonlinear system and u enters through B(x))")
    return res


def main() -> int:
    if not os.path.isdir(RAW_DIR):
        print("RAW dir missing: %s" % RAW_DIR, file=sys.stderr)
        return 2
    os.makedirs(OUT_DIR, exist_ok=True)
    raw = audit_raw()
    split = audit_split(raw)
    align = audit_alignment(raw)
    payload = {"raw": raw, "split": split, "alignment": align,
               "data_root": os.path.relpath(DATA_ROOT, REPO)}
    with io.open(os.path.join(OUT_DIR, "data_audit_raw.json"), "w",
                 encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    with io.open(os.path.join(OUT_DIR, "data_audit_summary.txt"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("ok -> %s" % OUT_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
