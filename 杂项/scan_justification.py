"""Scan the compiled paper for loose (over-stretched) justified lines.

A justified line whose mean inter-word gap is much larger than the font's
natural space width is a typographic defect ("loose line" / underfull hbox).
This script reports every line above a gap threshold, with page, block/line
index, gap, width and the line text, plus a summary count.

Usage:
    python scan_justification.py [gap_threshold_pt]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PAPER_DIR = Path(__file__).resolve().parents[1] / "论文" / "新版本"
PDF = PAPER_DIR / "build" / "Main.pdf"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\layout")

LIGATURES = (("\ufb00", "ff"), ("\ufb01", "fi"), ("\ufb02", "fl"), ("\ufb03", "ffi"), ("\ufb04", "ffl"))
# A line is only "loose" if it is close to a full column width; short lines are
# paragraph-ending lines and are legitimately unstretched.
MIN_WIDTH_FRACTION = 0.85


def clean(s: str) -> str:
    for a, b in LIGATURES:
        s = s.replace(a, b)
    return s


def main() -> int:
    import fitz

    threshold = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
    doc = fitz.open(str(PDF))
    OUT.mkdir(parents=True, exist_ok=True)

    # Column width = the modal maximum line width across the document.
    widths = []
    per_page = []
    for pno in range(doc.page_count):
        page = doc[pno]
        groups: dict[tuple[int, int], list] = {}
        for w in page.get_text("words"):
            groups.setdefault((w[5], w[6]), []).append(w)
        per_page.append((pno, groups))
        for ws in groups.values():
            ws = sorted(ws, key=lambda w: w[0])
            if len(ws) >= 2:
                widths.append(ws[-1][2] - ws[0][0])
    if not widths:
        print("no text found")
        return 1
    widths.sort()
    column = widths[int(len(widths) * 0.97)]
    print(f"PDF: {PDF}")
    print(f"pages: {doc.page_count}")
    print(f"estimated full column width: {column:.1f}pt")
    print(f"loose-line threshold: mean_gap > {threshold:.2f}pt")
    print()

    hits = []
    total_lines = 0
    for pno, groups in per_page:
        for key, ws in groups.items():
            ws = sorted(ws, key=lambda w: w[0])
            if len(ws) < 3:
                continue
            width = ws[-1][2] - ws[0][0]
            if width < MIN_WIDTH_FRACTION * column:
                continue
            total_lines += 1
            gaps = [ws[j + 1][0] - ws[j][2] for j in range(len(ws) - 1)]
            gap = sum(gaps) / len(gaps)
            if gap > threshold:
                hits.append((gap, pno + 1, key, len(ws), width, clean(" ".join(w[4] for w in ws))))

    hits.sort(reverse=True)
    print(f"full-width lines examined: {total_lines}")
    print(f"loose lines found: {len(hits)}")
    print()
    for gap, page, key, nwords, width, text in hits[:30]:
        print(f"  p{page} block{key[0]} line{key[1]}  gap={gap:5.2f}pt  width={width:6.1f}pt  words={nwords}")
        print(f"      {text[:76]}")

    doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
