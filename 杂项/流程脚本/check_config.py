import json
import sys

SCHEMA = r"C:\Users\12187\AppData\Local\Temp\opencode\config.schema.json"
CONFIG = r"C:\Users\12187\.config\opencode\opencode.json"

schema = json.load(open(SCHEMA, encoding="utf-8"))
config = json.load(open(CONFIG, encoding="utf-8"))

props = schema.get("properties", {})
print("=== top-level allowed keys ===")
print(", ".join(sorted(props.keys())))
print()

print("=== config keys ===")
print(", ".join(sorted(config.keys())))
print()

unknown = [k for k in config if k not in props]
print("=== config keys NOT in schema (would be rejected) ===")
print(unknown or "none")
print()

defs = schema.get("definitions") or schema.get("$defs") or {}

print("=== mcp schema ===")
print(json.dumps(props.get("mcp"), ensure_ascii=False)[:1500])
print()

print("=== provider schema ===")
print(json.dumps(props.get("provider"), ensure_ascii=False)[:1800])
print()

print("=== schema definitions available ===")
print(", ".join(sorted(defs.keys()))[:1500])
print()

try:
    import jsonschema
except ImportError:
    print("jsonschema NOT installed -> skipping strict validation")
else:
    v = jsonschema.Draft7Validator(schema)
    errors = sorted(v.iter_errors(config), key=lambda e: list(e.path))
    print(f"=== strict validation: {len(errors)} error(s) ===")
    for e in errors[:40]:
        print(f"  path={'/'.join(str(p) for p in e.path)} :: {e.message[:200]}")
