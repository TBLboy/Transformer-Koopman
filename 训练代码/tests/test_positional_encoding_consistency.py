"""ALN-010 regression guard: one PositionalEncoding, and the deploy copy matches.

The legacy tree had three copies of the sinusoidal positional encoding. Two are
now the shared ``utils.positional_encoding`` module; the deploy copy stays
standalone (it must run without the training package) but must be numerically
identical.
"""
import importlib.util
import re
from pathlib import Path

import pytest
import torch

from conftest import PROJECT_DIR, SRC_DIR

DEPLOY_MODEL = PROJECT_DIR / "deploy" / "algorithms" / "tk_assets" / "transformer_koopman_model.py"


def load_deploy_module():
    spec = importlib.util.spec_from_file_location("deploy_tk_model", DEPLOY_MODEL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_models_and_ablation_share_one_class():
    from patchtst_koopman.utils.positional_encoding import PositionalEncoding as canonical
    from patchtst_koopman.models.patchtst_encoder import PositionalEncoding as from_models
    from patchtst_koopman.ablation.positional_encoding import PositionalEncoding as from_ablation

    assert from_models is canonical, "models/patchtst_encoder.py has its own copy"
    assert from_ablation is canonical, "ablation/positional_encoding.py has its own copy"


def test_only_one_class_definition_in_src():
    definitions = []
    for path in sorted(SRC_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.match(r"\s*class\s+PositionalEncoding\b", line):
                definitions.append(f"{path.relative_to(SRC_DIR)}:{lineno}")
    assert len(definitions) == 1, (
        f"expected exactly one PositionalEncoding definition in src/, found {definitions}"
    )


@pytest.mark.parametrize("d_model", [8, 16, 64])
def test_deploy_copy_matches_canonical(d_model):
    from patchtst_koopman.utils.positional_encoding import PositionalEncoding as canonical

    deploy = load_deploy_module().PositionalEncoding

    torch.manual_seed(0)
    x = torch.randn(2, 12, d_model)

    a = canonical(d_model)
    b = deploy(d_model)

    assert a.pe.shape == b.pe.shape
    assert a.pe.dtype == b.pe.dtype, (
        f"dtype drift: canonical={a.pe.dtype} deploy={b.pe.dtype}"
    )
    torch.testing.assert_close(a.pe, b.pe, rtol=0, atol=0)
    torch.testing.assert_close(a(x), b(x), rtol=0, atol=0)


def test_deploy_copy_matches_under_float64_default():
    """The legacy deploy copy hard-coded float32; it must follow the default dtype."""
    from patchtst_koopman.utils.positional_encoding import PositionalEncoding as canonical

    deploy = load_deploy_module().PositionalEncoding

    previous = torch.get_default_dtype()
    try:
        torch.set_default_dtype(torch.float64)
        a = canonical(16)
        b = deploy(16)
        assert a.pe.dtype == torch.float64
        assert b.pe.dtype == torch.float64, (
            "deploy copy ignored torch.get_default_dtype(); it would diverge from "
            "the training-side encoding under float64 (ALN-010)"
        )
        torch.testing.assert_close(a.pe, b.pe, rtol=0, atol=0)
    finally:
        torch.set_default_dtype(previous)
