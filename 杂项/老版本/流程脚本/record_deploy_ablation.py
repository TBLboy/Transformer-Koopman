import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
DB = next(Path(ROOT, ".project-log", ".state").rglob("state.sqlite3"))
CODE = Path(ROOT) / "Transformer-Koopman" / "训练代码"

FILES = [
    "Transformer-Koopman/训练代码/configs/platform2.yaml",
    "Transformer-Koopman/训练代码/scripts/smoke_test.py",
    "Transformer-Koopman/训练代码/deploy/README.md",
    "Transformer-Koopman/训练代码/deploy/export_baseline_assets.py",
    "Transformer-Koopman/训练代码/tests/test_no_hardcoded_paths.py",
    "Transformer-Koopman/训练代码/README.md",
]
VB = {"git_commit": None, "diff_hash": None,
      "file_hashes": {f: hashlib.sha256((Path(ROOT) / f).read_bytes()).hexdigest() for f in FILES}}


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
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:220]))


print("== DEC-011: deploy/ + ablation/ migrated; docs/figures/experiment1/experiment3 excluded ==")
apply("record.create", {
    "id": "DEC-011", "kind": "decision", "status": "active",
    "title": "阶段① 迁移范围补充：迁入 deploy/ 与 src/ablation/，排除 docs/figures/experiment1/experiment3；暂不提交",
    "payload": {
        "authority": "C", "user_approval": "approved",
        "answered_question": "老仓库 5 个未迁移目录如何处理；是否现在提交迁移",
        "decision": "只迁移 deploy/（11 文件，字节一致）；同时补齐 src/patchtst_koopman/ablation/（11 文件，字节一致）以修复 scripts/ablation/* 的导入断裂；docs/、figures/、experiment1/、experiment3/ 不迁移；本次迁移暂不提交 git。",
        "rationale": "deploy/ 是已迁移脚本（smoke_test.py、test_platform2_pth.py）的依赖，且是阶段③ 部署所需；ablation/ 是 scripts/ablation/* 的硬依赖，缺失即断链。docs/figures/experiment1/experiment3 属阶段① 范围外，用户明确排除。",
        "consequence": "deploy/export_baseline_assets.py 的 --source-root 需指向老仓库 experiment1/（已改为必填参数）；README 已标注未迁移目录。",
        "supersedes_note": "细化 DEC-006 的「最小集合」边界。",
    }}, "t17-dec11", "DEC-011 created")

print("\n== ALN-020: editable install shadows the new repo ==")
apply("record.create", {
    "id": "ALN-020", "kind": "alignment", "status": "open",
    "title": "edmddl2 的 patchtst_koopman editable 安装指向旧副本，静默遮蔽新仓库代码",
    "payload": {
        "category": "environment-hazard",
        "observation": "conda env edmddl2 中 patchtst-koopman 0.1.0 为 editable 安装，Editable project location = D:\\Project\\code-projectv2。无 sys.path 干预时 import patchtst_koopman 解析到 D:\\Project\\code-projectv2\\src\\patchtst_koopman。",
        "discovery": "smoke_test.py 第 4 步 traceback 显示导入路径为 D:\\Project\\code-projectv2\\src\\...，而非新仓库。",
        "related_finding": "D:\\Project\\code-projectv2 与 D:\\Project\\论文3老版本\\Transformer-Koopman 是同一仓库的两份副本（git log 均为 ec90f2a/7dc1a20/6f9b1cf，src 树哈希均为 658df80cd6180604 / 42 py）。",
        "impact": "任何未显式插入 src/ 的脚本会静默使用旧代码，产生看似成功但结论错误的运行结果。",
        "mitigation_applied": "smoke_train.py:27、tests/conftest.py:18、scripts/smoke_test.py 均已显式 sys.path.insert(0, <repo>/src)，已验证导入解析到新仓库。",
        "residual_risk": "新增脚本若忘记插入 src/ 仍会踩坑；根治需在新仓库执行 pip install -e . 重指向，或卸载该 editable 包（属环境级变更，待用户决定）。",
        "verification": "smoke_test.py 修复后 traceback 路径变为 训练代码\\src\\patchtst_koopman\\...，4/4 步通过。",
    }}, "t17-aln020", "ALN-020 created")

print("\n== evidence: deploy/ + ablation/ migration, platform2 data_dir fix ==")
apply("evidence.record", {
    "id": "EV-PHASE1-MIGRATE-002", "kind": "test",
    "subject": "阶段① 迁移补齐：deploy/ 11 文件与 src/patchtst_koopman/ablation/ 11 文件均字节一致迁入；修正 platform2.yaml data_dir 旧路径；smoke_test.py 补 src/ 到 sys.path 后 4/4 步通过；完整缺口分析显示除 .gitignore 位置差异外无遗漏；pytest 141 passed / 2 skipped / 1 xfailed",
    "status": "valid", "task_id": "TASK-002",
    "covers": {"tasks": ["TASK-002"], "requirements": ["REQ-001"], "files": FILES},
    "version_binding": VB}, "t17-ev-migrate2", "EV-PHASE1-MIGRATE-002")

print("\nfinal revision:", revision())
