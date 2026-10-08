# -*- coding: utf-8 -*-
import sys, io, numpy as np, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

base = r"D:\Project\Transformer-Koopman\Transformer-Koopman\数据备份"
for sub in [r"机械臂数据\处理后的数据", r"软体平台数据\处理后的数据"]:
    print("=" * 60)
    print(sub)
    for split in ["train", "val", "test"]:
        p = os.path.join(base, sub, split + ".npz")
        if not os.path.exists(p):
            print("  %s: MISSING" % split); continue
        with np.load(p) as z:
            info = ["%s%s%s" % (k, z[k].shape, z[k].dtype) for k in z.files]
            print("  %s: %s" % (split, " | ".join(info)))
