import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

SUMMARY = (
    "阶段① 代码迁移与清理（第一批）完成。迁移：src/patchtst_koopman + scripts + configs + deploy + "
    "run_all_training.bat/.ps1 + README，与老仓库字节一致（除 .gitignore 位置与有意修改）；"
    "数据适配层 prepare_data.py（P1 输出与老 experiment_001 逐元素+sha256 相同）。"
    "缺陷处理：ALN-003/005/006/007/008/011/012/013/019/020 resolved，ALN-014 accepted（中文目录名经 DEC-014），"
    "ALN-004 partially-resolved（残余=ALN-002 阶段②）。ALN-010 四部分（EDMD 闭式解/PositionalEncoding/"
    "subprocess pipeline/rollout）完成，仍 partially-resolved（残余=部署侧模型栈副本一致性测试，阶段②/后续）。"
    "回归套件 220 passed / 2 skipped / 1 xfailed；smoke_train PASS（rho=0.999753）；smoke_test 4/4。"
    "决策：DEC-012（删死键）、DEC-013（FIX 编号退役，ALN 为权威）、DEC-014（保留中文目录名）。"
    "GOAL-001 门禁评估：拒绝完成（8 项 SC 全 pending，6 项必需证据缺失，高风险目标缺独立复核）——"
    "剩余 ALN-001/002/004残余/009/010残余/015/016/017/018 属阶段②（理论方法讨论）与阶段③（重训）。"
    "未验证项：阶段②/③ 的方法论与重训结果尚未产生；部署侧模型栈副本一致性测试未补。"
)


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
    print(f"  {'OK  ' if ok else 'FAIL'} {label}" + ("" if ok else " -> " + r.stderr.decode("utf-8", "replace")[:400]))


print("== finish TASK-002 ==")
apply("task.finish", {"task_id": "TASK-002", "summary": SUMMARY}, "t35-finish", "task.finish")

print("\nfinal revision:", revision())
