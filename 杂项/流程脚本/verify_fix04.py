import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\edmddl2\python.exe"
CODE = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码")


def run(args, label):
    r = subprocess.run(args, cwd=str(CODE), capture_output=True)
    out = (r.stdout + r.stderr).decode("utf-8", "replace").strip()
    print(f"--- {label}  (rc={r.returncode})")
    for line in out.splitlines()[:12]:
        print("    " + line)
    print()
    return r.returncode, out


print("=== 1. inspect_ckpt.py --help ===")
run([PY, "scripts/inspect_ckpt.py", "--help"], "argparse")

print("=== 2. inspect_ckpt.py on a synthetic checkpoint ===")
import torch
with tempfile.TemporaryDirectory() as tmp:
    ckpt = {
        "config": {"encoder": {"history_length": 32, "patch_length": 8, "latent_dim": 64},
                   "data": {"state_dim": 6, "control_dim": 3}},
        "normalization": {"x_mean": [0.0] * 6},
    }
    p = Path(tmp) / "model_synthetic.pth"
    torch.save(ckpt, p)
    run([PY, "scripts/inspect_ckpt.py", "--checkpoint", str(p)], "happy path")

print("=== 3. inspect_ckpt.py on a missing checkpoint (must fail cleanly) ===")
run([PY, "scripts/inspect_ckpt.py", "--checkpoint", "results/models/nope.pth"], "missing file")

print("=== 4. check_model_prediction.py --help ===")
run([PY, "scripts/check_model_prediction.py", "--help"], "argparse")

print("=== 5. check_model_prediction.py without --checkpoint (must fail cleanly) ===")
run([PY, "scripts/check_model_prediction.py"], "missing required arg")

print("=== 6. run_all_training.ps1 parse check ===")
ps = (
    "$e=$null;$t=$null;"
    "[System.Management.Automation.Language.Parser]::ParseFile("
    f"'{CODE / 'run_all_training.ps1'}',[ref]$t,[ref]$e)|Out-Null;"
    "if($e.Count -eq 0){'PARSE OK'}else{$e|ForEach-Object{$_.Message}}"
)
r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)
print("    " + (r.stdout + r.stderr).decode("utf-8", "replace").strip())
print()

print("=== 7. run_all_training.ps1 default ProjectDir resolves to the script dir ===")
ps2 = (
    f"$s=Get-Content -Raw '{CODE / 'run_all_training.ps1'}';"
    "$ProjectDir='';"
    f"if(-not $ProjectDir){{$ProjectDir='{CODE}'}};"
    "Write-Output ('ProjectDir=' + $ProjectDir);"
    "Write-Output ('PythonExe default=' + 'python')"
)
r = subprocess.run(["powershell", "-NoProfile", "-Command", ps2], capture_output=True)
print("    " + (r.stdout + r.stderr).decode("utf-8", "replace").strip())
print()

print("=== 8. .bat PROJECT derivation (%~dp0 minus trailing backslash) ===")
bat = (CODE / "run_all_training.bat").read_text(encoding="utf-8", errors="replace")
for line in bat.splitlines():
    if "PROJECT" in line or "PYTHON_EXE" in line:
        print("    " + line.strip())
