"""Measure justification quality of a paragraph and render a high-DPI crop.

For each line of the target paragraph, report the word count, line width and
mean inter-word gap in points. A normal justified line at 10pt has gaps close
to the font space width (~2.8pt); heavily stretched ("loose") lines show much
larger gaps.

Usage:
    python inspect_justification.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PAPER_DIR = Path(__file__).resolve().parents[1] / "论文" / "新版本"
PDF = PAPER_DIR / "build" / "Main.pdf"
OUT = Path(r"C:\Users\12187\AppData\Local\Temp\opencode\layout")

TARGET = "Since the Koopman operator is generally"
NEIGHBOUR = "The lifted dynamics are then approximated"

LIGATURES = (("\ufb00", "ff"), ("\ufb01", "fi"), ("\ufb02", "fl"), ("\ufb03", "ffi"), ("\ufb04", "ffl"))


def clean(s: str) -> str:
    for a, b in LIGATURES:
        s = s.replace(a, b)
    return s


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", clean(s))


def paragraphs(page):
    """Yield (block, line) groups of words, in reading order."""
    words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,wordno
    groups: dict[tuple[int, int], list] = {}
    for w in words:
        groups.setdefault((w[5], w[6]), []).append(w)
    return groups


def report(page, needle: str, max_lines: int = 6):
    needle = norm(needle)
    groups = paragraphs(page)
    # Find the (block, line) whose text contains the first words of the needle.
    start_key = None
    for key in sorted(groups):
        text = norm(" ".join(w[4] for w in sorted(groups[key], key=lambda w: w[0])))
        if needle.split(" ", 2)[0:3] == text.split(" ", 2)[0:3]:
            start_key = key
            break
    if start_key is None:
        return None

    keys = sorted(groups)
    i = keys.index(start_key)
    out = []
    for key in keys[i:i + max_lines]:
        ws = sorted(groups[key], key=lambda w: w[0])
        if len(ws) < 2:
            continue
        gaps = [ws[j + 1][0] - ws[j][2] for j in range(len(ws) - 1)]
        width = ws[-1][2] - ws[0][0]
        out.append((len(ws), width, sum(gaps) / len(gaps), clean(" ".join(w[4] for w in ws))))
    return out


def main() -> int:
    import fitz

    doc = fitz.open(str(PDF))
    OUT.mkdir(parents=True, exist_ok=True)

    page, pno = None, None
    for i in range(doc.page_count):
        if norm(TARGET) in norm(doc[i].get_text()):
            page, pno = doc[i], i
            break
    if page is None:
        print("target paragraph not found")
        return 1

    for label, needle in (("TARGET (defective?)", TARGET), ("NEIGHBOUR (reference)", NEIGHBOUR)):
        print(f"--- {label} ---")
        stats = report(page, needle)
        if not stats:
            print("  not found\n")
            continue
        for nwords, width, gap, text in stats:
            flag = "   <-- LOOSE" if gap > 4.0 else ""
            print(f"  words={nwords:2d} width={width:6.1f}pt mean_gap={gap:5.2f}pt{flag}")
            print(f"      {text[:76]}")
        print()

    rects = page.search_for("Since the Koopman operator")
    if rects:
        r = rects[0]
        clip = fitz.Rect(40, r.y0 - 5, 312, r.y0 + 66)
        png = OUT / f"crop_p{pno + 1}.png"
        page.get_pixmap(dpi=400, clip=clip).save(str(png))
        print(f"crop written: {png}")

    doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
