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
    return ok


apply("record.create", {
    "kind": "research", "id": "RES-001",
    "title": "目标仓库基线盘点与代码迁移策略选项分析（喂给 Q-MIGRATE-001）",
    "status": "complete",
    "payload": {
        "question_ref": "Q-MIGRATE-001",
        "baseline_inventory": {
            "work_folder": "D:\\Project\\Transformer-Koopman",
            "code_repo": "D:\\Project\\Transformer-Koopman\\Transformer-Koopman",
            "训练代码": "0 files / 0 subdirs (EMPTY)",
            "结果备份": "0 files / 0 subdirs (EMPTY)",
            "杂项": "0 files / 0 subdirs (EMPTY)",
            "数据备份": "129 files / 6 subdirs (机械臂数据 raw 20 .mat + processed 3; 软体平台数据 raw 100 .npz + processed 5, 含 train_data.mat 5.9MB)",
            "论文": "74 files / 6 subdirs (Main*.tex 33 个草稿 + bare_* 模板 + bibtex/tools/extras/testflow)",
            "git_tracked_files": 0,
            "git_untracked_entries": ["数据备份/", "论文/"],
            "gitignore_present": False,
            "branch": "Transformer-Koopman",
        },
        "implication": "阶段① 的前置条件是从老仓库迁移代码，而不是直接改已有文件；DEC-004 对阶段① 的描述与新仓库实际状态不匹配。",
        "options": [
            {"id": "A", "name": "迁移后清理", "desc": "整体拷贝老仓库训练代码到新仓库，再逐项执行 FIX-01..FIX-10。", "pro": "最快得到可端到端验证的流水线；改动与老代码可逐行对照。", "con": "先继承老结构债（重复 trainer、死代码、配置漂移），FIX-08/09 的收敛工作更晚。"},
            {"id": "B", "name": "洁净重建", "desc": "只按已批准契约（REQ-001 + 5 项损失）重写最小包骨架 Data->Dataset->Train->Eval，按需移植模块。", "pro": "结构最干净，天然满足可安装包与配置驱动目标。", "con": "最易无意识偏离论文方法定义；数字无法与老结果直接对照，追溯成本最高。"},
            {"id": "C", "name": "混合（推荐）", "desc": "核心（model / lifting / trainer）迁移并清理，外层（配置 schema、流水线编排、测试）重写。", "pro": "保住已由日志与论文验证过的数值路径，同时让外层结构干净；可在 platform1 M1 上先跑通最小 smoke 作为锚点。", "con": "需要明确划分 核心 vs 外层 的边界并逐个模块判断，判断成本前置。"},
        ],
        "recommendation": "选 C 混合，且第一步只迁移到能在 platform1 上跑通 M1 的最小集合，先建 FIX-10 测试套件作为迁移安全网，再逐步扩大范围。",
        "second_question": "是否将 数据备份/ 与 论文/ 加入 .gitignore。二者共 203 文件且含二进制（train_data.mat 5.9MB、IEEEtran.cls、多个 PDF），纳入 git 会让仓库迅速膨胀且难以增量管理。建议 ignore 二者，仅在需要时以外部路径引用。",
        "open_uncertainty": "用户期望的最终目录布局尚未确认（杂项/ 与 结果备份/ 目前为空且用途未知）。"}},
    "t8-res1", "research RES-001")

apply("record.link", {"from_kind": "research", "from_id": "RES-001",
                      "relation": "references", "to_kind": "requirement", "to_id": "REQ-001"},
      "t8-link1", "link RES-001 -> REQ-001")

print("\nfinal revision:", revision())
