import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")


def ascii_only(value: str) -> str:
    return re.sub(r"[^\x20-\x7e]", ".", value)


LOG = r"C:\Users\12187\AppData\Local\Temp\opencode\fullsuite.log"
lines = open(LOG, encoding="utf-16").read().splitlines()

blocks = []
i = 0
while i < len(lines):
    if re.match(r"^(FAIL|ERROR): ", lines[i]):
        header, j = lines[i], i + 1
        while not header.rstrip().endswith(")") and j < len(lines):
            header += lines[j]; j += 1
        while j < len(lines) and re.match(r"^-{20,}$", lines[j]):
            j += 1
        body = []
        while j < len(lines) and not re.match(r"^={20,}$", lines[j]):
            body.append(lines[j]); j += 1
        blocks.append((header.strip(), body)); i = j
    else:
        i += 1

EXC = re.compile(r"^[A-Za-z_][\w.]*(Error|Exception|Exit|Failure|Interrupt)\b")

out = []
for header, body in blocks:
    m = re.match(r"^(FAIL|ERROR): (\S+) \((.+?)\)(?:\s*\((.*)\))?$", header)
    kind, test, dotted = m.group(1), m.group(2), m.group(3)
    subtest = m.group(4) or ""
    idx = next((k for k in range(len(body) - 1, -1, -1) if EXC.match(body[k].strip())), None)
    if idx is None:
        exc = " ".join(l.strip() for l in body if l.strip())[-300:]
    else:
        exc = " ".join(l.strip() for l in body[idx:] if l.strip())
    exc = re.sub(r"\s+", " ", exc)
    last = next((l.strip() for l in reversed(body) if re.match(r"^\s+File .*tests", l)), "")
    fm = re.search(r'File "(.+?)", line (\d+)', last)
    floc = ""
    if fm:
        p = fm.group(1).replace("\\", "/")
        floc = "tests/" + p.split("/tests/")[-1] + ":" + fm.group(2)
    out.append((kind, dotted.split(".")[-2], test, subtest, floc, exc))

out.sort(key=lambda r: (r[0], r[2], r[3]))
for kind, cls, test, sub, floc, exc in out:
    print(f"[{kind}] {cls}.{test}" + (f" [sub={sub}]" if sub else ""))
    print(f"   loc: {floc}")
    print(f"   exc: {exc[:400]}")
    print()
