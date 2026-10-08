"""YAML config loader/saver."""
import os

import yaml


def load_config(config_path):
    """Load a YAML config into a nested dict."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file does not exist: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config, save_path):
    """Save a config dict to YAML, creating parent directories as needed."""
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
