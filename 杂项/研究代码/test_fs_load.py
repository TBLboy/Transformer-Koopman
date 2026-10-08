# -*- coding: utf-8 -*-
"""Load-test the FS-KOOPMAN model and inspect its lift config."""
import os, sys, json
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OLD = r"D:\Project\my_lunwen\结果备份\软体平台训练结果"
MC = r"D:\Project\my_lunwen\建模代码"
sys.path.insert(0, MC)
from modeling.trainers.fs_edmd import OursKoopmanTrainer  # noqa: E402

m = OursKoopmanTrainer(verbose=False).load(os.path.join(OLD, "fs_edmd.pkl"))
print("loaded fs_edmd.pkl")
print("  A_model", m.A_model.shape, "B_model", m.B_model.shape, "C_model", m.C_model.shape, "D_model", m.D_model.shape)
print("  N =", m.N)
print("  lift_config =", json.dumps(m.lift_config, ensure_ascii=False, default=str)[:600])
print("  lift_fn type:", type(m.lift_fn).__name__)
print("  lift_fn fitted:", getattr(m.lift_fn, "fitted", None))

# test predict in normalized space (arbitrary small input)
x0 = np.array([0.1, -0.2])
us = [np.array([0.0, 0.0]) for _ in range(5)]
try:
    p = m.predict(x0, us)
    print("  predict ok, out shape:", p.shape)
    print("  first rows:\n", p[:3])
except Exception as ex:
    import traceback
    traceback.print_exc()
