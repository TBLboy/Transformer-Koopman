"""Every job the pipeline schedules must be satisfiable.

This is the regression guard for the original defect (clarification ALN-003):
``scripts/run_all.py`` scheduled LSTM-Koopman on platform 2, whose config had no
``lstm_koopman`` section, so the job died with ``KeyError: 'lstm_koopman'`` deep
inside model construction instead of being caught before launch.

The map below states, per training entry point, which config section it requires.
Keeping that mapping explicit means a new job cannot be added without a config
that backs it.
"""
import importlib.util
from pathlib import Path

import pytest
import yaml

from conftest import CONFIG_DIR, PROJECT_DIR

# training script -> dotted path to the config section it reads
REQUIRED_SECTION = {
    "train_patchtst.py": None,                      # uses the shared top-level sections
    "train_mlp_koopman.py": "mlp_koopman",
    "train_lstm_koopman.py": "lstm_koopman",
    "train_traditional_edmd.py": "training.traditional_edmd",
}


def load_run_all():
    spec = importlib.util.spec_from_file_location(
        "run_all_under_test", PROJECT_DIR / "scripts" / "run_all.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUN_ALL = load_run_all()
JOBS = RUN_ALL.JOBS


def lookup(node, dotted):
    cursor = node
    for part in dotted.split("."):
        assert isinstance(cursor, dict) and part in cursor, f"missing '{dotted}'"
        cursor = cursor[part]
    return cursor


@pytest.mark.parametrize("job", JOBS, ids=[j["name"] for j in JOBS])
def test_job_script_exists(job):
    assert (PROJECT_DIR / "scripts" / job["script"]).is_file(), job["script"]


@pytest.mark.parametrize("job", JOBS, ids=[j["name"] for j in JOBS])
def test_job_config_exists(job):
    assert (CONFIG_DIR / job["config"]).is_file(), job["config"]


@pytest.mark.parametrize("job", JOBS, ids=[j["name"] for j in JOBS])
def test_job_config_declares_its_required_section(job):
    required = REQUIRED_SECTION.get(job["script"])
    if required is None:
        pytest.skip(f"{job['script']} has no dedicated config section")
    config = yaml.safe_load((CONFIG_DIR / job["config"]).read_text(encoding="utf-8"))
    try:
        lookup(config, required)
    except AssertionError:
        pytest.fail(
            f"job '{job['name']}' runs {job['script']} against {job['config']}, "
            f"but that config has no '{required}' section (defect ALN-003)"
        )


def test_every_scheduled_script_is_covered_by_the_map():
    unknown = sorted({j["script"] for j in JOBS} - set(REQUIRED_SECTION))
    assert not unknown, (
        f"these scheduled scripts have no declared required section: {unknown}; "
        "add them to REQUIRED_SECTION so the guard stays complete"
    )


def test_runtime_guard_detects_absent_section(tmp_path):
    """The pipeline's own pre-flight check must agree with this suite's map."""
    cfg = tmp_path / "synthetic.yaml"
    cfg.write_text("a:\n  b: 1\n", encoding="utf-8")
    assert RUN_ALL.missing_config_section(cfg, "absent") is True
    assert RUN_ALL.missing_config_section(cfg, "a.absent") is True
    assert RUN_ALL.missing_config_section(cfg, "a.b") is False
    assert RUN_ALL.missing_config_section(cfg, None) is False
    assert RUN_ALL.missing_config_section(tmp_path / "nope.yaml", "a") is True


def test_runtime_guard_passes_for_every_real_job():
    for job in JOBS:
        required = REQUIRED_SECTION.get(job["script"])
        assert RUN_ALL.missing_config_section(
            CONFIG_DIR / job["config"], required
        ) is False, f"{job['name']} would be skipped by the runtime guard"
