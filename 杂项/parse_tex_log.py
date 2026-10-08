"""Parse a LaTeX log and list badness-flagged boxes with the offending text.

LaTeX writes, e.g.:

    Underfull \\hbox (badness 10000) in paragraph at lines 193--194
    []|\\tenrm Since the Koopman operator is gen-erally ...

The line after the warning shows the typeset line that TeX could not justify
well, which identifies the paragraph responsible. This script pairs each
warning with that context line.

Usage:
    python parse_tex_log.py [path/to/Main.log]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_LOG = Path(__file__).resolve().parents[1] / "论文" / "新版本" / "build" / "Main.log"

WARN = re.compile(r"(Underfull|Overfull) \\([hv])box \(([^)]*)\)(.*)")
BADNESS = re.compile(r"badness (\d+)")


def main() -> int:
    log_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LOG
    if not log_path.exists():
        print(f"log not found: {log_path}")
        return 2

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()

    warnings = []
    for i, line in enumerate(lines):
        m = WARN.search(line)
        if not m:
            continue
        kind, box, detail, where = m.group(1), m.group(2), m.group(3), m.group(4).strip()
        bm = BADNESS.search(detail)
        badness = int(bm.group(1)) if bm else None
        # The offending text is on the next non-empty line.
        ctx = ""
        for j in range(i + 1, min(i + 4, len(lines))):
            if lines[j].strip():
                ctx = lines[j].strip()
                break
        warnings.append((badness if badness is not None else -1, kind, box, where, ctx))

    under = [w for w in warnings if w[1] == "Underfull"]
    over = [w for w in warnings if w[1] == "Overfull"]

    print(f"log: {log_path}")
    print(f"Underfull boxes: {len(under)}   Overfull boxes: {len(over)}")
    print()

    print("--- Underfull hboxes (worst first) ---")
    for badness, kind, box, where, ctx in sorted(under, reverse=True):
        print(f"  badness={badness:>5}  hbox  {where}")
        if ctx:
            print(f"      {ctx[:96]}")
    print()

    print("--- Overfull boxes ---")
    for badness, kind, box, where, ctx in sorted(over, reverse=True):
        print(f"  badness={badness:>5}  hbox  {where}")
        if ctx:
            print(f"      {ctx[:96]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
