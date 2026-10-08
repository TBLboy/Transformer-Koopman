import subprocess, json
from pathlib import Path
NESTED = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman")
LEG = Path(r"D:\Project\Transformer-Koopman\.project-log\legacy")
rels = subprocess.run(["git","-C",str(NESTED),"ls-files",".project-log"],capture_output=True,text=True,check=True).stdout.split()
bad = []
for rel in rels:
    pres = subprocess.run(["git","-C",str(NESTED),"show","HEAD:"+rel],capture_output=True,check=True).stdout
    arc = (LEG/rel[len(".project-log/"):]).read_bytes()
    if pres.replace(b"\r\n",b"\n") != arc.replace(b"\r\n",b"\n"):
        bad.append(rel)
print(json.dumps({"count":len(rels),"all_equal_after_eol_normalize":not bad,"mismatches":bad}))
