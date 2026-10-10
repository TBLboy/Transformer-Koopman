import re, io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
p = r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex"
s = io.open(p, "r", encoding="utf-8").read()

# split preamble (before \begin{document}) and body
i = s.find(r"\begin{document}")
preamble, body = s[:i], s[i:]

defined = set(re.findall(r"\\newcommand\{\\([A-Za-z@]+)\}", preamble))
defined |= set(re.findall(r"\\def\\([A-Za-z@]+)", preamble))
defined |= set(re.findall(r"\\DeclareMathOperator\{\\([A-Za-z@]+)\}", preamble))
print("defined custom macros:", sorted(defined))

# candidate custom macros used in body: start with \v or \m followed by letters
used = set(re.findall(r"\\(v[A-Za-z]+|m[A-Za-z]+)\b", body))
missing = sorted(u for u in used if u not in defined)
print("\nused \\v*/\\m* macros not defined in preamble:")
for u in missing:
    n = len(re.findall(r"\\" + re.escape(u) + r"\b", body))
    print(f"  \\{u}  (used {n}x)")
