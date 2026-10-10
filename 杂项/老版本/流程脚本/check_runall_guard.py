import importlib.util
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PROJECT = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码")
spec = importlib.util.spec_from_file_location("ra", PROJECT / "scripts" / "run_all.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

print("=== run_all.py pre-flight guard over all scheduled jobs ===")
for j in m.JOBS:
    req = m.REQUIRED_SECTION.get(j["script"])
    miss = m.missing_config_section(PROJECT / "configs" / j["config"], req)
    flag = "SKIP" if miss else "ok"
    print(f"  [{flag}] {j['name']:<24} {j['script']:<26} required={str(req):<28}")

print("\n=== negative control: guard on a config that lacks the section ===")
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "platform2_without_lstm.yaml"
    import yaml
    d = yaml.safe_load((PROJECT / "configs" / "platform2.yaml").read_text(encoding="utf-8"))
    d.pop("lstm_koopman")
    p.write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")
    print("  missing_config_section(no-lstm config, 'lstm_koopman') =",
          m.missing_config_section(p, "lstm_koopman"), "(expected True)")
