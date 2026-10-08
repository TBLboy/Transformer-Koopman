# -*- coding: utf-8 -*-
"""Resolve the N collision: N was used both for the patch count (Section IV-A)
and for the MPC prediction horizon (Section VI).  The patch count becomes N_p."""
from pathlib import Path
import re

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")
with open(TEX, "r", encoding="utf-8", newline="") as f:
    text = f.read()
nl = "\r\n" if "\r\n" in text else "\n"

REPL = [
    (r"we partition it into $N = P/p$ contiguous",
     r"we partition it into $N_p = P/p$ contiguous"),
    (r"\mX_k^{(i)} \in \mathbb{R}^{p \times n}, \qquad i=1,\ldots,N.",
     r"\mX_k^{(i)} \in \mathbb{R}^{p \times n}, \qquad i=1,\ldots,N_p."),
    (r"reduces the sequence length from $P$ to $N=P/p$",
     r"reduces the sequence length from $P$ to $N_p=P/p$"),
    (r"\{\tilde{\vphi}_k^{(i)}\}_{i=1}^{N}",
     r"\{\tilde{\vphi}_k^{(i)}\}_{i=1}^{N_p}"),
    (r"\right) \in \mathbb{R}^{N \times d_{\mathrm{model}}},",
     r"\right) \in \mathbb{R}^{N_p \times d_{\mathrm{model}}},"),
    (r"\mH_k \in \mathbb{R}^{N \times d_{\mathrm{model}}}",
     r"\mH_k \in \mathbb{R}^{N_p \times d_{\mathrm{model}}}"),
    (r"\vr_k = \frac{1}{N}\sum_{i=1}^{N} \mH_k^{(i)}",
     r"\vr_k = \frac{1}{N_p}\sum_{i=1}^{N_p} \mH_k^{(i)}"),
]

for old, new in REPL:
    c = text.count(old)
    assert c == 1, "expected 1 occurrence of %r, found %d" % (old, c)
    text = text.replace(old, new)
    print("ok:", old[:60])

with open(TEX, "w", encoding="utf-8", newline="") as f:
    f.write(nl.join(text.replace("\r\n", "\n").split("\n")))

# post-check: no bare N left in the methodology section
lines = text.replace("\r\n", "\n").split("\n")
leftover = []
for i in range(270, 370):
    if i < len(lines) and re.search(r"(?<![A-Za-z\\])N(?![A-Za-z_])", lines[i]):
        leftover.append("L%d: %s" % (i + 1, lines[i].strip()[:120]))
print()
print("leftover bare N in methodology:", len(leftover))
for l in leftover:
    print("   " + l)
