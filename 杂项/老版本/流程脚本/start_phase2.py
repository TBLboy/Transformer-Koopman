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
C = "Transformer-Koopman/训练代码"
PAPER = "Transformer-Koopman/论文/草稿/Main34.tex"

NEXT = ("阶段② 已启动：已读最新稿 Main34.tex（= 论文.txt，含 5 项损失）并与代码对齐。"
        "下一步：与用户逐项确认 6 个差异点（归约 mean/sum、λ 取值、platform2 补键、"
        "MLP/LSTM consistency 语义、论文实验节为空、INV1 与 Theorem 1 的关系），再定损失契约。")

ALIGN = {
    "paper": {
        "file": PAPER,
        "sha256": hashlib.sha256((Path(ROOT) / PAPER).read_bytes()).hexdigest(),
        "note": "Main34.tex 与老仓库 论文.txt 内容一致（仅换行差异）；Main33.tex 是其前身（无 5 项损失）。",
    },
    "architecture_matches": [
        "历史窗口 X_k∈R^{P×n} -> dataset x_history",
        "N=P/p 非重叠 patch -> num_patches=P//p",
        "patch 向量化 vec(X^(i))∈R^{pn} -> reshape(p*n)",
        "patch embedding W_p∈R^{d_model×pn} -> nn.Linear(p*n, d_model)",
        "正弦位置编码 -> utils/positional_encoding.PositionalEncoding",
        "L 层 Transformer -> nn.TransformerEncoder",
        "mean pooling -> readout_method='mean'",
        "h_k=W_h r_k+b_h∈R^{d-n} -> projection Linear(d_model, d-n)",
        "z_k=[x_k;h_k] -> cat([x_t, h_t])",
        "固定解码 C=[I_n 0] -> LinearDecoder z[:, :n]（无参数）",
        "z_{k+1}=A z_k+B u_k -> KoopmanDynamics",
    ],
    "training_matches": [
        "Stage 0 ridge EDMD warm start -> edmd_trainer Stage 0",
        "Θ=(Z+)^T Ω(Ω^T Ω+λI)^{-1} -> utils/koopman_solve.solve_koopman_operator",
        "Stage 1 五项损失 -> _pretrain_epoch（结构逐项对应）",
        "L_x -> L_pred=mse(x_pred,x_next)",
        "L_z -> L_latent=mse(z_pred, z_true=encoder(x_history_next))",
        "L_c=||g_θ(W+_pred)-z_k^+||² -> L_consistency=mse(encoder([x[1:],x_pred]), z_true)",
        "L_multi,x=Σ||x̂_{k+i}-x_{k+i}||² -> L_multi_x=mse(roll_out_latent[...,:n], x_future)",
        "L_multi,z=Σ||ẑ_{k+i}-z_{k+i}||² -> L_multi_z=mse(z_hat_seq, encoder(x_history_future))",
        "Stage 2 refit A,B -> edmd_trainer Stage 2",
        "控制器 Q=diag(Q_x,αI), R, dlqr, u_ff=B†(z_ref_next-A z_ref), u_fb=-K e_z -> deploy/algorithms/transformer_koopman_controller.py",
    ],
    "discrepancies": [
        {
            "id": "D1",
            "topic": "多步损失归约 mean vs sum",
            "paper": "L_multi,x / L_multi,z 用 Σ_{i=1}^{N_L} ||·||²（对 horizon 求和）",
            "code": "F.mse_loss（对 batch×horizon×dims 取均值）",
            "impact": "缩放差约 (batch×N_L×n) 倍；λ 的有效量级随之改变",
            "aln": "ALN-018",
        },
        {
            "id": "D2",
            "topic": "λ 取值未在论文中给出",
            "paper": "λ_x,λ_z,λ_c,λ_multi,x,λ_multi,z 仅称 nonnegative hyperparameters，未写数值；N_L 未写死",
            "code": "platform1: prediction=1.0, latent=0.5, consistency=0.5, multi_step_physical=1.0, multi_step_latent=0.5, N_L=3",
            "impact": "DEC-003 用户定 multi_step_physical=10.0，但 config 仍为 1.0，未落地",
            "aln": "ALN-001/002",
        },
        {
            "id": "D3",
            "topic": "platform2 缺 2 项多步损失",
            "paper": "双平台应统一 5 项",
            "code": "platform2.yaml 无 multi_step 键，loss_weights 仅 3 项",
            "impact": "两平台数字由不同损失产生",
            "aln": "ALN-001/002",
        },
        {
            "id": "D4",
            "topic": "MLP/LSTM consistency 语义",
            "paper": "L_c 是 re-encoding loss：||g_θ(W+_pred)-z_k^+||²",
            "code": "MLP/LSTM 用 mse(z_pred.detach(), z_true)，是 detached 的 latent 一致性，非 re-encoding",
            "impact": "基线的一致性项与主方法/论文语义不同",
            "aln": "ALN-016",
        },
        {
            "id": "D5",
            "topic": "论文实验节为空",
            "paper": "Section VI Experiments 只有 \\section 标题，无内容；abstract/conclusion 声称的结果未在草稿中",
            "code": "results/ 有历史产物，但未与论文绑定",
            "impact": "阶段③ 需重训并填充实验节",
            "aln": "ALN-009",
        },
        {
            "id": "D6",
            "topic": "INV1（rho<=1）与 Theorem 1 的关系",
            "paper": "Theorem 1 只要求 (A,B) 可稳、(A,Q^{1/2}) 可检测，则 A_cl=A-BK_c 为 Schur；未要求 rho(A)<=1",
            "code": "项目 INV1 要求 rho(A)<=1；实际 6 份产物 rho>1",
            "impact": "INV1 比论文更严；rho>1 影响开环多步预测精度，但不直接违反 Theorem 1",
            "aln": "ALN-015",
        },
    ],
    "open_questions_for_user": [
        "D1：多步损失是否改为论文的 sum 归约（会放大 λ 有效量级）？",
        "D2：λ 向量与 N_L 的最终取值（DEC-003 的 10x 是否落地）？",
        "D3：platform2 是否补齐 5 项（含 N_L 与两个多步 λ）？",
        "D4：MLP/LSTM 的 consistency 是否改为论文的 re-encoding 语义？",
        "D6：INV1 是否保留（rho<=1）还是放宽为论文的 stabilizability？",
    ],
}


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


print("== create TASK-003 ==")
apply("task.create", {"id": "TASK-003",
                      "title": "阶段② 论文技术方案对齐与损失契约定值（strict）",
                      "goal_id": "GOAL-001",
                      "extensions": {"implementer": "vibe-main", "owner": "user", "risk_class": "strict"}},
      "t36-task003", "TASK-003")

print("\n== begin RUN-003 ==")
apply("task.begin", {"task_id": "TASK-003", "run_id": "RUN-003", "next_action": NEXT},
      "t36-begin", "task.begin")

print("\n== research record PAPER-ALIGN-001 ==")
apply("record.create", {"kind": "research", "id": "PAPER-ALIGN-001",
                        "title": "最新稿 Main34.tex 技术方案 vs 代码对齐",
                        "status": "complete", "payload": ALIGN},
      "t36-align", "PAPER-ALIGN-001")

print("\nfinal revision:", revision())
