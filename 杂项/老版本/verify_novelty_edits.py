"""Verify that the novelty-audit edits are present in the compiled PDF.

Checks (text extracted from build/Main.pdf with PyMuPDF):
  1. Section II-C now accurately describes the low-rank Koopman operator of
     Forootani & Iervolino (arXiv:2602.02592).
  2. The new Feizi et al. (RA-L 2025) acknowledgment sentence is present.
  3. Contribution 1 headline is the new wording.
  4. The bibliography entry for Feizi et al. is present.

Usage:  python verify_novelty_edits.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1] / "论文" / "新版本"
PDF = PAPER_DIR / "build" / "Main.pdf"

NEEDLES = {
    "II-C low-rank operator": "single low-rank operator",
    "II-C static-vs-modulated distinction": "full-rank nominal transition",
    "II-C Feizi acknowledgment": "low-rank space-varying transitions",
    "contribution-1 headline": "Low-rank history-conditioned modulation of the lifted transition",
    "bib Feizi author": "Feizi",
    "bib Feizi RA-L venue": "IEEE Robot. Autom. Lett.",
}

FORBIDDEN = {
    "old vague criticism (removed)": "blur the lines between representation learning",
    "old contribution headline (removed)": "Low-rank history-conditioned Koopman modeling",
}


def main() -> int:
    if not PDF.exists():
        print(f"FAIL: PDF not found: {PDF}")
        return 2

    import fitz  # PyMuPDF

    doc = fitz.open(str(PDF))
    text = "\n".join(page.get_text() for page in doc)
    pages = doc.page_count
    doc.close()

    # Normalise whitespace and ligatures so phrases match across line breaks.
    flat = re.sub(r"\s+", " ", text).replace("\ufb00", "ff").replace("\ufb01", "fi")

    print(f"PDF: {PDF}")
    print(f"pages: {pages}")
    print()

    ok = True
    print("required:")
    for label, needle in NEEDLES.items():
        hit = needle in flat
        ok &= hit
        print(f"  [{'PASS' if hit else 'FAIL'}] {label}: {needle!r}")

    print()
    print("must be absent:")
    for label, needle in FORBIDDEN.items():
        gone = needle not in flat
        ok &= gone
        print(f"  [{'PASS' if gone else 'FAIL'}] {label}: {needle!r}")

    print()
    print("VERDICT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
