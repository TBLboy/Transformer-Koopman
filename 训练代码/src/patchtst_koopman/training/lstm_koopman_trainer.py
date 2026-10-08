"""
LSTM-Koopman 训练器

继承自 MLPKoopmanTrainer，只需修改配置键名从 'mlp_koopman' 到 'lstm_koopman'。
支持两种训练方式，由 config['lstm_koopman']['training_method'] 控制：
  - "edmd"       : 预训练编码器 → EDMD 闭式解求 A、B
  - "end_to_end" : 编码器 + A + B 全程梯度下降
"""

from .mlp_koopman_trainer import MLPKoopmanTrainer


class LSTMKoopmanTrainer(MLPKoopmanTrainer):
    """LSTM-Koopman trainer that reuses MLP-Koopman training logic."""

    def __init__(self, model, config):
        # Initialize parent but override the config key
        self.model = model
        self.config = config
        self.device = config['experiment']['device']
        # Use lstm_koopman config section instead of mlp_koopman
        self.mlp_cfg = config['lstm_koopman']  # reuse parent's self.mlp_cfg variable name
