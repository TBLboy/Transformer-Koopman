# -*- coding: utf-8 -*-
"""Apply front-matter compression edits (Main(6) editorial review) to Main.tex.

Replaces three line ranges with content read from 杂项/_new_*.tex.
Ranges are applied bottom-up so that earlier 1-based indices stay valid.
Original line endings (LF or CRLF) are preserved.
"""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")
BASE = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\杂项")

# (start_line, end_line_inclusive, replacement_file)
EDITS = [
    (134, 169, BASE / "_new_related.tex"),   # Related Work block + leading banner
    (109, 133, BASE / "_new_intro.tex"),     # Introduction block + trailing blanks
    (101, 103, BASE / "_new_abstract.tex"),  # Abstract body
]

CHECKS = {
    101: r"\begin{abstract}",
    103: r"\end{abstract}",
    109: r"% =========================================================",
    110: r"\section{Introduction}",
    135: r"\section{Related Work}",
    136: r"\label{sec:related_work}",
    172: r"\section{Preliminaries and Problem Formulation}",
}


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    assert "\ufeff" not in text, "unexpected BOM"

    crlf = "\r\n" in text
    nl = "\r\n" if crlf else "\n"
    print("line_ending = %s" % ("CRLF" if crlf else "LF"))

    lines = text.replace("\r\n", "\n").split("\n")
    for ln, want in CHECKS.items():
        got = lines[ln - 1].strip()
        assert got == want, "anchor mismatch at line %d: %r != %r" % (ln, got, want)

    for start, end, path in EDITS:
        raw = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        new = raw.rstrip("\n").split("\n")
        print("replace L%d-%d (%d lines) -> %d lines  [%s]"
              % (start, end, end - start + 1, len(new), path.name))
        lines[start - 1:end] = new

    out = nl.join(lines)
    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print("OK: wrote %d lines" % len(lines))


if __name__ == "__main__":
    main()
