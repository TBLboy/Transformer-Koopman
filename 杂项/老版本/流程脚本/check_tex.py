import re, sys, io
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
p = r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex"
s = io.open(p, "r", encoding="utf-8").read()

# environment balance
begins = re.findall(r"\\begin\{([^}]+)\}", s)
ends = re.findall(r"\\end\{([^}]+)\}", s)
from collections import Counter
cb, ce = Counter(begins), Counter(ends)
print("environment mismatch:")
for k in sorted(set(cb) | set(ce)):
    if cb[k] != ce[k]:
        print(f"  {k}: begin={cb[k]} end={ce[k]}")
print("  (none)" if all(cb[k] == ce[k] for k in set(cb) | set(ce)) else "")

# labels vs refs
labels = set(re.findall(r"\\label\{([^}]+)\}", s))
refs = set(re.findall(r"\\ref\{([^}]+)\}", s)) | set(re.findall(r"\\eqref\{([^}]+)\}", s))
print("\ndangling refs (ref with no label):")
d = sorted(refs - labels)
print("  ", d if d else "(none)")
print("\nunused labels:")
u = sorted(labels - refs)
print("  ", u if u else "(none)")

# brace balance
print("\nbrace balance:", s.count("{") - s.count("}"))
print("dollar parity (even expected):", s.count("$") % 2)
