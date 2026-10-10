import re

p = r"D:\Project\vibe-coding\vibe-coding\AI_INSTALL.md"
t = open(p, encoding="utf-8").read()

checks = {
    "Format N offenders (must be [])": re.findall(r"\bFormat\s+[0-9]+\b", t),
    "has runtime/opencode/install.sh (must be True)": "runtime/opencode/install.sh" in t,
    "has global_installer.py verify (must be False)": "global_installer.py verify" in t,
    "has codex mcp list (must be False)": "codex mcp list" in t,
    "bare ./install.sh line (must be None)": re.search(r"(?m)^\s*\./install\.sh\b", t),
    "has init_project.py --target (must be False)": 'init_project.py" --target' in t,
    "has vibe.py init (must be True)": 'vibe.py" init' in t,
}
for k, v in checks.items():
    print(f"  {k}: {v!r}")

print()
print("=== new section as written ===")
start = t.index("## 全局默认模型")
end = t.index("## Vibe Python 环境与安装流程")
print(t[start:end].rstrip())
