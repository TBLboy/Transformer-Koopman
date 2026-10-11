# -*- coding: utf-8 -*-
"""
TASK-041（阶段八）装配扫描器 —— 只用标准库，任何 Python 3 均可。

做四件事：
  1) Theory_Package 的九件套点名 + 文件清单（含 sha256）。
  2) 交叉引用自洽性：每件里 `NN` 形式的引用是否指向存在的件；
     以及对外部路径（notes/、validation/、论文/）的引用是否存在。
  3) 禁止清单扫描：bilinear/双线性、实时/截止时间/deadline、闭环稳定/递归可行、
     摘要/Introduction/实验/标题 —— 逐条给出命中行，并粗分类「否定式 / 未分类」。
     要求：未分类命中数必须为 0（即每一处命中都是明确的否定或禁止清单本身的引用）。
  4) 论文/ 目录是否被本阶段改动（列出 mtime；git 层面的核验由主 Agent 用 git 另行完成）。

运行：D:\\conda\\envs\\vibe-coding\\python.exe 00_assembly_scan.py
（脚本自行以 UTF-8 写出同目录的 00_assembly_scan.txt，然后打印一行 ok；
 不要用 shell 重定向，PowerShell 控制台编码会污染中文。）
"""
import io, os, re, hashlib, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))   # Theory_Package -> 新版本 -> 杂项 -> repo
NEW = os.path.abspath(os.path.join(HERE, ".."))                # 杂项/新版本
out = []

NINE = ["01_Model_Definition.md", "02_Assumptions.md", "03_Low_rank_Boundedness.md",
        "04_Scheduling_Lipschitz.md", "05_Prediction_Error_Bound.md",
        "06_Frozen_LTV_QP_Proof.md", "07_Freezing_Error_Bound.md",
        "08_Conditional_Suboptimality.md", "09_Reference_List.md"]

out.append("repo root : %s" % REPO)
out.append("scanned   : %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# ---------- 1) inventory -----------------------------------------------------
out.append("")
out.append("=== 1. Theory_Package inventory ===")
names = sorted(os.listdir(HERE))
nineset = set(NINE)
for n in names:
    p = os.path.join(HERE, n)
    if os.path.isfile(p):
        b = io.open(p, "rb").read()
        tag = "nine " if n in nineset else "aux  "
        out.append("  %s %8d B  sha256=%s  %s" % (tag, len(b), hashlib.sha256(b).hexdigest().lower()[:16], n))
    else:
        out.append("  dir       %s/" % n)
missing = [n for n in NINE if not os.path.isfile(os.path.join(HERE, n))]
out.append("")
out.append("  nine-piece checklist : %d/9 present%s"
           % (9 - len(missing), "" if not missing else "  MISSING=%s" % missing))

# ---------- 2) cross references ---------------------------------------------
out.append("")
out.append("=== 2. cross-reference self-consistency ===")
TEXT = {}
for n in names:
    p = os.path.join(HERE, n)
    if os.path.isfile(p) and n.endswith((".md", ".py", ".txt")):
        TEXT[n] = io.open(p, "r", encoding="utf-8", errors="replace").read()

bad = []
for n in NINE:
    if n not in TEXT:
        continue
    refs = sorted(set(re.findall(r"`(0[1-9])`", TEXT[n])))
    tgt = []
    for r in refs:
        hit = [x for x in NINE if x.startswith(r)]
        if hit:
            tgt.append(r)
        else:
            bad.append("%s -> `%s` (no such piece)" % (n, r))
    out.append("  %-34s -> %s" % (n, ",".join(tgt) if tgt else "(none)"))

# external path references mentioned in the pieces
out.append("")
out.append("  external path references mentioned inside the pieces:")
for needle in ["notes/literature/", "validation/", "论文/", "citation_audit_report.md",
               "_audit_bib.json", "framework-defects.md"]:
    hits = [n for n in NINE if needle in TEXT.get(n, "")]
    out.append("    %-28s mentioned in: %s" % (needle, ", ".join(hits) if hits else "(none)"))
for rel in [os.path.join("notes", "literature", "01_search_log.md"),
            os.path.join("notes", "literature", "02_ref_scan.py"),
            os.path.join("notes", "literature", "03_ref_scan_output.txt"),
            os.path.join("validation", "validate_theory.py"),
            os.path.join("validation", "results.md"),
            os.path.join("validation", "results.json")]:
    p = os.path.join(NEW, rel)
    out.append("    exists? %-46s %s" % (rel.replace("\\", "/"), os.path.isfile(p)))
out.append("  dangling internal refs: %s" % (bad if bad else "none"))

# ---------- 3) prohibition scan ---------------------------------------------
out.append("")
out.append("=== 3. prohibition scan ===")
PAT = [
    ("bilinear", r"bilinear|双线性|bi-linear"),
    ("realtime", r"real-time|real time|实时|截止时间|deadline"),
    ("closedloop", r"closed-loop stability|闭环稳定|递归可行|recursive feasibility|保证.{0,6}稳定|guarantee[sd]?\s+\w*\s*stabil"),
    ("abstract", r"\\begin\{abstract\}|\b摘要\b"),
    ("introduction", r"\\section\{Introduction|^\s*#+\s*Introduction|\bIntroduction\b"),
    ("experiment", r"\bexperiments?\b|实验"),
    ("title", r"\\title\{|论文标题"),
]
NEG = r"(不|未|无|非|禁止|不得|不做|不作|没有|避免|排除|not\b|no\b|without|never|prohibit)"
total_hits = 0
unclassified = 0
UNCL = []
for n in NINE:
    if n not in TEXT:
        continue
    lines = TEXT[n].split("\n")
    hits = []
    for i, ln in enumerate(lines, 1):
        for label, pat in PAT:
            m = re.search(pat, ln)
            if not m:
                continue
            head = ln[:m.start()]
            neg = re.search(NEG, head[-40:]) is not None or re.search(NEG, ln[m.end():m.end() + 20]) is not None
            hits.append((label, i, neg, ln.strip()[:130]))
    total_hits += len(hits)
    unclassified += sum(1 for h in hits if not h[2])
    for label, i, neg, ln in hits:
        if not neg:
            UNCL.append((n, label, i, ln))
    out.append("  --- %s : %d hit(s), %d unclassified" % (n, len(hits), sum(1 for h in hits if not h[2])))
    for label, i, neg, ln in hits:
        out.append("      [%s%s] L%d: %s" % (label, "" if neg else " ?", i, ln))
out.append("")
out.append("  TOTAL hits=%d  unclassified=%d  (unclassified must be 0)" % (total_hits, unclassified))
out.append("")
out.append("  --- unclassified hits, listed for MANUAL adjudication (the classifier is deliberately crude:")
out.append("      it looks 40 chars before / 20 chars after the keyword for a negation marker, so")
out.append("      cross-row table cells, section headings and long sentences will show up here).")
for n, label, i, ln in UNCL:
    out.append("      %s L%d [%s]: %s" % (n, i, label, ln))

# hard markers: these must be absent everywhere in the nine pieces
out.append("")
out.append("  hard markers (must be absent from the nine pieces):")
for label, pat in [("\\begin{abstract}", r"\\begin\{abstract\}"), ("\\section{Introduction}", r"\\section\{Introduction"),
                   ("\\title{", r"\\title\{"), ("\\maketitle", r"\\maketitle")]:
    found = [n for n in NINE if re.search(pat, TEXT.get(n, ""))]
    out.append("    %-24s %s" % (label, "ABSENT" if not found else "PRESENT in %s" % found))

# ---------- 4) paper dir untouched? -----------------------------------------
out.append("")
out.append("=== 4. 论文/ file mtimes (git-level check is done separately by the main agent) ===")
PAPER = os.path.join(REPO, "论文")
for dp, dn, fn in os.walk(PAPER):
    if ".git" in dp:
        continue
    for f in sorted(fn):
        p = os.path.join(dp, f)
        out.append("  %s  %s" % (datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M"),
                                 os.path.relpath(p, PAPER)))

text = "\n".join(out) + "\n"
io.open(os.path.join(HERE, "00_assembly_scan.txt"), "w", encoding="utf-8", newline="\n").write(text)
print("ok -> %s (%d lines, unclassified=%d)" % (os.path.join(HERE, "00_assembly_scan.txt"), len(out), unclassified))
