# -*- coding: utf-8 -*-
"""Final-pass compression of the Related Work section (keep 3 subsections, ~600 words)."""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")
NEW = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\杂项\_new_related5.tex")

START, END = 130, 155  # 1-based, inclusive; Related Work block incl. leading banner

CHECKS = {
    131: r"\section{Related Work}",
    132: r"\label{sec:related_work}",
    151: r"\subsection{Real-Time and Scheduled Predictive Control}",
    158: r"\section{Preliminaries and Problem Formulation}",
}


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    assert "\ufeff" not in text, "unexpected BOM"
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.replace("\r\n", "\n").split("\n")

    for ln, want in CHECKS.items():
        got = lines[ln - 1].strip()
        assert got == want, "anchor mismatch at line %d: %r != %r" % (ln, got, want)

    new = NEW.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n").split("\n")
    print("replace L%d-%d (%d lines) -> %d lines" % (START, END, END - START + 1, len(new)))
    lines[START - 1:END] = new

    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(lines))
    print("OK: wrote %d lines" % len(lines))


if __name__ == "__main__":
    main()
