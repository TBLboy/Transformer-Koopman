import hashlib
import sys

import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

DOC = r"D:\Project\Transformer-Koopman\.project-log\docs\business-logic\clarification.yaml"

FIXES = [
    (
        '      - "论文当前仅使用单步预测损失（3 项）" —— 已过期；论文实为 5 项\n',
        "      - 论文当前仅使用单步预测损失（3 项）—— 该说法已过期；论文实为 5 项\n",
    ),
    (
        '      - "L_c 去留暂定保留" —— 已由论文明确为保留\n',
        "      - L_c 去留暂定保留 —— 已由论文明确为保留\n",
    ),
]

text = open(DOC, encoding="utf-8").read()
for old, new in FIXES:
    if old in text:
        text = text.replace(old, new)
        print("patched:", old.strip()[:60])
    else:
        print("NOT FOUND:", old.strip()[:60])

open(DOC, "w", encoding="utf-8", newline="\n").write(text)

try:
    data = yaml.safe_load(text)
    print("\nYAML VALID")
    print("top keys:", list(data.keys()))
    print("alignment entries:", len(data["alignment"]))
    print("atoms check - invariants:", len(data["functional_business_logic"]["invariants"]))
except yaml.YAMLError as error:
    print("\nSTILL INVALID:")
    mark = getattr(error, "problem_mark", None)
    lines = text.splitlines()
    if mark is not None:
        for i in range(max(0, mark.line - 3), min(len(lines), mark.line + 3)):
            flag = ">>" if i == mark.line else "  "
            print(f"{flag} {i+1:4d}: {lines[i]}")
    print(error)

b = text.encode("utf-8")
print("\nbytes:", len(b))
print("sha256:", hashlib.sha256(b).hexdigest())
