# -*- coding: utf-8 -*-
import sys, io, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"D:\Project\Transformer-Koopman\Transformer-Koopman"
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".project-log", "results", "node_modules"}

non_ascii_paths = []
non_ascii_ident = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    rel_dir = os.path.relpath(dirpath, ROOT)
    for name in list(dirnames) + filenames:
        if any(ord(c) > 127 for c in name):
            non_ascii_paths.append(os.path.join(rel_dir, name))
    for fn in filenames:
        if not fn.endswith(".py"):
            continue
        p = os.path.join(dirpath, fn)
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            # non-ASCII inside an identifier-ish token (not in a string/comment)
            stripped = line.split("#", 1)[0]
            for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*[\u4e00-\u9fff][A-Za-z0-9_\u4e00-\u9fff]*", stripped):
                non_ascii_ident.append("%s:%d: %s" % (os.path.relpath(p, ROOT), i, m.group(0)))

print("=== non-ASCII path/file names (%d) ===" % len(non_ascii_paths))
for x in sorted(non_ascii_paths):
    print("  ", x)
print()
print("=== non-ASCII identifiers in .py (%d) ===" % len(non_ascii_ident))
for x in sorted(non_ascii_ident):
    print("  ", x)
