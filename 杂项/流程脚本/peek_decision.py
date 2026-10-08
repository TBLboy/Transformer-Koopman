import json, sys
p = r"D:\Project\Transformer-Koopman\.project-log\ledger\v1\ledger.jsonl"
lines = [l for l in open(p, encoding="utf-8") if '"action":"record.create"' in l]
for l in lines:
    o = json.loads(l)
    req = o.get("request", {})
    pl = req.get("payload", {})
    if pl.get("kind") == "decision":
        sys.stdout.write(json.dumps(req, ensure_ascii=False, indent=1)[:1600])
        break
