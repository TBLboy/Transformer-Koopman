# -*- coding: utf-8 -*-
"""
TASK-035 / 09_Reference_List.md §3 的可复现扫描脚本。

做三件事：
  1) 解剖 论文/老版本/Main.tex：内联 thebibliography 的 \\bibitem、正文 \\cite、
     文件指纹；给出 cited\\bibitem 与 bibitem\\cited。
  2) 盘点仓库内全部 .bib（数量、条目数、是否为 IEEEtran 模板）。
  3) 盘点草稿 杂项/老版本/_new_*.tex 的 key 并集与「草稿专用」键。
  4) 读 杂项/老版本/_audit_bib.json，把它的题录文本与当前 Main.tex 逐条比对
     （空白归一化），判定既有 strict 审计的可继承范围。

运行：D:\\conda\\envs\\vibe-coding\\python.exe 02_ref_scan.py
（脚本**自行**以 UTF-8 写出同目录的 03_ref_scan_output.txt，然后打印一行 ok；
 请**不要**用 shell 重定向到同一文件 —— PowerShell 控制台编码会污染中文。
 本脚本只用标准库，任何 Python 3 均可。）
"""
import io, os, re, json, hashlib, glob

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", ".."))
# __file__ = <repo>/杂项/新版本/notes/literature/02_ref_scan.py
# 上溯 4 级：literature -> notes -> 新版本 -> 杂项 -> <repo>
out = []

MAIN = os.path.join(REPO, "论文", "老版本", "Main.tex")
b = io.open(MAIN, "rb").read()
txt = b.decode("utf-8", "replace")

out.append("repo root : %s" % REPO)
out.append("Main.tex  : %d B  sha256=%s" % (len(b), hashlib.sha256(b).hexdigest().lower()))
out.append("（既有审计报告记录的指纹：sha256 0DA30C3EDC56…, 80917 B）")

# ---- 1) inline bibliography -------------------------------------------------
m = re.search(r"\\begin\{thebibliography\}(.*?)\\end\{thebibliography\}", txt, re.S)
out.append("")
out.append("=== 1. inline thebibliography ===")
if not m:
    out.append("  NOT FOUND")
    raise SystemExit(1)
out.append("  block at lines %d..%d" % (txt[:m.start()].count("\n") + 1, txt[:m.end()].count("\n") + 1))
blk = m.group(1)
bib = {}
for mm in re.finditer(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}(.*?)(?=\\bibitem|$)", blk, re.S):
    bib[mm.group(1).strip()] = " ".join(mm.group(2).split())
out.append("  bibitem entries : %d" % len(bib))

body = txt[:m.start()]
cited = set()
for mm in re.finditer(r"\\cite[a-zA-Z]*\{([^}]*)\}", body):
    for k in mm.group(1).split(","):
        if k.strip():
            cited.add(k.strip())
out.append("  cite keys       : %d" % len(cited))
out.append("  cited \\ bibitem : %s" % sorted(cited - set(bib)))
out.append("  bibitem \\ cited : %s" % sorted(set(bib) - cited))

# ---- 2) .bib inventory ------------------------------------------------------
out.append("")
out.append("=== 2. .bib inventory ===")
nbib = 0
for p in sorted(glob.glob(os.path.join(REPO, "论文", "**", "*.bib"), recursive=True)):
    t = io.open(p, "r", encoding="utf-8", errors="replace").read()
    n = len(re.findall(r"@\w+\s*\{", t))
    ex = len(re.findall(r"IEEEexample:", t))
    out.append("  %8d B  %-46s entries=%-4d IEEEexample-refs=%d"
               % (os.path.getsize(p), os.path.relpath(p, REPO), n, ex))
    nbib += 1
out.append("  total .bib files: %d" % nbib)

# ---- 3) draft keys ---------------------------------------------------------
out.append("")
out.append("=== 3. draft 杂项/老版本/_new_*.tex ===")
draft = set()
for p in sorted(glob.glob(os.path.join(REPO, "杂项", "老版本", "_new_*.tex"))):
    t = io.open(p, "r", encoding="utf-8", errors="replace").read()
    ks = set()
    for mm in re.finditer(r"\\cite[a-zA-Z]*\{([^}]*)\}", t):
        for k in mm.group(1).split(","):
            if k.strip():
                ks.add(k.strip())
    draft |= ks
    out.append("  %-34s %d keys" % (os.path.basename(p), len(ks)))
out.append("  union of draft keys : %d" % len(draft))
out.append("  draft-only (not cited in Main.tex): %d %s" % (len(draft - cited), sorted(draft - cited)))
out.append("  key universe = |bibitem| + |draft-only| = %d + %d = %d"
           % (len(bib), len(draft - cited), len(bib) + len(draft - cited)))

# ---- 4) inherit the prior strict audit -------------------------------------
out.append("")
out.append("=== 4. 既有 strict 审计（_audit_bib.json）的可继承范围 ===")
aj = os.path.join(REPO, "杂项", "老版本", "_audit_bib.json")
if not os.path.isfile(aj):
    out.append("  _audit_bib.json NOT FOUND")
else:
    d = json.load(io.open(aj, "r", encoding="utf-8"))
    order = d.get("order", [])
    ents = d.get("entries", {})
    A = set(order) | set(ents.keys())
    C = set(bib)
    out.append("  audit json: order=%d entries=%d" % (len(order), len(ents)))
    out.append("  |audit keys|=%d |current bibitem|=%d" % (len(A), len(C)))
    out.append("  audit \\ current = %s" % sorted(A - C))
    out.append("  current \\ audit = %s" % sorted(C - A))
    same, diff = [], []
    for k in sorted(A & C):
        v = ents.get(k)
        v = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
        (same if " ".join(v.split()) == bib[k] else diff).append(k)
    out.append("  text-identical  : %d" % len(same))
    out.append("  text-different  : %d %s" % (len(diff), diff))
    out.append("")
    out.append("  text-identical keys (可继承审计核验):")
    for k in same:
        out.append("      %s" % k)

# ---- 5) count self-check for §3.5 ------------------------------------------
out.append("")
out.append("=== 5. §3.5 计数自洽性 ===")
B_cls = ["han2024robust", "shenoy2025temporal"]
draft_only = sorted(draft - cited)
out.append("  A' (= text-identical)      : %d" % len(same))
out.append("  B  (not audited, 2 new)    : %s" % B_cls)
out.append("  A' + B                     : %d  (应为 |bibitem| = %d)" % (len(same) + len(B_cls), len(bib)))
out.append("  draft-only                 : %d" % len(draft_only))
out.append("  D  (already-removed keys)  : yuan2022variational(in draft)=%s  rank2019recurrent(in draft)=%s"
           % ("yuan2022variational" in draft_only, "rank2019recurrent" in draft_only))
uncited_bib = set(bib) - cited
_d_only_unc = sorted(set(draft_only) & uncited_bib)
_yuan = [k for k in draft_only if k == "yuan2022variational"]
_C = [k for k in draft_only if k not in uncited_bib and k != "yuan2022variational"]
out.append("  draft-only 分解            : C=%d + yuan(in D)=%d + Main 未引 bibitem=%d → %d"
           % (len(_C), len(_yuan), len(_d_only_unc), len(_C) + len(_yuan) + len(_d_only_unc)))
out.append("  （其中 Main 未引 bibitem = %s，已计入 A'）" % _d_only_unc)
out.append("  核对宇宙 = |bibitem| + |draft-only| = %d" % (len(bib) + len(draft_only)))

text = "\n".join(out) + "\n"
dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "03_ref_scan_output.txt")
io.open(dst, "w", encoding="utf-8", newline="\n").write(text)
print("ok -> %s (%d lines)" % (dst, len(out)))
