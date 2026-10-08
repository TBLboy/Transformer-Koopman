# -*- coding: utf-8 -*-
import sys, io, numpy as np, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

base = r"D:\Project\论文3老版本\Transformer-Koopman\data"
for d in ["experiment_001", "experiment_002", "experiment_003", "experiment_004", "experiment_005", "experiment_006"]:
    print("=" * 60)
    print(d)
    for split in ["train", "val", "test"]:
        p = os.path.join(base, d, split + ".npz")
        if not os.path.exists(p):
            print("  %s: MISSING" % split); continue
        with np.load(p) as z:
            info = []
            for k in z.files:
                a = z[k]
                info.append("%s%s%s" % (k, a.shape, a.dtype))
            print("  %s: %s" % (split, " | ".join(info)))
