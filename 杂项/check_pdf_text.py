"""Check whether given phrases are present in the compiled PDF text.

Usage:
    python check_pdf_text.py "phrase one" "phrase two" ...
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PDF = Path(__file__).resolve().parents[1] / "论文" / "新版本" / "build" / "Main.pdf"

LIGATURES = (("\ufb00", "ff"), ("\ufb01", "fi"), ("\ufb02", "fl"), ("\ufb03", "ffi"), ("\ufb04", "ffl"))


def norm(s: str) -> str:
    s = re.sub(r"\s+", " ", s)
    for a, b in LIGATURES:
        s = s.replace(a, b)
    return s


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: check_pdf_text.py <phrase> [<phrase> ...]")
        return 2

    import fitz

    doc = fitz.open(str(PDF))
    text = norm("\n".join(doc[i].get_text() for i in range(doc.page_count)))
    pages = doc.page_count
    doc.close()

    print(f"PDF: {PDF}")
    print(f"pages: {pages}")
    print()
    low = text.lower()
    for needle in sys.argv[1:]:
        print(f"  [{'FOUND' if norm(needle).lower() in low else 'MISSING'}] {needle!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
