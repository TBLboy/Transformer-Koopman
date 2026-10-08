import re
from collections import defaultdict

LOG = r"C:\Users\12187\AppData\Local\Temp\opencode\fullsuite.log"
lines = open(LOG, encoding="utf-16").read().splitlines()

blocks = []
i = 0
while i < len(lines):
    if re.match(r"^(FAIL|ERROR): ", lines[i]):
        header = lines[i]
        j = i + 1
        while not header.rstrip().endswith(")") and j < len(lines):
            header += lines[j]
            j += 1
        body = [header]
        while j < len(lines) and not re.match(r"^-{20,}$", lines[j]):
            body.append(lines[j])
            j += 1
        blocks.append(body)
        i = j
    else:
        i += 1

print("blocks parsed:", len(blocks))
print()

groups = defaultdict(list)
for body in blocks:
    m = re.match(r"^(FAIL|ERROR): (\S+) \((.+?)\)\s*$", body[0].strip())
    if not m:
        print("UNPARSED:", body[0][:120])
        continue
    kind, test, dotted = m.group(1), m.group(2), m.group(3)
    cls = dotted.split(".")[-2] if dotted.count(".") >= 2 else "?"
    exc = next((l.strip() for l in reversed(body) if l.strip()), "?")
    exc = re.sub(r"\s+", " ", exc)
    frame = next((l.strip() for l in body if re.match(r"^\s+File .*tests", l)), "")
    fm = re.search(r'File "(.+?)", line (\d+)', frame)
    floc = ""
    if fm:
        p = fm.group(1).replace("\\", "/")
        floc = "tests/" + p.split("/tests/")[-1] + ":" + fm.group(2)
    groups[exc].append((kind, cls, test, floc))

for exc, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print(f"### {len(items)}x :: {exc[:150]}")
    for kind, cls, test, floc in items:
        print(f"    [{kind}] {cls}.{test}")
        if floc:
            print(f"          {floc}")
    print()
