import re, io, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
p = r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex"
s = io.open(p, "r", encoding="utf-8").read()

# citation keys used
keys = set()
for m in re.finditer(r"\\cite\{([^}]+)\}", s):
    for k in m.group(1).split(","):
        keys.add(k.strip())
# bibitem keys defined
bib = set(re.findall(r"\\bibitem\{([^}]+)\}", s))
print("cite keys used:", len(keys), "| bibitems:", len(bib))
missing = sorted(keys - bib)
unused = sorted(bib - keys)
print("MISSING bibitem for cite:", missing if missing else "(none)")
print("unused bibitem:", unused if unused else "(none)")

# environment balance
begins = re.findall(r"\\begin\{([^}]+)\}", s)
ends = re.findall(r"\\end\{([^}]+)\}", s)
cb, ce = Counter(begins), Counter(ends)
bad = [k for k in set(cb) | set(ce) if cb[k] != ce[k]]
print("env mismatch:", bad if bad else "(none)")

labels = set(re.findall(r"\\label\{([^}]+)\}", s))
refs = set(re.findall(r"\\ref\{([^}]+)\}", s)) | set(re.findall(r"\\eqref\{([^}]+)\}", s))
print("dangling refs:", sorted(refs - labels) or "(none)")
print("brace balance:", s.count("{") - s.count("}"), "| dollar parity:", s.count("$") % 2)
print("proof blocks:", s.count(r"\begin{proof}"), "/", s.count(r"\end{proof}"))
