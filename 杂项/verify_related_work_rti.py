"""Verify that the RTI / scheduled-MPC related-work subsection is in the PDF.

Checks (text extracted from build/Main.pdf with PyMuPDF):
  1. The new Section II-C heading is present.
  2. Both lineages (real-time iteration, advanced-step, quasi-LPV/gain scheduling)
     are described.
  3. The positioning sentence about the endogenous scheduling trajectory is present.
  4. All six new bibliography entries appear in the reference list.

Usage:  python verify_related_work_rti.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1] / "论文" / "新版本"
PDF = PAPER_DIR / "build" / "Main.pdf"

NEEDLES = {
    "II-C heading": "Real-Time and Scheduled Predictive Control",
    "RTI lineage": "real-time iteration",
    "advanced-step lineage": "advanced-step NMPC",
    "gain-scheduling lineage": "gain scheduling",
    "quasi-LPV lineage": "quasi-linear parameter-varying",
    "positioning sentence": "endogenous to the learned model",
    "bib Diehl stability": "Nominal stability of real-time iteration scheme",
    "bib Zavala advanced step": "advanced-step NMPC controller",
    "bib Rugh gain scheduling": "Research on gain scheduling",
    "bib Leith velocity": "velocity-based linearization families",
    "bib Cisneros qLMPC": "quasi-LPV representation",
    "bib Cisneros qLPV": "quasi-linear parameter varying form",
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

    flat = re.sub(r"\s+", " ", text)
    for src, dst in (("\ufb00", "ff"), ("\ufb01", "fi"), ("\ufb02", "fl")):
        flat = flat.replace(src, dst)

    print(f"PDF: {PDF}")
    print(f"pages: {pages}")
    print()

    ok = True
    for label, needle in NEEDLES.items():
        hit = needle in flat
        ok &= hit
        print(f"  [{'PASS' if hit else 'FAIL'}] {label}: {needle!r}")

    print()
    print("VERDICT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
