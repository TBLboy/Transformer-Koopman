import json

SCHEMA = r"C:\Users\12187\AppData\Local\Temp\opencode\config.schema.json"
s = json.load(open(SCHEMA, encoding="utf-8"))
defs = s["$defs"]

print("Config.additionalProperties =", defs["Config"].get("additionalProperties"))
print()

model = defs["ProviderConfig"]["properties"]["models"]["additionalProperties"]
print("model properties:", ", ".join(sorted(model.get("properties", {}).keys())))
print()
print("limit schema:", json.dumps(model["properties"].get("limit"), ensure_ascii=False))
