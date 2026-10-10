import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
base = r"D:\Project\Transformer-Koopman\Transformer-Koopman"
for d in [r"数据备份\软体平台数据\原始数据", r"数据备份\软体平台数据\处理后的数据"]:
    p = os.path.join(base, d)
    print("=== " + d + " ===")
    if os.path.isdir(p):
        for f in sorted(os.listdir(p))[:30]:
            fp = os.path.join(p, f)
            print(("  [D] " if os.path.isdir(fp) else "  [F] ") + f)
    else:
        print("  (missing)")
    print()
# look for any data/ or experiment_006 dirs
print("=== search: data / experiment_006 / *.pth under repo ===")
hits = []
for root, dirs, files in os.walk(base):
    if ".git" in root or "__pycache__" in root:
        continue
    low = root.lower()
    if low.endswith(os.sep + "data") or "experiment_006" in low:
        hits.append(root)
    for f in files:
        if f.endswith(".pth") or f.endswith(".pt"):
            hits.append(os.path.join(root, f))
for h in hits[:60]:
    print("  " + h)
print("  total:", len(hits))
