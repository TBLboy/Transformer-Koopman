import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\vibe.exe".replace("vibe.exe", r"..\..\vibe-coding\python.exe")
PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"

SUCCESS = [
    "新项目是结构清晰、YAML 配置驱动的可安装 Python 包，覆盖 Data→Dataset→Train→Eval 主链路",
    "双平台统一使用论文 eq:pretraining_loss 定义的 5 项 Stage-1 损失（L_x, L_z, L_c, L_multi_x, L_multi_z），platform2 补齐缺失的多步损失",
    "双平台四类方法（PatchTST-Koopman 主方法、MLP-Koopman、LSTM-Koopman、Traditional EDMD）均可训练与评估并产出 RMSE/MAE，platform2 结果由新配置重训得到",
    "流水线不再调度配置中不存在的任务（消除 LSTM x platform2 KeyError 一类缺陷），且不再硬编码外部机器路径",
    "7 类消融变体（no_patch, no_attention, no_positional, window, patch_size, readout, pure_feature）在双平台可训练评估并产出 CSV/LaTeX/图表",
    "部署资产导出链路可用，部署包不依赖训练包",
    "回归测试套件存在且可重复运行，替代老项目的手工 CLI harness",
    "老项目 D:\\Project\\论文3老版本\\Transformer-Koopman 全程只读",
]

EVIDENCE = [
    "双平台四类方法的训练与评估命令及实际输出（含新的 RMSE/MAE 数字），并说明与老数字的差异来源",
    "platform2 补齐多步损失后的训练配置与结果，含 N_L 与 5 个 lambda 的实际取值",
    "缺陷修复清单及逐项验证证据（KeyError、配置漂移、硬编码路径、死接口）",
    "消融变体训练的完成证据与结果文件（CSV/LaTeX/图表）",
    "回归测试套件的运行命令、结果与环境信息",
    "独立复核（不复用实现者结论）对新项目主链路与论文方法定义一致性的 go 结论",
]


def revision() -> int:
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


envelope = {
    "schema_version": 1,
    "command_id": "t008-goal-update-c",
    "expected_revision": revision(),
    "action": "goal.update",
    "payload": {
        "id": "GOAL-001",
        "success_conditions": SUCCESS,
        "required_evidence": EVIDENCE,
    },
}
path = f"{TMP}/env_t008_goal_update_c.json"
open(path, "w", encoding="utf-8", newline="\n").write(
    json.dumps(envelope, ensure_ascii=False, indent=2)
)
r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path],
                   capture_output=True)
out = r.stdout.decode("utf-8", "replace").strip()
print("rc:", r.returncode)
print(out if r.returncode != 0 else "goal.update OK -> revision " + str(revision()))
