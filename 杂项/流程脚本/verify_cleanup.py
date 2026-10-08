import json
import sys

CFG = r"C:\Users\12187\.config\opencode\opencode.json"
BAK = r"C:\Users\12187\.config\opencode\backups\opencode.json.bak-20260928-113716"
SCHEMA = r"C:\Users\12187\AppData\Local\Temp\opencode\config.schema.json"

text = open(CFG, encoding="utf-8").read()
print("bytes:", len(text.encode("utf-8")))
print("CR count:", text.count("\r"))
print("enabled-true occurrences:", text.count('"enabled": true'))

cfg = json.loads(text)
print("JSON: VALID")
print("mcp servers:", len(cfg["mcp"]), "->", ", ".join(cfg["mcp"].keys()))
for name, entry in cfg["mcp"].items():
    assert "enabled" not in entry, f"{name} still has enabled"
    assert entry["type"] in ("local", "remote"), name
print("all mcp entries: 'enabled' removed, type intact")

schema = json.load(open(SCHEMA, encoding="utf-8"))
try:
    import jsonschema
except ImportError:
    print("jsonschema not installed; skipping")
else:
    v = jsonschema.Draft202012Validator(schema)
    errs = sorted(v.iter_errors(cfg), key=lambda e: list(e.path))
    print("schema errors:", len(errs))
    for e in errs[:20]:
        print("  ", "/".join(str(p) for p in e.path), "::", e.message[:160])

old = open(BAK, encoding="utf-8").read().splitlines()
new = text.splitlines()
print()
print("lines before/after:", len(old), "/", len(new))
removed = [l for l in old if l.strip() == '"enabled": true,']
print("lines that were 'enabled: true':", len(removed))
diff = [l for l in old if l not in new]
added = [l for l in new if l not in old]
print("removed lines:", len(diff), "->", set(x.strip() for x in diff))
print("added lines:", len(added), "->", set(x.strip() for x in added) or "none")
