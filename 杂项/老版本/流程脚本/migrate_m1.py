import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
OLD = Path(r"D:\Project\论文3老版本\Transformer-Koopman")
NEWREPO = Path(ROOT) / "Transformer-Koopman"
CODE = NEWREPO / "训练代码"


def revision():
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def apply(action, payload, tag, label):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(),
           "action": action, "payload": payload}
    p = f"{TMP}/env_{tag}.json"
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(env, ensure_ascii=False, indent=2))
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", p], capture_output=True)
    ok = r.returncode == 0
    note = "" if ok else " -> " + r.stderr.decode("utf-8", "replace").strip()[:200]
    print(f"  {'OK  ' if ok else 'FAIL'} {label}{note}")


print("== DEC-009: project interpreter / environment ==")
apply("record.create", {
    "kind": "decision", "id": "DEC-009",
    "title": "项目解释器与运行环境确定为 conda env edmddl2", "status": "active",
    "payload": {
        "authority": "B",
        "decision": "本项目代码统一使用 D:\\conda\\envs\\edmddl2\\python.exe 运行；vibe-coding 环境仅用于 Vibe 控制层，不安装项目依赖。",
        "evidence": "edmddl2 = python 3.9.25 + numpy 1.26.3 + scipy 1.13.1 + torch 2.6.0+cu124（CUDA 可用，NVIDIA GeForce RTX 4060 Laptop）+ pyyaml 6.0.2 + matplotlib 3.9.4 + scikit-learn 1.6.1；与老配置注释中的 RTX 4060 一致。无名为 koopman 的环境。",
        "other_candidates_rejected": "project 环境 torch 2.8.0+cpu（无 CUDA）；FlexibleArm 缺 numpy/scipy/torch；matpython 缺 torch。",
        "rationale": "避免在错误环境中运行训练而误判为代码缺陷（failure attribution: environment）。",
        "note": "老仓库 pyproject 声明 requires-python >=3.8，edmddl2 的 3.9.25 满足。"}},
    "t11-dec9", "decision DEC-009")

print("\n== migrate code: platform1 M1 set (exclude ablation/) ==")
copied = []
src_pkg = OLD / "src" / "patchtst_koopman"
dst_pkg = CODE / "src" / "patchtst_koopman"
for p in sorted(src_pkg.rglob("*.py")):
    rel = p.relative_to(src_pkg)
    if rel.parts and rel.parts[0] == "ablation":
        continue
    if "__pycache__" in rel.parts:
        continue
    dst = dst_pkg / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dst)
    copied.append(rel.as_posix())

shutil.copy2(OLD / "configs" / "platform1.yaml", (CODE / "configs" / "platform1.yaml") if (CODE / "configs").mkdir(parents=True, exist_ok=True) is None else None)
shutil.copy2(OLD / "requirements.txt", CODE / "requirements.txt")
shutil.copy2(OLD / ".gitignore", NEWREPO / ".gitignore")
print(f"  copied {len(copied)} .py modules + platform1.yaml + requirements.txt + .gitignore")

print("\n== byte-identity verification (sha256 src vs dst) ==")
mismatch = []
for rel in copied:
    a = hashlib.sha256((src_pkg / rel).read_bytes()).hexdigest()
    b = hashlib.sha256((dst_pkg / rel).read_bytes()).hexdigest()
    if a != b:
        mismatch.append(rel)
print(f"  checked {len(copied)}  mismatches: {mismatch if mismatch else 'NONE'}")
for name, s, d in (("configs/platform1.yaml", OLD / "configs/platform1.yaml", CODE / "configs/platform1.yaml"),
                   ("requirements.txt", OLD / "requirements.txt", CODE / "requirements.txt"),
                   (".gitignore", OLD / ".gitignore", NEWREPO / ".gitignore")):
    same = hashlib.sha256(s.read_bytes()).hexdigest() == hashlib.sha256(d.read_bytes()).hexdigest()
    print(f"  {name:<24} identical={same}")

print("\n== pyproject.toml (adapted for 训练代码/ layout) ==")
pp = CODE / "pyproject.toml"
pp.write_text('''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "patchtst-koopman"
version = "0.1.0"
description = "PatchTST-Koopman: noise-robust nonlinear system modeling and control"
requires-python = ">=3.8"
license = {text = "Research-internal"}
authors = [
    {name = "Paper 4 Author"},
]
dependencies = [
    "torch>=2.0.0",
    "numpy>=1.24.0",
    "scipy>=1.10.0",
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
    "pyyaml>=6.0",
    "tqdm>=4.65.0",
    "scikit-learn>=1.2.0",
]

[project.optional-dependencies]
deploy = ["control", "PyQt6"]
test = ["pytest>=7.0"]

[project.scripts]
inspect-npz = "patchtst_koopman.utils.npz_inspector:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
''', encoding="utf-8", newline="\n")
print("  written; changed vs old: dropped readme=README.md (no README in 训练代码/), added test extra + pytest config")

print("\n== import smoke (edmddl2, from 训练代码/) ==")
r = subprocess.run([r"D:\conda\envs\edmddl2\python.exe", "-c",
                    "import sys; sys.path.insert(0,'src');"
                    "from patchtst_koopman.models.full_model import PatchTSTKoopmanModel;"
                    "from patchtst_koopman.training.edmd_trainer import EDMDTrainer;"
                    "from patchtst_koopman.data.dataset import KoopmanDataset;"
                    "from patchtst_koopman.utils.config_loader import load_config;"
                    "from patchtst_koopman.lifting.robot_lifting import *;"
                    "print('import OK')"],
                   capture_output=True, cwd=str(CODE))
print("  rc=", r.returncode)
print("  stdout:", r.stdout.decode("utf-8", "replace").strip()[:400])
if r.returncode != 0:
    print("  stderr:", r.stderr.decode("utf-8", "replace").strip()[-800:])

print("\nfinal revision:", revision())
