import subprocess, hashlib
from pathlib import Path
NESTED = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
LEG = Path(r"D:\Project\Transformer-Koopman\.project-log\legacy")
for rel in ["requirements.md","progress.md","business-logic/main.md"]:
    orig = subprocess.run(["git","-C",str(NESTED),"show","HEAD:.project-log/"+rel],capture_output=True,check=True).stdout
    arc = (LEG/rel).read_bytes()
    same_norm = orig.replace(b"\r\n",b"\n") == arc.replace(b"\r\n",b"\n")
    print(f"{rel}: head_crlf={orig.count(bytes([13,10]))} archive_crlf={arc.count(bytes([13,10]))} head_lf={orig.count(bytes([10]))} archive_lf={arc.count(bytes([10]))} equal_after_normalize={same_norm}")
