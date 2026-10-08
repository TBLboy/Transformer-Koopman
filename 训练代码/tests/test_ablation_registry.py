"""ALN-013 regression guard: ablation registry, reachable set and docs must agree.

``src/patchtst_koopman/ablation/models.py`` defines ``ABLATION_MODELS``;
``scripts/ablation/train_ablation.py`` exposes a subset of it through
``build_ablation_variants``. A registry entry that is not reachable is dead code
unless it is explicitly pinned below with a reason.
"""
import importlib.util
import re
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_DIR, SRC_DIR

ABLATION_CONFIG = PROJECT_DIR / "scripts" / "ablation" / "ablation_platform2.yaml"

# ``build_ablation_variants`` emits parameterised ids (``patch_L1``) while
# ``ABLATION_MODELS`` keys are templates (``patch_L``); map one onto the other.
TEMPLATE_PATTERNS = [
    (re.compile(r"^patch_L\d+$"), "patch_L"),
    (re.compile(r"^history_P\d+$"), "history_P"),
    (re.compile(r"^n_layers_L\d+$"), "n_layers"),
    (re.compile(r"^latent_dim_d\d+$"), "latent_dim"),
]

# Registry entries that ``build_ablation_variants`` does not expose. They are
# *designed* variants (the legacy docs/ABLATION_DESIGN.md lists ``readout_max``
# as a hyperparameter ablation) that were never wired into the pipeline. Wiring
# them up changes the experiment design, which belongs to 阶段② (DEC-004); until
# then they are pinned here so a *new* unreachable entry fails the suite.
DESIGNED_BUT_UNWIRED = {"readout_max", "readout_last", "pure_feature"}


def load_train_ablation():
    spec = importlib.util.spec_from_file_location(
        "train_ablation_under_test",
        PROJECT_DIR / "scripts" / "ablation" / "train_ablation.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def registry_ids():
    from patchtst_koopman.ablation.models import ABLATION_MODELS
    return set(ABLATION_MODELS)


def reachable_ids():
    module = load_train_ablation()
    config = yaml.safe_load(ABLATION_CONFIG.read_text(encoding="utf-8"))
    return set(module.build_ablation_variants(config))


def registry_template(variant_id):
    """Map a parameterised variant id onto its ``ABLATION_MODELS`` template."""
    for rx, template in TEMPLATE_PATTERNS:
        if rx.match(variant_id):
            return template
    return variant_id


def reachable_templates():
    return {registry_template(v) for v in reachable_ids()}


def test_registry_entries_are_reachable_or_pinned():
    unreachable = registry_ids() - reachable_templates()
    new = sorted(unreachable - DESIGNED_BUT_UNWIRED)
    assert not new, (
        f"ABLATION_MODELS defines {new}, which build_ablation_variants never "
        "exposes. Wire them up or pin them in DESIGNED_BUT_UNWIRED with a reason."
    )


def test_pinned_set_is_still_unreachable():
    """Keep the pin honest: a variant that becomes reachable must be unpinned."""
    stale = sorted(DESIGNED_BUT_UNWIRED - (registry_ids() - reachable_templates()))
    assert not stale, (
        f"DESIGNED_BUT_UNWIRED lists {stale}, which are now reachable (or no "
        "longer in the registry); remove them from the pinned set."
    )


def test_reachable_variants_are_all_registered():
    """Every reachable variant must resolve to a registry entry."""
    unknown = sorted(reachable_templates() - registry_ids())
    assert not unknown, (
        f"build_ablation_variants exposes {unknown}, which ABLATION_MODELS does "
        "not define"
    )


def test_readme_does_not_claim_platform_configs():
    """PLATFORM_CONFIGS lives in the (unmigrated) figures/ tree, not in ablation/."""
    readme = (PROJECT_DIR / "README.md").read_text(encoding="utf-8")
    assert "PLATFORM_CONFIGS" not in readme, (
        "README claims PLATFORM_CONFIGS is under ablation/, but it is defined in "
        "figures/ablation/plot_ablation.py (not migrated); see ALN-013"
    )
