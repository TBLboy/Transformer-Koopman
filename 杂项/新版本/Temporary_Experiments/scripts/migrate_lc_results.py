# -*- coding: utf-8 -*-
"""One-off migration of results/modeling/latent_consistency_<device>.json.

Why: the first real (50-epoch) run finished M4/base seed0 BEFORE the per-run
"epochs" tag existed, so the resumable grid would have discarded it as "not
produced at this epoch count".  At the same time, three 5-epoch smoke entries are
still sitting in the file and must not be mistaken for real results.

This script:
  * backs the file up verbatim;
  * tags legacy runs with epochs = --epochs when they clearly ran the full budget
    (info.epochs_run > 10; the smoke runs used exactly 5);
  * drops the stale smoke runs and records them under "archived_smoke".
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "models"))
sys.path.insert(0, HERE)

import device as dev                       # noqa: E402
dev.bootstrap_from_argv()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", "-d", default=None)
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--legacy-min-epochs-run", type=int, default=10)
    args = ap.parse_args()

    path = os.path.join(dev.results_dir("modeling"),
                        "latent_consistency_%s.json" % dev.current()["name"])
    if not os.path.exists(path):
        print("no file at %s -- nothing to do" % path)
        return 0
    backup = path.replace(".json", ".premigration.json")
    shutil.copyfile(path, backup)
    print("backup -> %s" % backup)

    d = json.load(io.open(path, encoding="utf-8"))
    archived = []
    tagged = []
    for spec in sorted(d.get("arms", {})):
        for arm in sorted(d["arms"][spec]):
            entry = d["arms"][spec][arm]
            keep = []
            for r in entry.get("runs", []):
                if "epochs" in r:
                    keep.append(r)
                    continue
                er = int((r.get("info") or {}).get("epochs_run", 0) or 0)
                if er > args.legacy_min_epochs_run:
                    r["epochs"] = args.epochs
                    r["epochs_tagged_by_migration"] = True
                    keep.append(r)
                    tagged.append("%s/%s seed%d (epochs_run=%d)" % (spec, arm, r["seed"], er))
                else:
                    r["_stale_reason"] = "smoke run (epochs_run=%d)" % er
                    archived.append({"spec": spec, "arm": arm, "run": r})
            entry["runs"] = keep
    d["archived_smoke"] = archived
    d["migration"] = {"at": time.strftime("%Y-%m-%d %H:%M:%S"),
                      "tagged": tagged, "archived": len(archived)}
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    print("tagged  : %s" % (tagged if tagged else "none"))
    print("archived: %d stale smoke run(s)" % len(archived))
    for spec in sorted(d.get("arms", {})):
        for arm in sorted(d["arms"][spec]):
            runs = d["arms"][spec][arm]["runs"]
            print("  %s/%-5s kept=%d seeds=%s" % (spec, arm, len(runs),
                                                  sorted(r["seed"] for r in runs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
