"""Render the PDF page(s) containing a search phrase, for layout inspection.

Usage:
    python render_paper_page.py "practical computation requires" [out_dir]

Renders at 150 dpi and prints the page number, the phrase's bounding box, and
the width of the text block containing it, which makes justified-line defects
(stretched / underfull lines) easy to spot.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parents[1] / "论文" / "新版本"
PDF = PAPER_DIR / "build" / "Main.pdf"
DEFAULT_OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\layout")


def norm(s: str) -> str:
    s = re.sub(r"\s+", " ", s)
    for a, b in (("\ufb00", "ff"), ("\ufb01", "fi"), ("\ufb02", "fl")):
        s = s.replace(a, b)
    return s


def main() -> int:
    needle = norm(sys.argv[1] if len(sys.argv) > 1 else "practical computation requires")
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    out_dir.mkdir(parents=True, exist_ok=True)

    import fitz  # PyMuPDF

    doc = fitz.open(str(PDF))
    print(f"PDF: {PDF}")
    print(f"pages: {doc.page_count}")
    print(f"needle: {needle!r}")
    print()

    found = 0
    for pno in range(doc.page_count):
        page = doc[pno]
        text = norm(page.get_text())
        if needle not in text:
            continue
        found += 1
        # Locate the phrase with the raw (un-normalised) search first, then fall
        # back to a shorter distinctive fragment.
        rects = page.search_for(needle)
        if not rects:
            frag = needle.split()
            for n in range(len(frag), 2, -1):
                rects = page.search_for(" ".join(frag[:n]))
                if rects:
                    break
        print(f"page {pno + 1}: phrase rects = {len(rects)}")
        if rects:
            r = rects[0]
            print(f"   first rect: x0={r.x0:.1f} x1={r.x1:.1f} y0={r.y0:.1f} y1={r.y1:.1f}  width={r.width:.1f}pt")
        # Report the text-block geometry around the phrase.
        for b in page.get_text("blocks"):
            x0, y0, x1, y1, btext = b[0], b[1], b[2], b[3], b[4]
            if needle in norm(btext):
                print(f"   block: x0={x0:.1f} x1={x1:.1f} width={x1 - x0:.1f}pt  lines={len([l for l in btext.splitlines() if l.strip()])}")
                break
        png = out_dir / f"page{pno + 1:02d}.png"
        page.get_pixmap(dpi=150).save(str(png))
        print(f"   wrote {png}")

    if not found:
        print("phrase not found in any page")
        doc.close()
        return 1

    doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
