# -*- coding: utf-8 -*-
"""Report artifact hashes, sizes and PDF page count for the paper."""
import hashlib
from pathlib import Path

import fitz

BASE = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本")
TARGETS = [BASE / "Main.tex", BASE / "build" / "Main.pdf"]

for p in TARGETS:
    b = p.read_bytes()
    print("%-14s sha256=%s  bytes=%d" % (p.name, hashlib.sha256(b).hexdigest()[:12].upper(), len(b)))

doc = fitz.open(str(BASE / "build" / "Main.pdf"))
print("pages = %d" % doc.page_count)
doc.close()
