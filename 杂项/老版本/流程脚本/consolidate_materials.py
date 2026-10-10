# -*- coding: utf-8 -*-
"""Consolidate the research materials from the opencode temp folder into
D:\\Project\\Transformer-Koopman\\Transformer-Koopman\\杂项 (COPY, originals kept)."""
import os, re, sys, shutil, hashlib, io

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SRC = r"C:\Users\12187\AppData\Local\Temp\opencode"
DST = r"D:\Project\Transformer-Koopman\Transformer-Koopman\杂项"

RESEARCH_RE = re.compile(
    r"^(gate|V_|D_|Q_|N_|N_P|spike_|ctrl_|testA_|testB_|testC_|test_r1|p1_|p2_|p08|"
    r"profile_|diagnose_|audit_|debug_|s8|plot_|render_|extract_|eval_|peek_ckpt|"
    r"check_ckpt|inspect_p2_ckpt|repro_restore|rewrite_|inspect_data|inspect_route)")

RESULT_JSON_RE = re.compile(
    r"^(gate|N_|D_|Q_|V_|spike_|test|p1_|p08|ctrl_baseline)")

RECORD_JSON_RE = re.compile(
    r"(_payload\.json$|_covers\.json$|^covers_|^env_t|^dec-|^fig3_|^minor_rev_|"
    r"^reviewer_edits_|^latex_compile_|^r4_|^svc-state|^vibe-status)")

buckets = {
    "研究代码": [],
    "流程脚本": [],
    "模型检查点": [],
    "实验结果": [],
    "记录载荷": [],
    "图表": [],
    "说明文档": [],
}
skipped = []

for name in sorted(os.listdir(SRC)):
    p = os.path.join(SRC, name)
    if not os.path.isfile(p):
        continue
    ext = os.path.splitext(name)[1].lower()
    base = os.path.splitext(name)[0]
    if ext == ".py":
        buckets["研究代码" if RESEARCH_RE.match(base) else "流程脚本"].append(name)
    elif ext == ".json":
        if RECORD_JSON_RE.search(name):
            buckets["记录载荷"].append(name)
        elif RESULT_JSON_RE.match(base):
            buckets["实验结果"].append(name)
        else:
            buckets["记录载荷"].append(name)  # default any other json to record payloads
    elif ext == ".pt":
        buckets["模型检查点"].append(name)
    elif ext == ".png":
        buckets["图表"].append(name)
    elif ext in (".md", ".txt", ".ps1", ".log"):
        buckets["说明文档"].append(name)
    else:
        skipped.append(name)

# gate_states/*.pt -> 模型检查点
for name in sorted(os.listdir(os.path.join(SRC, "gate_states"))):
    buckets["模型检查点"].append("gate_states/" + name)

# ---- copy ----
os.makedirs(DST, exist_ok=True)
manifest = {}
for bucket, names in buckets.items():
    outdir = os.path.join(DST, bucket)
    os.makedirs(outdir, exist_ok=True)
    for n in names:
        srcp = os.path.join(SRC, n.replace("/", os.sep))
        dstp = os.path.join(outdir, os.path.basename(n))
        shutil.copy2(srcp, dstp)
    manifest[bucket] = len(names)
    print(f"{bucket}: {len(names)}")

print("skipped(root, not classified):", len(skipped))
print("skipped names:", skipped)

# ---- integrity: compare sha256 for a sample (all files) ----
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

bad = 0
checked = 0
for bucket, names in buckets.items():
    for n in names:
        srcp = os.path.join(SRC, n.replace("/", os.sep))
        dstp = os.path.join(DST, bucket, os.path.basename(n))
        if not os.path.exists(dstp):
            print("MISSING:", dstp); bad += 1; continue
        if os.path.getsize(srcp) != os.path.getsize(dstp) or sha(srcp) != sha(dstp):
            print("MISMATCH:", n); bad += 1
        checked += 1
print(f"verified {checked} files, mismatches={bad}")

with io.open(os.path.join(DST, "_manifest_counts.txt"), "w", encoding="utf-8") as f:
    for k, v in manifest.items():
        f.write(f"{k}\t{v}\n")
print("DONE")
