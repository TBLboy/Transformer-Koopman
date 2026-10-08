import copy
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

CODE = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码")
sys.path.insert(0, str(CODE / "src"))

import yaml
from patchtst_koopman.models.mlp_koopman_model import MLPKoopmanModel
from patchtst_koopman.models.lstm_koopman_model import LSTMKoopmanModel
from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
from patchtst_koopman.training.performance import apply_gpu_training_defaults
from patchtst_koopman.training.mlp_koopman_trainer import MLPKoopmanTrainer
from patchtst_koopman.training.lstm_koopman_trainer import LSTMKoopmanTrainer

for name in ("platform1.yaml", "platform2.yaml"):
    cfg = yaml.safe_load((CODE / "configs" / name).read_text(encoding="utf-8"))
    before = json.dumps(cfg, sort_keys=True, default=str)

    m_mlp = MLPKoopmanModel(cfg)
    m_lstm = LSTMKoopmanModel(cfg)
    m_main = PatchTSTKoopmanModel(cfg)
    out = apply_gpu_training_defaults(cfg)

    after = json.dumps(cfg, sort_keys=True, default=str)
    print(f"=== {name} ===")
    print(f"  config unchanged after 3 model builds + gpu defaults: {before == after}")
    print(f"  encoder.latent_dim (file)      = {cfg['encoder']['latent_dim']}")
    print(f"  mlp_koopman.latent_dim         = {cfg['mlp_koopman']['latent_dim']}")
    print(f"  lstm_koopman.latent_dim        = {cfg['lstm_koopman']['latent_dim']}")
    print(f"  MLPKoopmanModel.koopman.d      = {m_mlp.koopman.d}  (expect mlp value)")
    print(f"  LSTMKoopmanModel.koopman.d     = {m_lstm.koopman.d}  (expect lstm value)")
    print(f"  PatchTSTKoopmanModel.koopman.d = {m_main.koopman.d}  (expect encoder value)")
    print(f"  apply_gpu_training_defaults returned a copy: {out is not cfg}")
    # trainers must construct too
    MLPKoopmanTrainer(m_mlp, cfg)
    LSTMKoopmanTrainer(m_lstm, cfg)
    print("  MLPKoopmanTrainer + LSTMKoopmanTrainer constructed OK")
    print()
