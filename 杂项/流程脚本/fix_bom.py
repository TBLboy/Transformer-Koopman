import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

CODE = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码")
OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman")
BOM = b"\xef\xbb\xbf"
CRLF = b"\r\n"

for name in ("run_all_training.bat", "run_all_training.ps1"):
    new = CODE / name
    old = OLD / name
    raw_new = new.read_bytes()
    raw_old = old.read_bytes()
    print(name + ":")
    print("  old first bytes: " + repr(raw_old[:6]) + "  BOM=" + str(raw_old.startswith(BOM)))
    print("  new first bytes: " + repr(raw_new[:6]) + "  BOM=" + str(raw_new.startswith(BOM)))
    if raw_new.startswith(BOM):
        new.write_bytes(raw_new[3:])
        print("  -> BOM stripped")
    after = new.read_bytes()
    crlf = after.count(CRLF)
    lf = after.count(b"\n") - crlf
    print("  CRLF=" + str(crlf) + "  bare LF=" + str(lf))