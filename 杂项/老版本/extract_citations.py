# -*- coding: utf-8 -*-
"""Extract bibliography entries and per-key citation contexts from Main.tex."""
import json
import re
from pathlib import Path

BASE = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本")
TEX = BASE / "Main.tex"

text = TEX.read_text(encoding="utf-8")

# ---- bibliography entries -------------------------------------------------
start = text.index(r"\begin{thebibliography}")
bib = text[start:]
chunks = re.split(r"\\bibitem(?:\[[^\]]*\])?\{", bib)[1:]
entries = {}
order = []
for ch in chunks:
    key = ch[: ch.index("}")]
    body = ch[ch.index("}") + 1:]
    body = body.split(r"\end{thebibliography}")[0]
    body = body.split(r"\bibitem")[0]
    entries[key] = " ".join(body.split())
    order.append(key)

# ---- citation usage ------------------------------------------------------
plain = re.sub(r"\s+", " ", text)
sentences = re.split(r"(?<=[.!?])\s+", plain)
usage = {}
for idx, s in enumerate(sentences):
    for m in re.finditer(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])?\{([^}]*)\}", s):
        for k in [x.strip() for x in m.group(1).split(",") if x.strip()]:
            usage.setdefault(k, []).append((idx, s))

(BASE.parent.parent / "杂项" / "_audit_bib.json").write_text(
    json.dumps({"order": order, "entries": entries}, ensure_ascii=False, indent=1),
    encoding="utf-8",
)

lines = []
lines.append("bibitem count = %d" % len(order))
lines.append("distinct cited keys = %d" % len(usage))
uncited = [k for k in order if k not in usage]
lines.append("bibitems never cited (%d): %s" % (len(uncited), ", ".join(uncited)))
lines.append("cited keys with no bibitem: %s"
             % ", ".join(sorted(k for k in usage if k not in entries)))
lines.append("")
for k in order:
    lines.append("=" * 78)
    lines.append("[%s]" % k)
    lines.append("BIB: " + entries.get(k, "<MISSING>"))
    if k in usage:
        for idx, s in usage[k]:
            lines.append("  CTX(%d): %s" % (idx, s))
    else:
        lines.append("  CTX: <never cited>")

out = BASE.parent.parent / "杂项" / "_audit_usage.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print("wrote %s (%d chars)" % (out.name, out.stat().st_size))
print("bibitems=%d cited=%d uncited=%d" % (len(order), len(usage), len(uncited)))
