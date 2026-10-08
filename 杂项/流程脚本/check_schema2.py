import json

SCHEMA = r"C:\Users\12187\AppData\Local\Temp\opencode\config.schema.json"
schema = json.load(open(SCHEMA, encoding="utf-8"))

print("=== root schema keys ===")
print(list(schema.keys()))
print()
print("=== root (first 600 chars) ===")
print(json.dumps(schema, ensure_ascii=False)[:600])
print()

defs = schema.get("definitions") or schema.get("$defs") or {}

cfg = defs.get("Config", {})
print("=== Config definition: keys ===")
print(list(cfg.keys()))
print()
print("=== Config.properties keys ===")
print(", ".join(sorted((cfg.get("properties") or {}).keys())))
print()

for name in ("McpLocalConfig", "McpRemoteConfig", "ProviderConfig"):
    d = defs.get(name, {})
    print(f"=== {name} ===")
    print("  required:", d.get("required"))
    props = d.get("properties") or {}
    print("  properties:", ", ".join(sorted(props.keys())))
    ap = d.get("additionalProperties")
    print("  additionalProperties:", ap if not isinstance(ap, dict) else "{...}")
    print()

print("=== ProviderConfig full ===")
print(json.dumps(defs.get("ProviderConfig", {}), ensure_ascii=False)[:2500])
print()
print("=== McpLocalConfig full ===")
print(json.dumps(defs.get("McpLocalConfig", {}), ensure_ascii=False)[:2500])
