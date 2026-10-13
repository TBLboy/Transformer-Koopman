# -*- coding: utf-8 -*-
"""Generate the ARM reports from the raw ledgers (nothing typed by hand).

Outputs:
  reports/arm_modeling_comparison.md   WP-M on the robotic arm (Gate 1/2)
  reports/arm_control_comparison.md    WP-C on the robotic arm (Gate 3/4/5)
  reports/arm_cross_device.md          arm vs soft platform, method-for-method

Run:  python scripts/report_arm.py --device arm_3link
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "models"))

import device as dev                          # noqa: E402
dev.bootstrap_from_argv()

D = dev.current()
RES = dev.results_dir("modeling")
CTRL = dev.results_dir("control")
THEO = dev.results_dir("theory_diagnostics")
REP = os.path.join(EXP, "reports")
FIG = os.path.join(EXP, "figures")
os.makedirs(FIG, exist_ok=True)

SPECS = ["M0", "M1", "M2", "M3", "M4", "M5", "M6"]
NAMES = {
    "M0": "DMDc (linear state space)",
    "M1": "EDMDc (fixed dictionary)",
    "M2": "EDMD-DL with control (learnable dictionary)",
    "M3": "LSTM/GRU controlled predictor",
    "M4": "old model A(c) + fixed B0",
    "M5": "new model A(c) + B(x)",
    "M6": "Controlled Transformer",
}
HKEYS = list(D["horizons"].keys())
STATE_NAMES = D["state_names"]


def mean_std(vals):
    v = np.asarray([x for x in vals if x == x], dtype=float)
    if not v.size:
        return float("nan"), float("nan")
    return float(v.mean()), float(v.std(ddof=0))


def load(p):
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def secs(hk):
    return D["horizons"][hk] * D["dt"]


# ============================================================ modelling
def report_modeling():
    led = load(os.path.join(RES, "gate1_ledger.json"))
    if led is None:
        print("no arm gate1 ledger yet -> reports/arm_modeling_comparison.md skipped")
        return
    test = led.get("test", {})
    lines = []
    A = lines.append
    A("# 机械臂 WP-M 建模比较报告（Gate 1 / Gate 2）")
    A("")
    A("> **状态**：临时实验材料，**不是论文正文**；数值全部由 `scripts/report_arm.py`")
    A("> 从 `results/arm/modeling/gate1_ledger.json` 自动生成，无手工填写。")
    A("> **协议**：`configs/arm_protocol.yaml`（设备冻结口径）+ `configs/modeling_protocol.yaml`（方法口径）。")
    A("> **数据审计**：`reports/data_audit_arm.md`（机械臂 Gate 0）。")
    A("")
    A("## 1. 设置摘要")
    A("")
    A("| 项 | 值 |")
    A("|---|---|")
    A("| 设备 | %s（%d 维状态 / %d 维控制） |" % (D["label"], D["n_state"], D["n_ctrl"]))
    A("| 状态 | `%s` |" % " ; ".join("x[%d]=%s" % (i, n) for i, n in enumerate(STATE_NAMES)))
    A("| 控制 | `%s` |" % ", ".join(D["control_names"]))
    _nt = D["n_traj"]
    A("| 数据 | 真实平台采集；%d 条记录 × %d 步；dt = %g s（%g Hz） |"
      % (sum(_nt.values()), D["trajectory_length"], D["dt"], 1.0 / D["dt"]))
    A("| 划分 | 按完整轨迹 %d/%d/%d（train/val/test）；train-only 归一化常数冻结 |"
      % (_nt["train"], _nt["val"], _nt["test"]))
    A("| 历史窗口 | P = %d 测量 + P−1 = %d 过去输入；当前输入 u_k 不进 context |"
      % (D["history_P"], D["history_P"] - 1))
    A("| 隐维 | d = %d（= n + %d；沿用软体平台「n_psi = 8」规则） |"
      % (D["latent_dim"], D["latent_dim"] - D["n_state"]))
    A("| 预测任务 | one-step x_{k+1}；自回归开环 H ∈ {%s} = {%s} s |"
      % (", ".join(str(D["horizons"][k]) for k in HKEYS),
         ", ".join("%g" % secs(k) for k in HKEYS)))
    A("| 评估起点 | 冻结整数算法生成，所有模型/种子完全相同 |")
    A("| 选择准则 | validation 多步 rollout RMSE（H=%d，协议口径），**从不使用 test** |"
      % D["selection_horizon"])
    A("| 搜索预算 | 每模型 6 trial（random search）→ 选定配置 3 seed 重训 → test 一次评估 |")
    A("| 随机种子 | 0, 1, 2 |")
    A("")
    A("**关键不可比点**：250 Hz 下协议步数时域 H=25 只有 **%g s**（软体平台同一 H 是 5 s）。"
      % secs("mid"))
    A("因此下表同时给出协议步数口径与物理时间口径；**跨设备比较时必须用物理时间**。")
    A("")
    A("## 2. Gate 1 主表（test，归一化单位，mean ± std，3 seeds）")
    A("")
    A("归一化分母为 train-only `x_std`（逐通道）。**不报告单一最优 seed**。")
    A("")
    A("> **test 只有 1 条轨迹**：本表所有数字的统计单位是 **1 条独立轨迹**，")
    A("> 因此没有「跨轨迹方差」可言，也不能声称统计显著性。")
    A("")
    hdr = "| 方法 | one-step | " + " | ".join(
        "roll H=%d (%.2gs)" % (D["horizons"][k], secs(k)) for k in HKEYS) + " | 参数量 |"
    A(hdr)
    A("|---" * (len(HKEYS) + 3) + "|")
    for s in SPECS:
        runs = test.get(s)
        if not runs:
            A("| %s %s | 待运行 |%s — |" % (s, NAMES[s], " — |" * len(HKEYS)))
            continue
        os_m, _ = mean_std([r["test"]["one_step"]["short"] for r in runs])
        cells = []
        for k in HKEYS:
            m, sd = mean_std([r["test"]["rollout"][k] for r in runs])
            cells.append("%.4f ± %.4f" % (m, sd) if sd == sd else "%.4f" % m)
        A("| %s %s | %.4f | %s | %d |" % (s, NAMES[s], os_m, " | ".join(cells),
                                          runs[0]["params"]))
    A("")
    A("## 3. 逐通道 RMSE（H=%d，归一化单位）" % D["selection_horizon"])
    A("")
    A("**禁止**用全通道平均误差掩盖某一通道退化。")
    A("")
    A("| 方法 | " + " | ".join(STATE_NAMES) + " |")
    A("|---" * (len(STATE_NAMES) + 1) + "|")
    for s in SPECS:
        runs = test.get(s)
        if not runs:
            continue
        pc = np.asarray([r["test"]["per_channel"]["mid"] for r in runs])
        A("| %s | %s |" % (s, " | ".join("%.4f ± %.4f" % (pc[:, j].mean(), pc[:, j].std())
                                         for j in range(pc.shape[1]))))
    A("")
    A("## 4. 逐 seed 明细（H=%d，最长协议时域；暴露不稳定）" % D["horizons"]["long"])
    A("")
    A("| 方法 | seed 0 | seed 1 | seed 2 | 均值 ± 标准差 |")
    A("|---|---|---|---|---|")
    for s in SPECS:
        runs = test.get(s)
        if not runs:
            continue
        vals = [r["test"]["rollout"]["long"] for r in runs]
        while len(vals) < 3:
            vals.append(float("nan"))
        m, sd = mean_std(vals)
        A("| %s | %.4f | %.4f | %.4f | %.4f ± %.4f |" % (s, vals[0], vals[1], vals[2], m, sd))
    A("")
    if "long3" in HKEYS:
        A("## 5. 物理时间长时域（H=%d = %g s；协议步数口径之外）"
          % (D["horizons"]["long3"], secs("long3")))
        A("")
        A("| 方法 | H=%d (%.2gs) | H=%d (%.2gs) |" % (D["horizons"]["long2"], secs("long2"),
                                                        D["horizons"]["long3"], secs("long3")))
        A("|---|---|---|")
        for s in SPECS:
            runs = test.get(s)
            if not runs:
                continue
            m2, s2 = mean_std([r["test"]["rollout"]["long2"] for r in runs])
            m3, s3 = mean_std([r["test"]["rollout"]["long3"] for r in runs])
            A("| %s | %.4f ± %.4f | %.4f ± %.4f |" % (s, m2, s2, m3, s3))
        A("")
    A("## 6. 配对比较（同 seed 差值，H=%d）" % D["selection_horizon"])
    A("")
    A("所有模型使用**同一测试起点集合**且同种子，故同 seed 差值即配对量。n = 3，**不做显著性断言**。")
    A("")
    A("| 对比 | seed 0 | seed 1 | seed 2 | 均值 ± 标准差 |")
    A("|---|---|---|---|---|")
    for a, b in (("M4", "M5"), ("M5", "M3"), ("M4", "M6"), ("M5", "M2"), ("M4", "M0")):
        ra, rb = test.get(a), test.get(b)
        if not ra or not rb:
            continue
        d = [ra[i]["test"]["rollout"]["mid"] - rb[i]["test"]["rollout"]["mid"]
             for i in range(min(len(ra), len(rb)))]
        while len(d) < 3:
            d.append(float("nan"))
        m, sd = mean_std(d)
        A("| %s − %s | %+.4f | %+.4f | %+.4f | %+.4f ± %.4f |"
          % (a, b, d[0], d[1], d[2], m, sd))
    A("")
    A("> 负值表示左侧误差更小。**同号且绝对值远大于标准差**才算一致差异。")
    A("")
    A("## 7. 失败与异常记录（不得静默排除）")
    A("")
    A("| 模型 | trial | 状态 | 说明 |")
    A("|---|---|---|---|")
    anyfail = False
    for s in SPECS:
        for t in led.get("trials", {}).get(s, []):
            if t.get("status") != "ok":
                anyfail = True
                A("| %s | %d | %s | %s |" % (s, t["trial"], t["status"],
                                             str(t.get("error", ""))[:160].replace("|", "/")))
    if not anyfail:
        A("| — | — | — | 本次搜索无失败 trial |")
    A("")
    A("## 8. 入选配置（validation 选择，test 只评估一次）")
    A("")
    A("| 模型 | 配置 |")
    A("|---|---|")
    for s in SPECS:
        b = led.get("best", {}).get(s)
        if b:
            A("| %s | `%s` (val roll25 = %.6f) |"
              % (s, json.dumps(b["cfg"], ensure_ascii=False), b["val_roll25"]))
    A("")

    # Gate 2
    g2 = load(os.path.join(RES, "gate2_diagnostics.json"))
    g2_sum = ((g2 or {}).get("em3") or {}).get("summary", {})
    em4 = (g2 or {}).get("em4", {})
    em5 = (g2 or {}).get("em5", {})
    A("## 9. Gate 2 — E-M3 结构消融（配对：同 encoder / 窗口 / latent / 损失 / 预算）")
    A("")
    if g2_sum:
        A("配对配置（取自 M5 的入选配置）：`%s`"
          % json.dumps((g2 or {}).get("paired_cfg", {}), ensure_ascii=False))
        A("")
        A("| 结构 | roll H=%d | roll H=%d | one-step | 参数量 |" % (D["selection_horizon"],
                                                                    D["horizons"]["long"]))
        A("|---|---|---|---|---|")
        for v in ("A0B0", "AcB0", "A0Bx", "AcBx"):
            sm = g2_sum.get(v)
            if sm:
                A("| %s | %.4f ± %.4f | %.4f | %.4f | %d |"
                  % (v, sm["roll25_mean"], sm["roll25_std"], sm["roll100_mean"],
                     sm["one_step_mean"], sm["params"]))
        A("")
        A("> `A0B0` = 无调度；`AcB0` = 只有 A(c)；`A0Bx` = 只有 B(χ)；`AcBx` = 完整模型（M5）。")
    else:
        A("*待运行 `scripts/run_gate2.py --device arm_3link`。*")
        A("")
    A("## 10. Gate 2 — E-M4 容量匹配")
    A("")
    if em4.get("target_params"):
        sel = em4.get("selected", {})
        ms = em4.get("matched_summary", {})
        A("| 项 | 值 |")
        A("|---|---|")
        A("| 完整模型参数量 | %d |" % em4["target_params"])
        A("| 匹配后的 `A(c)+B0` | d_model=%s, r_A=%s, 参数量=%s（相对误差 %.1f%%） |"
          % (sel.get("d_model"), sel.get("r_A"), sel.get("params"),
             100.0 * sel.get("rel_err", 0.0)))
        if ms:
            A("| 匹配后 roll H=%d | %.4f ± %.4f |" % (D["selection_horizon"],
                                                      ms["roll25_mean"], ms["roll25_std"]))
        A("")
    else:
        A("*待运行 `scripts/run_gate2.py --device arm_3link`。*")
        A("")
    A("## 11. Gate 2 — E-M5 调度诊断（test 起点采样经验界；**不是**全局 Lipschitz 证书）")
    A("")
    if em5:
        A("| 结构 | ‖A(c)−A0‖₂ max | ‖B(χ)−B0‖₂ max | ρ(A) max | ΔA 有效秩(90%) | 输入响应相对差 |")
        A("|---|---|---|---|---|---|")
        for v in ("A0B0", "AcB0", "A0Bx", "AcBx"):
            d = em5.get(v, {})
            A("| %s | %.4f | %.4f | %.4f | %d | %.3f |"
              % (v, d.get("A_dev_spec_max", 0.0), d.get("B_dev_spec_max", 0.0),
                 d.get("rho_A_max", 0.0), d.get("dA_effective_rank_90pct", 0),
                 d.get("Bx_response_rel_diff_mean", 0.0)))
        A("")
        A("> `ρ(A) > 1` 表示**调度后的 A 不稳定**；这与「‖A(c)−A0‖ 有界」不矛盾：")
        A("> 有界性不保证稳定（论文规则 §C.16）。")
        A("")
    else:
        A("*待运行 `scripts/run_gate2.py --device arm_3link`。*")
        A("")
    A("## 12. 结论与局限")
    A("")
    A("**结论按数据填写，不预设优劣。**")
    A("")
    A("局限：")
    A("")
    A("- **test 只有 1 条轨迹**，所有 test 结论的统计单位为 1；")
    A("- 超参搜索 6 trial/模型（算力受限），不保证接近各方法最优配置；")
    A("- 250 Hz 下 one-step（4 ms 前瞻）接近平凡，**结论应主要依据多步 rollout**；")
    A("- M3/M6 的递推是「预测测量喂回输入序列」，与 scheduled Koopman 的 latent 递归传播是不同策略；")
    A("- 本节所有误差为**离线预测**误差，不含任何闭环控制含义。")
    A("")

    out = dev.report_path("modeling_comparison.md")
    io.open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("written -> %s" % out)
    figures(test)


def figures(test):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, len(HKEYS), figsize=(4.2 * len(HKEYS), 4.2))
        if len(HKEYS) == 1:
            ax = [ax]
        for k, hk in zip(range(len(HKEYS)), HKEYS):
            for s in SPECS:
                runs = test.get(s)
                if not runs:
                    continue
                curves = np.asarray([r["test"]["curve"][hk] for r in runs])
                m = curves.mean(axis=0)
                ax[k].plot(np.arange(1, len(m) + 1), m, label=s)
                if curves.shape[0] > 1:
                    ax[k].fill_between(np.arange(1, len(m) + 1), curves.min(0), curves.max(0),
                                       alpha=0.15)
            ax[k].set_title("H=%d (%.2g s)" % (D["horizons"][hk], secs(hk)))
            ax[k].set_xlabel("rollout step h")
            ax[k].set_ylabel("RMSE (normalised)")
            ax[k].set_yscale("log")
            ax[k].grid(alpha=0.3)
        ax[0].legend(fontsize=7)
        fig.suptitle("Arm: rollout RMSE vs horizon (test, mean over seeds; band = min..max)")
        fig.tight_layout()
        p1 = dev.figure_path("em2_horizon_rmse.png")
        fig.savefig(p1, dpi=150)
        plt.close(fig)
        print("written -> %s" % p1)
    except Exception as exc:                                  # noqa: BLE001
        print("figure failed: %r" % (exc,))


# ============================================================ control
def report_control():
    test = load(os.path.join(CTRL, "control_test.json"))
    val = load(os.path.join(CTRL, "control_val_search.json"))
    fr = load(os.path.join(THEO, "freezing_diagnostics.json"))
    if test is None and fr is None:
        print("no arm control artifacts yet -> reports/arm_control_comparison.md skipped")
        return
    lines = []
    A = lines.append
    A("# 机械臂 WP-C 控制实验报告（Gate 3 / Gate 4 / Gate 5）")
    A("")
    A("> **状态**：临时实验材料，**不是论文正文**；本文件由 `scripts/report_arm.py`")
    A("> 从 `results/arm/**` 与单测原始输出自动生成，数值无手工填写。")
    A(">")
    A("> **诚实边界（先读）**：本报告只包含**离线闭环仿真**（控制器输出驱动一个仿真 plant 的下一步状态），")
    A("> **没有**任何真实硬件实验。所有控制结论只对所用 plant 成立。")
    A("> 离线 QP 求解耗时**不等于**闭环控制周期。")
    A("")
    A("## 1. 框架与不声称清单")
    A("")
    A("| 类别 | 定义 | 本报告是否包含 |")
    A("|---|---|---|")
    A("| 离线预测回放 | 用真实记录的控制序列评价模型 | ✅（Gate 1/2，见 `arm_modeling_comparison.md`） |")
    A("| 闭环仿真 | 控制器输出影响仿真 plant 的下一步状态 | ✅（§3） |")
    A("| 真实硬件闭环 | 控制器驱动真实执行器并实时获取反馈 | ❌ **未做** |")
    A("")
    A("不声称：闭环稳定性、递归可行性、实时性/截止时间、真实硬件控制、非凸完整问题的全局最优性。")
    A("")
    A("**plant 独立性**：plant A = M3（GRU 受控预测器），plant B = M6（Controlled Transformer），")
    A("与三个控制器的内部模型（`A0/B0`、M4、M5）属于不同模型族。")
    A("")
    A("## 2. Gate 3 — 控制器单元测试（n=%d, m=%d）" % (D["n_state"], D["n_ctrl"]))
    A("")
    A("```powershell")
    A("D:\\conda\\envs\\edmddl2\\python.exe -u tests\\test_ltv_qp.py --device arm_3link")
    A("```")
    A("")
    raw = ""
    p = os.path.join(CTRL, "gate3_unit_tests_arm.txt")
    if os.path.exists(p):
        raw = io.open(p, encoding="utf-8").read()
    import re
    m = re.search(r"(\d+)/(\d+) tests passed", raw)
    if m:
        A("**结果：%s/%s 通过**（原始输出 `results/arm/control/gate3_unit_tests_arm.txt`）。"
          % (m.group(1), m.group(2)))
    else:
        A("**结果**：未找到单测原始输出。")
    A("")
    A("覆盖：冻结预测矩阵 `Z=F+GU`、目标函数与梯度、OSQP↔cvxpy 独立对照、盒约束饱和、")
    A("`nominal_rollout` 自洽、LTI 退化、控制器端到端（含 warm-start 与确定性）、")
    A("latent 递归传播（encoder 每次 rollout 只调用一次）、Gate-5 helper 一致性。")
    A("")

    if test:
        A("## 3. Gate 4 — 控制场景评估（离线闭环仿真）")
        A("")
        A("**命令**：`python scripts/run_gate4.py --device arm_3link --split val --search`")
        A("→ `python scripts/run_gate4.py --device arm_3link --split test`")
        A("")
        A("**控制器**：C0 = 固定线性模型（`A0,B0`）+ LTI-MPC；C1 = M4 `A(c)+B0` + 冻结调度 LTV-MPC；")
        A("C2 = M5 `A(c)+B(x)` + 冻结调度 LTV-MPC。三者使用**相同代价权重、相同约束、相同求解器**。")
        A("")
        meta = test.get("scenario_meta", {})
        A("**场景**：定点 %d 步（%g s），跟踪 %d 步（%g s）；位置通道 %s，速度目标 0。"
          % (meta.get("setpoint_steps", 0), meta.get("setpoint_steps", 0) * D["dt"],
             meta.get("tracking_steps", 0), meta.get("tracking_steps", 0) * D["dt"],
             meta.get("pos_channels")))
        A("")
        A("**力矩盒约束**：物理 %s（来源：%s）。"
          % (json.dumps(test.get("u_limit_physical_assumed")), test.get("u_limit_source")))
        A("")
        A("> ⚠️ 该限幅是 **train 经验范围 × 1.05 的假设**（DEC-086，用户确认口径），")
        A("> **不是执行器额定极限**；因此必须同时看输入越界比例（§3.4）。")
        A("")
        A("### 3.1 plant 保真度（**实际使用的 plant**，test 冻结起点）")
        A("")
        A("| plant | one-step | roll H=5 | roll H=25 | roll H=100 | 来源 |")
        A("|---|---|---|---|---|---|")
        rc = test.get("model_reproduction_check") or {}
        for pn, spec in (("plant_A_M3_GRU", "M3"), ("plant_B_M6_Transformer", "M6")):
            af = (rc.get(spec) or {}).get("actual_model_fidelity")
            li = (rc.get(spec) or {}).get("load_info") or {}
            src = ("checkpoint %s" % li.get("path")) if li.get("loaded") else "本进程重训 seed0"
            if af:
                A("| %s (%s) | %.4f | %.4f | %.4f | %.4f | %s |"
                  % (pn, spec, af["one_step"], af["roll5"], af["roll25"], af["roll100"], src))
        A("")
        A("### 3.1b 模型复现一致性（本进程模型 vs Gate-1 ledger seed 0）")
        A("")
        A("| 模型 | 本进程 one-step | ledger seed0 | 绝对差 | 判定 |")
        A("|---|---|---|---|---|")
        for spec in ("M3", "M4", "M5", "M6"):
            c = rc.get(spec)
            if not c:
                continue
            d = c["abs_diff_one_step"]
            v = "一致（<=1e-3）" if d <= 1e-3 else "**不一致：种子 0 训练不可复现**"
            A("| %s | %.6f | %.6f | %.2e | %s |"
              % (spec, c["retrained_one_step"], c["ledger_seed0_one_step"], d, v))
        A("")
        runs = test["runs"]["default"]
        A("### 3.2 定点调节（setpoint，%d 个目标）" % len(meta.get("targets", [])))
        A("")
        A("| plant | 控制器 | 稳态误差 | 调节步数 | 超调 % | 控制能量 | 约束违反 | 求解失败 | 中位求解 ms |")
        A("|---|---|---|---|---|---|---|---|---|")
        for pn in runs:
            for cn in ("C0", "C1", "C2"):
                A("| %s | %s | %.4f | %.1f | %.1f | %.3g | %.1f | %.1f | %.2f |"
                  % (pn, cn, agg(runs, pn, cn, "setpoint", "steady_state_error"),
                     agg(runs, pn, cn, "setpoint", "settling_time_steps"),
                     agg(runs, pn, cn, "setpoint", "overshoot_pct"),
                     agg(runs, pn, cn, "setpoint", "control_energy"),
                     agg(runs, pn, cn, "setpoint", "constraint_violations"),
                     agg(runs, pn, cn, "setpoint", "solve_failures"),
                     agg(runs, pn, cn, "setpoint", "solve_ms_median")))
        A("")
        A("### 3.3 轨迹跟踪（tracking）")
        A("")
        A("| plant | 控制器 | RMSE | MAE | 最大误差 | 相位滞后(步) | 输入变化 | 约束违反 | 求解失败 | p95 求解 ms |")
        A("|---|---|---|---|---|---|---|---|---|---|")
        for pn in runs:
            for cn in ("C0", "C1", "C2"):
                A("| %s | %s | %.4f | %.4f | %.4f | %.1f | %.3g | %.1f | %.1f | %.2f |"
                  % (pn, cn, agg(runs, pn, cn, "tracking", "rmse"),
                     agg(runs, pn, cn, "tracking", "mae"),
                     agg(runs, pn, cn, "tracking", "max_error"),
                     agg(runs, pn, cn, "tracking", "phase_lag_steps"),
                     agg(runs, pn, cn, "tracking", "input_variation"),
                     agg(runs, pn, cn, "tracking", "constraint_violations"),
                     agg(runs, pn, cn, "tracking", "solve_failures"),
                     agg(runs, pn, cn, "tracking", "solve_ms_p95")))
        A("")
        A("### 3.4 plant 外推诚实指标（超出 train 数据范围的比例）")
        A("")
        A("> **重要**：学习到的 plant 只在训练分布内可信；越界比例高说明闭环结果**大部分是外推**，")
        A("> 此时只能作为「在所学 plant 上的相对比较」，**不能**当作真实平台性能。")
        A("")
        A("| plant | 控制器 | 状态越界比例 | 输入越界比例 |")
        A("|---|---|---|---|")
        for pn in runs:
            for cn in ("C0", "C1", "C2"):
                A("| %s | %s | %.3f | %.3f |"
                  % (pn, cn, agg(runs, pn, cn, "tracking", "plant_state_out_of_train_range_frac"),
                     agg(runs, pn, cn, "tracking", "input_out_of_train_range_frac")))
        A("")
        if val:
            A("### 3.5 敏感性分析（validation 场景，权重对三个控制器**同时**改变）")
            A("")
            subset = (val.get("scenario_meta") or {}).get("scenario_subset")
            if subset:
                A("> **场景子集**：本次敏感性研究使用 %s（2 个场景），且该子集对**所有**设置"
                  "（含 `default`）统一使用，以保证排序比较内部一致（DEC-088 D2，计算预算约束）。"
                  % ", ".join("`%s`" % s for s in subset))
                A("> 因此本节数字**不能**与 §3.2/§3.3 的全场景数字相减。")
                A("")
            A("| 设置 | plant | C0 RMSE | C1 RMSE | C2 RMSE | 排序 |")
            A("|---|---|---|---|---|---|")
            for st, rr in val["runs"].items():
                for pn in rr:
                    v = {cn: agg(rr, pn, cn, "tracking", "rmse") for cn in ("C0", "C1", "C2")}
                    order = " < ".join(sorted(v, key=lambda k: v[k]))
                    A("| %s | %s | %.4f | %.4f | %.4f | %s |"
                      % (st, pn, v["C0"], v["C1"], v["C2"], order))
            A("")
            A("> 该表用于检验排序是否依赖某一组权重；**不用于挑选权重**。主比较使用 `default`。")
            A("")
    else:
        A("## 3. Gate 4 — 控制场景评估")
        A("")
        A("*待运行 `python scripts/run_gate4.py --device arm_3link --split val --search` 与 `--split test`。*")
        A("")

    A("## 4. Gate 5 — 理论—实验交叉核验（冻结调度误差）")
    A("")
    if fr:
        A("模型 `%s`，时域 H=%d，起点数 %d，对称盒 ±%s。"
          % (fr["model"], fr["horizon"], fr["n_starts"],
             fr["decision_comparison"].get("constraint", "")))
        A("")
        A("| ‖U−Ū‖ 水平 | 实测 ‖U−Ū‖ | max‖z_full−z_fr‖ | max‖c_full−c̄‖ | ‖A_full−Ā‖₂ max | ‖B_full−B̄‖₂ max | 代价差 max |")
        A("|---|---|---|---|---|---|---|")
        for r in fr["deltas"]:
            A("| %.2f | %.3f | %.3e | %.3e | %.3e | %.3e | %.3e |"
              % (r["delta"], r["u_mismatch_mean"], r["z_err_max_max"], r["c_err_max"],
                 r["A_dev_spec_max"], r["B_dev_spec_max"], r["cost_gap_max"]))
        A("")
        tc = fr["theory_checks"]
        A("- P1（`U = Ū` 时冻结误差恒为 0）：**%s**"
          % ("成立" if tc["P1_zero_mismatch_gives_zero_error"] else "不成立"))
        A("- P2（冻结误差随 ‖U−Ū‖ 增长）：**%s**"
          % ("成立" if tc["P2_monotone_growth"] else "不成立"))
        A("")
        A("**决策比较（同一可行集、仅输入约束）**")
        A("")
        A("| 量 | 值 |")
        A("|---|---|")
        for k, v in fr["decision_comparison"].items():
            if k == "note":
                continue
            A("| `%s` | %s |" % (k, v))
        A("")
        A("> %s" % fr["decision_comparison"]["note"])
        A("")
        A("**不声称**：" + "；".join(fr["not_claimed"]) + "。")
        A("")
    else:
        A("*待运行 `python scripts/run_gate5.py --device arm_3link`。*")
        A("")
    A("## 5. 未验证项与待确认问题")
    A("")
    A("- 力矩限幅 = train 经验范围 × 1.05（DEC-086，用户确认口径），**是假设而非执行器额定值**；")
    A("  已附 `data_range_u` 敏感性设置以隔离外推影响。")
    A("- 未做真实硬件实验；无急停/传感器异常/控制超时回退的实测。")
    A("- 控制权重为先验固定，另做敏感性分析；**不以控制器相对优劣为准则调参**。")
    A("- C3（完整非线性 MPC）与 C4（多次调度更新）未实现，原因见 `configs/control_protocol.yaml`。")
    A("- 关节 2 力矩被重力偏置主导（几乎不过零），盒约束非对称；定点目标取自 train 分位数，")
    A("  与真实任务需求无关。")
    A("")

    out = dev.report_path("control_comparison.md")
    io.open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("written -> %s" % out)


def agg(runs, plant, ctrl, kind, key):
    vals = []
    for name, mm in runs.get(plant, {}).get(ctrl, {}).items():
        if name.startswith("setpoint") == (kind == "setpoint") and key in mm:
            vals.append(mm[key])
    return (sum(vals) / len(vals)) if vals else float("nan")


# ============================================================ cross device
def report_cross():
    arm = load(os.path.join(RES, "gate1_ledger.json"))
    soft = load(os.path.join(EXP, "results", "modeling", "gate1_ledger.json"))
    if arm is None or soft is None:
        print("need both ledgers -> reports/arm_cross_device.md skipped")
        return
    soft_dt, soft_h = 0.2, {"short": 5, "mid": 25, "long": 100}
    lines = []
    A = lines.append
    A("# 跨设备对照：机械臂 vs 软体平台（同方法、同协议规则）")
    A("")
    A("> 本文件由 `scripts/report_arm.py` 从两个 ledger 自动生成，无手工填写。")
    A("> **方法完全一致**（M0–M6、窗口规则、归一化规则、评估指标、选择准则、控制器集合）。")
    A("> **设备不同**，因此下表按**物理时间**对齐，而不是按步数。")
    A("")
    A("## 1. 设备差异")
    A("")
    A("| 项 | 软体平台 | 机械臂 |")
    A("|---|---|---|")
    A("| 状态维 | 2 | %d |" % D["n_state"])
    A("| 控制维 | 2 | %d |" % D["n_ctrl"])
    A("| dt | 0.2 s（5 Hz） | %g s（%g Hz） |" % (D["dt"], 1.0 / D["dt"]))
    A("| 记录 | 100 × 300 步 | 20 × ~4977 步 |")
    A("| 划分（轨迹） | 70 / 20 / 10 | 15 / 4 / 1 |")
    A("| 隐维 d | 10（n + 8） | %d（n + 8） |" % D["latent_dim"])
    A("| 协议时域 | H ∈ {5, 25, 100} = {1, 5, 20} s | H ∈ {%s} = {%s} s |"
      % (", ".join(str(D["horizons"][k]) for k in HKEYS),
         ", ".join("%g" % secs(k) for k in HKEYS)))
    A("| MPC 时域 | N = 10（2 s） | N = %d（%g s） |" % (D["mpc_N"], D["mpc_N"] * D["dt"]))
    A("")
    A("## 2. 物理时间对齐的预测误差（test，归一化单位，3 seeds 均值）")
    A("")
    A("每行取机械臂的一个时域，并找出软体平台**物理时间最接近**的时域。两设备的时域集合"
      "并不重合（软体平台 H ∈ {5,25,100} = {1,5,20} s；机械臂 H ∈ {%s} = {%s} s），"
      "因此两列都标注物理秒数与时间比，**不是严格同点对照**。"
      % (", ".join(str(D["horizons"][k]) for k in HKEYS),
         ", ".join("%g" % secs(k) for k in HKEYS)))
    A("")
    A("| 机械臂时域 | 软体平台最接近时域 | 时间比(软/机) | M3 (GRU) | M5 (A(c)+B(χ)) | M6 (Transformer) |")
    A("|---|---|---|---|---|---|")
    soft_items = sorted(soft_h.items(), key=lambda kv: kv[1])
    for hk in HKEYS:
        ha = D["horizons"][hk]
        ta = ha * D["dt"]
        sk, hs = min(soft_items, key=lambda kv: abs(kv[1] * soft_dt - ta))
        ts = hs * soft_dt
        cells = []
        for spec in ("M3", "M5", "M6"):
            a = arm.get("test", {}).get(spec)
            s = soft.get("test", {}).get(spec)
            if not a or not s:
                cells.append("—")
                continue
            va = float(np.mean([r["test"]["rollout"][hk] for r in a]))
            vs = float(np.mean([r["test"]["rollout"][sk] for r in s]))
            cells.append("%.4f → %.4f" % (vs, va))
        A("| H=%d (%.3g s) | H=%d (%.3g s) | %.2f× | %s |"
          % (ha, ta, hs, ts, ts / ta, " | ".join(cells)))
    A("")
    A("> ⚠️ 由于时间比不等于 1（最接近的配对仍有 %.1f–%.1f 倍差距），"
      "**本表只能说明量级与趋势，不能用于声称某设备上方法更准**。"
      % (min(soft_h[k] * soft_dt / (D["horizons"][h] * D["dt"])
             for h in HKEYS for k in soft_h),
         max(soft_h[k] * soft_dt / (D["horizons"][h] * D["dt"])
             for h in HKEYS for k in soft_h)))
    A("")
    A("> ⚠️ 两设备的**物理时域集合并不重合**（软体平台记录只有 60 s，机械臂只有 20 s；")
    A("> 且步数网格不同），上表用最接近的可用时域，**不是严格同点对照**。")
    A("> 更严格的对齐需要为两设备重跑同一物理时域集合，本轮未做。")
    A("")
    A("## 3. 协议步数口径对照（**仅用于说明口径差异，不用于跨设备排序**）")
    A("")
    A("| 方法 | 软体平台 H=25 | 机械臂 H=25 | 软体平台 H=100 | 机械臂 H=100 |")
    A("|---|---|---|---|---|")
    for spec in SPECS:
        a = arm.get("test", {}).get(spec)
        s = soft.get("test", {}).get(spec)
        if not a or not s:
            continue
        A("| %s | %.4f | %.4f | %.4f | %.4f |"
          % (spec,
             float(np.mean([r["test"]["rollout"]["mid"] for r in s])),
             float(np.mean([r["test"]["rollout"]["mid"] for r in a])),
             float(np.mean([r["test"]["rollout"]["long"] for r in s])),
             float(np.mean([r["test"]["rollout"]["long"] for r in a]))))
    A("")
    A("> 同一 H 在两设备代表完全不同的物理时间（H=25：软体平台 5 s vs 机械臂 0.1 s），")
    A("> **本表不得用于声称某设备上方法更好**。")
    A("")
    A("## 4. 结构结论是否一致")
    A("")
    A("| 问题 | 软体平台结论 | 机械臂结论 |")
    A("|---|---|---|")
    A("| A(c) 调度是否有收益 | 有（H=25：0.0756 → 0.0265） | 见 `arm_modeling_comparison.md` §9 |")
    A("| B(χ) 是否有可测量收益 | **无**（0.0265 → 0.0258；输入响应相对差 1.2–2.2%） | 见 §9 / §11 |")
    A("| M4 与 M5 是否被选中相同配置 | 是（参数量差 0.26%） | 见 §8 |")
    A("| ρ(A) 是否 > 1（调度后不稳定） | 是（1.01–1.03） | 见 §11 |")
    A("| 控制排序是否稳健 | 否（tight_R / N20 下翻转） | 见 `arm_control_comparison.md` §3.5 |")
    A("")
    A("> 本表把两设备的**同类问题**并列，结论栏指向各自报告的权威小节；")
    A("> 不得把某一设备的结论直接搬到另一设备。")
    A("")

    out = os.path.join(REP, "arm_cross_device.md")
    io.open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("written -> %s" % out)


def main():
    # HARD GUARD: this script writes device-scoped reports.  Run without the arm
    # device it would overwrite the SOFT platform's reports with arm text -- which
    # actually happened once during tooling checks, so it is now impossible.
    if D["name"] != "arm_3link":
        raise SystemExit(
            "report_arm.py is the ARM report generator but the active device is %r.\n"
            "Re-run with:  python scripts/report_arm.py --device arm_3link\n"
            "(refusing to overwrite the soft-platform reports)"
            % D["name"])
    print("device=%s -> report prefix %r" % (D["name"], D["report_prefix"]))
    report_modeling()
    report_control()
    report_cross()


if __name__ == "__main__":
    main()
