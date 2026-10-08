import glob
import os
import re
import sys

import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

OLD = r"D:\Project\论文3老版本\Transformer-Koopman"


def show(label, value):
    print(f"  {label}: {value}")


print("=== [1] per-platform lifting + stability switches (authoritative configs) ===")
for name in ("platform1", "platform2"):
    d = yaml.safe_load(open(f"{OLD}\\configs\\{name}.yaml", encoding="utf-8"))
    lm = d["training"]["traditional_edmd"]["lifting_function"]
    show(f"{name} state_dim/control_dim", f"{d['data']['state_dim']}/{d['data']['control_dim']}")
    show(f"{name} lifting type", lm.get("type"))
    show(f"{name} lifting params", lm.get("params"))
    show(f"{name} koopman.enforce_stability", d["koopman"].get("enforce_stability"))
    show(f"{name} edmd.compute.svd_clipping", d["training"]["edmd"]["compute"].get("svd_clipping"))
    print()

print("=== [2] threelink_lifting input dim vs platform2 state_dim ===")
src = open(f"{OLD}\\src\\patchtst_koopman\\lifting\\threelink_lifting.py", encoding="utf-8").read().splitlines()
for i, l in enumerate(src, 1):
    if re.search(r"n_input|n_features|assert", l):
        print(f"  threelink_lifting.py:{i}: {l.strip()[:110]}")

print()
print("=== [3] MLP trainer consistency loss ===")
src = open(f"{OLD}\\src\\patchtst_koopman\\training\\mlp_koopman_trainer.py", encoding="utf-8").read().splitlines()
for i, l in enumerate(src, 1):
    if "mse_loss" in l or "detach" in l:
        print(f"  mlp_koopman_trainer.py:{i}: {l.strip()[:120]}")

print()
print("=== [4] EDMDTrainer L_c + multi-step reduction (mean vs sum) ===")
src = open(f"{OLD}\\src\\patchtst_koopman\\training\\edmd_trainer.py", encoding="utf-8").read().splitlines()
for i, l in enumerate(src, 1):
    if re.search(r"L_consistency|L_multi_x =|L_multi_z =|mse_loss|cross_entropy|\.sum\(\)", l):
        print(f"  edmd_trainer.py:{i}: {l.strip()[:120]}")

print()
print("=== [5] do logged artifacts exceed rho=1? ===")
hits = 0
for path in glob.glob(f"{OLD}\\results\\logs\\*.log"):
    text = open(path, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"rho[=:\s]+([0-9]*\.?[0-9]+)", text):
        v = float(m.group(1))
        if v > 1.0:
            hits += 1
            print(f"  {os.path.basename(path)}: rho={v}")
            break
print(f"  logs with rho>1: {hits}")

print()
print("=== [6] document lineage of the paper ===")
for p in (f"{OLD}\\论文.txt", f"{OLD}\\docs\\paper_notes.txt"):
    print(f"  exists {p}: {os.path.isfile(p)}")
tex = glob.glob(f"{OLD}\\论文草稿\\*.tex") + glob.glob(f"{OLD}\\论文草稿\\**\\*.tex", recursive=True)
print(f"  论文草稿 tex drafts: {len(set(tex))}")
five, three = [], []
for t in sorted(set(tex)):
    body = open(t, encoding="utf-8", errors="replace").read()
    has_multi = "multi,x" in body or "mathrm{multi}" in body
    (five if has_multi else three).append(os.path.basename(t))
print(f"  drafts mentioning multi-step loss: {five}")
print(f"  drafts without it: {len(three)} files")
print()
notes = f"{OLD}\\docs\\paper_notes.txt"
if os.path.isfile(notes):
    lines = open(notes, encoding="utf-8", errors="replace").read().splitlines()
    for i, l in enumerate(lines, 1):
        if re.search(r"kept small|largest|小权重|最高权重|10", l):
            print(f"  paper_notes.txt:{i}: {l.strip()[:130]}")
