import hashlib
import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
DOC_REL = ".project-log/docs/business-logic/clarification.yaml"
DOC_ABS = r"D:\Project\Transformer-Koopman\.project-log\docs\business-logic\clarification.yaml"

DOC_SHA = hashlib.sha256(open(DOC_ABS, "rb").read()).hexdigest()
DOC_REF = {"path": DOC_REL, "sha256": DOC_SHA}

ATOMS = [
    ("BA-MP1", "active", "主链路：原始数据到实时控制",
     {"rule": "RawData(NPZ) -> KoopmanDataset -> [Encoder|LiftingFunction] -> KoopmanDynamics -> [Decoder] -> Evaluation -> DeployAssets -> RealTimeControl",
      "source": "论文 + 老 .project-log/business-logic/main.md + graph.md", "authority": "confirmed"}),
    ("BA-PLATFORMS", "active", "两个实验平台的规格",
     {"rule": "P1=6-DOF 柔性机械臂 state_dim=6 control_dim=3；P2=2-DOF 软体机器人 state_dim=2 control_dim=2",
      "source": "configs/platform1.yaml, configs/platform2.yaml", "authority": "confirmed"}),
    ("BA-METHODS", "active", "必须支持的方法族",
     {"rule": "主方法 PatchTST-Koopman；对照基线 MLP-Koopman / LSTM-Koopman / Traditional EDMD；同一训练器的另一 method 为 End-to-End",
      "source": "论文 + 老 requirements.md", "authority": "confirmed"}),
    ("BA-LOSS-STRUCT", "active", "Stage-1 损失为 5 项且双平台统一",
     {"rule": "L_pre = lambda_x L_x + lambda_z L_z + lambda_c L_c + lambda_multi_x L_multi_x + lambda_multi_z L_multi_z，其中 L_multi 为 sum_{i=1..N_L}；L_c 保留为重编码鲁棒正则项",
      "source": "论文.txt eq:pretraining_loss（权威）+ DEC-003", "authority": "confirmed",
      "doc_ref": DOC_REF}),
    ("BA-LOSS-NUM", "draft", "多步损失的权重数值与 N_L（待阶段②）",
     {"rule": "lambda 数值（含 multi_step_physical=10.0）与 horizon N_L 尚未冻结，属阶段② 理论方法讨论议题",
      "source": "DEC-003 provisional + DEC-004", "authority": "inferred/draft", "blocked_by": "阶段② 理论讨论"}),
    ("BA-ABLATION", "active", "消融变体集合与排序不变量",
     {"variants": ["no_patch", "no_attention", "no_positional", "window", "patch_size", "readout", "pure_feature"],
      "invariant": "full_model 在全部变体中表现最好；去掉 Patch/Attention/PositionalEncoding 后性能必须下降",
      "outputs": ["CSV", "LaTeX 表格", "柱状图"], "source": "老 edges.md E7 + 论文", "authority": "confirmed"}),
    ("BA-INV1", "active", "Koopman 矩阵谱半径约束",
     {"rule": "谱半径 <= 1，由 SVD 裁剪保证（控制器稳定性前提）",
      "source": "老 constraints.md Safety Constraints", "authority": "confirmed"}),
    ("BA-INV3", "active", "部署包不依赖训练包",
     {"rule": "上位机只装 PyTorch CPU，不安装训练包；部署侧必须自包含",
      "source": "老 constraints.md Software Constraints", "authority": "confirmed"}),
    ("BA-INV4", "active", "滑动窗口不得跨越轨迹边界",
     {"rule": "样本 i 的有效范围必须保证整个 history 与 future target 落在同一 trajectory 内",
      "source": "data/dataset.py:100-117", "authority": "confirmed"}),
    ("BA-INV5", "active", "归一化统计量只由训练集决定",
     {"rule": "val/test 必须复用 train 的 mean/std，不得重算",
      "source": "data/dataset.py:77-88, utils/data_prep.py:17-21", "authority": "confirmed"}),
    ("BA-INV6", "active", "history_length 必须可被 patch_length 整除",
     {"rule": "不满足时必须在 __init__ 抛出 ValueError，不得退化为隐晦的 reshape 错误",
      "source": "老 known-issues.md 2026-06-05 修复项", "authority": "confirmed"}),
    ("BA-SCOPE", "active", "本增量范围边界",
     {"in_scope": ["双平台建模", "四类方法训练与评估", "消融实验", "部署资产导出", "论文配图"],
      "out_of_scope": ["硬件在环测试", "上位机 GUI 开发", "FlexibleArmControl34 本体代码"],
      "read_only": ["D:\\Project\\论文3老版本\\Transformer-Koopman"],
      "source": "老 requirements.md 任务范围", "authority": "confirmed"}),
]

ALIGNMENTS = [
    ("ALN-001", "constraint-conflict", "双平台 Stage-1 损失项数不一致（P1 五项 / P2 三项）", "结构性由 DEC-003 裁决，数值待阶段②"),
    ("ALN-002", "missing-implementation", "platform2.yaml 缺少 multi_step 与两个多步权重键", "待阶段② 定值后补键"),
    ("ALN-003", "implementation-drift", "run_all 调度 LSTM x platform2，但 platform2.yaml 无 lstm_koopman 段，必 KeyError", "open"),
    ("ALN-004", "implementation-drift", "代码读取但 YAML 缺失的配置键（含 platform2 缺 6 项）", "open"),
    ("ALN-005", "implementation-drift", "YAML 声明但从不被读取的键（controller/evaluation/logging 整段）", "open"),
    ("ALN-006", "constraint-conflict", "硬编码外部机器绝对路径（论文4 / FlexibleArmControl34）", "open"),
    ("ALN-007", "implementation-drift", "死接口：MATLAB 适配器期望的 checkpoint 格式无人写入", "open"),
    ("ALN-008", "missing-test", "没有可机器判定的回归信号，无 tests/ 无 pytest 配置", "open"),
    ("ALN-009", "traceability-gap", "论文数字与产生它们的配置未绑定", "阶段③ 重训时重建绑定"),
    ("ALN-010", "implementation-drift", "重复实现：rollout x3、pipeline x7、EDMD 损失 x2、PositionalEncoding x3、部署模型栈副本", "open"),
    ("ALN-011", "implementation-drift", "配置对象被就地修改（_patch_config、apply_gpu_training_defaults）", "open"),
    ("ALN-012", "unknown", "data/experiment_002..005 四个孤儿数据目录用途不明", "open"),
    ("ALN-013", "implementation-drift", "消融变体注册集合与 README 宣称不一致", "open"),
    ("ALN-014", "constraint-conflict", "中文路径/文件名造成的工具链隐患", "新项目已规避部分"),
]


def revision() -> int:
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def create(kind: str, rid: str, title: str, status: str, payload: dict, tag: str) -> None:
    envelope = {
        "schema_version": 1,
        "command_id": tag,
        "expected_revision": revision(),
        "action": "record.create",
        "payload": {"kind": kind, "id": rid, "title": title, "status": status, "payload": payload},
    }
    path = f"{TMP}/env_{tag}.json"
    open(path, "w", encoding="utf-8", newline="\n").write(
        json.dumps(envelope, ensure_ascii=False, indent=2)
    )
    size = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", path],
                       capture_output=True)
    ok = r.returncode == 0
    note = "" if ok else r.stderr.decode("utf-8", "replace").strip()[:160]
    print(f"  {'OK ' if ok else 'FAIL'} {kind}/{rid} ({size}B) {note}")


print("doc sha256:", DOC_SHA)
print()
print("== requirement baseline ==")
create("requirement", "REQ-001", "阶段① 重构业务逻辑澄清基线",
       "draft",
       {"doc_ref": DOC_REF,
        "scope": "功能业务逻辑 + 技术业务逻辑 + 双向对齐，覆盖双平台主链路与消融",
        "status_note": "draft：待用户批准后提升为 active",
        "covers": ["BA-MP1", "BA-PLATFORMS", "BA-METHODS", "BA-LOSS-STRUCT", "BA-ABLATION", "BA-SCOPE"]},
       "t012-req001")

print("== business atoms ==")
for rid, status, title, payload in ATOMS:
    create("business-atom", rid, title, status, payload, f"t-atom-{rid.lower()}")

print("== alignments ==")
for aid, klass, subject, status in ALIGNMENTS:
    create("alignment", aid, subject, "open",
           {"class": klass, "subject": subject, "status_note": status,
            "doc_ref": {"path": DOC_REL, "sha256": DOC_SHA}},
           f"t-aln-{aid.lower()}")

print()
print("final revision:", revision())
