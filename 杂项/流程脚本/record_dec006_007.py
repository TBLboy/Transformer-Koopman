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


print("== DEC-006: migration strategy = hybrid (C) ==")
apply("record.create", {
    "kind": "decision", "id": "DEC-006",
    "title": "阶段① 代码迁移策略 = C 混合方案（核心迁移+外层重写）", "status": "active",
    "payload": {
        "authority": "C", "user_approval": "approved",
        "answered_question": "Q-MIGRATE-001（选项见 RES-001）",
        "decision": "采用 C 混合方案：核心（model / lifting / trainer）从老仓库迁移并清理，外层（配置 schema、流水线编排、测试）在新仓库重写。第一步只迁移到 platform1 上 M1 能跑通最小 smoke 的范围，先建立 FIX-10 回归测试套件作为迁移安全网，再逐步扩大。",
        "rationale": "保住已被日志与论文验证过的数值路径（降低无意偏离论文方法定义的风险），同时让外层结构干净；最小 smoke 锚点可在迁移早期发现破坏。",
        "supersedes_note": "DEC-004 的阶段① 描述（整理代码）需按本决策理解为 先迁移后清理。"}},
    "t9-dec6", "decision DEC-006")

print("\n== DEC-007: data + paper tracked in git ==")
apply("record.create", {
    "kind": "decision", "id": "DEC-007",
    "title": "数据备份/ 与 论文/ 均不加入 .gitignore，全部纳入 git 跟踪", "status": "active",
    "payload": {
        "authority": "C", "user_approval": "approved",
        "decision": "不建立排除规则；数据备份/（129 文件，含 train_data.mat 5.9MB）与 论文/（74 文件，含 IEEEtran.cls 与多个 PDF）都将被 git 跟踪。",
        "consequence_of_record": "仓库首次提交会包含约 5.9MB 级二进制与 200 个文件；若日后改为不跟踪，仅删除文件不足以从历史中移除，需要重写历史才能缩小仓库体积。此后果已由用户明确接受。",
        "follow_up": "首次 commit 前应确认 .git 目录不会被数据目录污染，并在提交信息中如实说明这是首次数仓同步。"}},
    "t9-dec7", "decision DEC-007")

print("\n== resume TASK-002 (blocker Q-MIGRATE-001 resolved) ==")
apply("task.resume", {
    "task_id": "TASK-002",
    "next_action": "确定仓库代码布局（Q-LAYOUT-001，即 OQ-001）后：建立 FIX-10 回归测试套件骨架，再迁移 platform1 M1 最小集合跑通 smoke，逐项执行 FIX-01..FIX-09"},
    "t9-resume2", "task.resume TASK-002")

print("\nfinal revision:", revision())
