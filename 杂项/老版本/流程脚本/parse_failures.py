import re
from collections import defaultdict

LOG = r"C:\Users\12187\AppData\Local\Temp\opencode\fullsuite.log"
lines = open(LOG, encoding="utf-8", errors="replace").read().splitlines()

starts = [i for i, l in enumerate(lines) if re.match(r"^(FAIL|ERROR): ", l)]

blocks = []
for n, i in enumerate(starts):
    end = starts[n + 1] if n + 1 < len(starts) else len(lines)
    body = lines[i:end]
    # cut at the separating rule that follows the traceback
    for j, l in enumerate(body):
        if j and (re.match(r"^-{20,}$", l) or re.match(r"^={20,}$", l)):
            body = body[:j]
            break
    blocks.append(body)

print("blocks found:", len(blocks))
print()

groups = defaultdict(list)
for body in blocks:
    header = body[0]
    m = re.match(r"^(FAIL|ERROR): (\S+) \((.+?)\)", header)
    kind, test, dotted = m.group(1), m.group(2), m.group(3)
    # last non-empty line = raised exception
    exc = next((l.strip() for l in reversed(body) if l.strip()), "?")
    # first frame inside tests/
    frame = next((l.strip() for l in body if re.match(r"^\s+File .*tests", l)), "")
    floc = ""
    fm = re.search(r'File "(.+?)", line (\d+)', frame)
    if fm:
        floc = fm.group(1).split("vibe-coding")[-1].lstrip("\\/").replace("\\", "/") + ":" + fm.group(2)
    groups[exc].append((kind, dotted.split(".")[-2] if "." in dotted else "?", test, floc))

for exc, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print(f"### {len(items)}x  {exc}")
    for kind, cls, test, floc in items:
        print(f"    [{kind}] {cls}.{test}")
        if floc:
            print(f"          at {floc}")
    print()
