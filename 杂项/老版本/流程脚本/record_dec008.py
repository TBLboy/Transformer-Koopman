import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"


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
    note = "" if ok else " -> " + r.stderr.decode("utf-8", "replace").strip()[:220]
    print(f"  {'OK  ' if ok else 'FAIL'} {label}{note}")


apply("record.create", {
    "kind": "decision", "id": "DEC-008",
    "title": "仓库代码布局：全部代码置于 训练代码/ 下，包名沿用 patchtst_koopman", "status": "active",
    "payload": {
        "authority": "C", "user_approval": "approved",
        "answered_question": "Q-LAYOUT-001（即 OQ-001 ASCII 目录名未决项）",
        "decision": "仓库根保留用户既有中文目录（数据备份/ 论文/ 结果备份/ 杂项/），全部代码与工程文件置于 训练代码/ 之下，形成：训练代码/src/patchtst_koopman/（Python 包，ASCII 名）、训练代码/configs/、训练代码/scripts/、训练代码/tests/、训练代码/pyproject.toml。",
        "rationale": "顶层目录语义清晰（数据/论文/代码分离），且 Python 包名保持 ASCII 以保证 import 与打包工具链兼容；沿用老仓库包名 patchtst_koopman 符合复用现有约定。",
        "resolves": "OQ-001（澄清文档中记录的顶层中文目录名未决项）",
        "consequence": "路径较根目录 src 布局更长；包内相对路径与配置文件定位逻辑需统一以仓库根的 训练代码/ 为基准，迁移时须显式处理，否则会重现 ALN-006 一类路径缺陷。"}},
    "t10-dec8", "decision DEC-008")

print("\nfinal revision:", revision())
