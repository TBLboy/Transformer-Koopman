import json, sys
p = r"D:\Project\Transformer-Koopman\.project-log\ledger\v1\ledger.jsonl"
lines = [l for l in open(p, encoding="utf-8") if '"action":"evidence.record"' in l]
o = json.loads(lines[0])
print("KEYS:", list(o.keys()))
for k, v in o.items():
    if k not in ("receipt",):
        continue
    print("RECEIPT KEYS:", list(v.keys()) if isinstance(v, dict) else type(v))
sys.stdout.write(json.dumps(o, ensure_ascii=False, indent=1)[:3000])
