# -*- coding: utf-8 -*-
import sys, io, yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DEAD = [
    "controller", "evaluation", "logging",
    "data.add_noise", "data.noise_level", "data.noise_type", "data.normalization_method",
    "encoder.positional_encoding", "koopman.enforce_stability", "koopman.model_type",
    "decoder.decoder_type", "training.val_every_n_epochs", "training.save_every_n_epochs",
    "training.save_best_only", "training.edmd.pretrain.optimizer",
    "training.edmd.compute.batch_encode", "training.end_to_end.optimizer",
    "mlp_koopman.edmd.pretrain.optimizer", "mlp_koopman.end_to_end.optimizer",
    "lstm_koopman.edmd.pretrain.optimizer", "lstm_koopman.end_to_end.optimizer",
]

def get(d, path):
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur

for name in ["platform1.yaml", "platform2.yaml"]:
    path = r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\configs" + "\\" + name
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    print("=== %s ===" % name)
    print("top-level:", list(cfg.keys()))
    bad = [k for k in DEAD if get(cfg, k) is not None]
    print("remaining dead keys:", bad if bad else "NONE")
    # keep-checks
    print("koopman.rho_max =", get(cfg, "koopman.rho_max"))
    print("experiment.log_dir =", get(cfg, "experiment.log_dir"))
    print("encoder.readout_method =", get(cfg, "encoder.readout_method"))
