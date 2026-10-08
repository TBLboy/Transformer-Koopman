"""Shared fixtures for the regression suite.

Paths are derived from this file, so the suite runs from any working directory and
carries no machine-specific absolute path.
"""
import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]  # 训练代码/
REPO_ROOT = PROJECT_DIR.parent                      # Transformer-Koopman/
SRC_DIR = PROJECT_DIR / "src"
CONFIG_DIR = PROJECT_DIR / "configs"
DATA_ROOT = REPO_ROOT / "数据备份"

# Import the package without requiring an install.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(scope="session")
def project_dir():
    return PROJECT_DIR


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


@pytest.fixture(scope="session")
def config_dir():
    return CONFIG_DIR


@pytest.fixture(scope="session")
def data_root():
    return DATA_ROOT


PLATFORMS = {
    "p1": DATA_ROOT / "机械臂数据" / "处理后的数据",
    "p2": DATA_ROOT / "软体平台数据" / "处理后的数据",
}


@pytest.fixture(scope="session")
def processed_dirs():
    return PLATFORMS
