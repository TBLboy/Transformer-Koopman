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
        while j < len(lines) and re.match(r"^-{20,}$", lines[j]):   # skip separator
            j += 1
        body = []
        while j < len(lines) and not re.match(r"^={20,}$", lines[j]):
            body.append(lines[j])
            j += 1
        blocks.append((header.strip(), body))
        i = j
    else:
        i += 1

print("blocks parsed:", len(blocks))
print()

groups = defaultdict(list)
for header, body in blocks:
    m = re.match(r"^(FAIL|ERROR): (\S+) \((.+?)\)(?:\s*\((.*)\))?$", header)
    kind, test, dotted = m.group(1), m.group(2), m.group(3)
    subtest = m.group(4) or ""
    cls = dotted.split(".")[-2] if dotted.count(".") >= 2 else "?"
    exc = next((re.sub(r"\s+", " ", l.strip()) for l in reversed(body) if l.strip()), "?")
    frames = [l.strip() for l in body if re.match(r"^\s+File .*tests", l)]
    floc = ""
    if frames:
        fm = re.search(r'File "(.+?)", line (\d+)', frames[-1])
        p = fm.group(1).replace("\\", "/")
        floc = "tests/" + p.split("/tests/")[-1] + ":" + fm.group(2)
    groups[(kind, exc, floc)].append((cls, test, subtest))

for (kind, exc, floc), items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print(f"### {len(items)}x [{kind}] {exc[:190]}")
    if floc:
        print(f"        at {floc}")
    for cls, test, sub in items:
        print(f"        - {cls}.{test}" + (f"  subtest={sub}" if sub else ""))
    print()
