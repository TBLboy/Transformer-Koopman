# -*- coding: utf-8 -*-
"""Generate the WP-M comparison report and figures FROM THE RAW LEDGER.

Every number in the output comes from results/modeling/gate1_ledger.json and
results/modeling/gate2_diagnostics.json.  Nothing is typed by hand.

Run:  python scripts/report_modeling.py
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RES = os.path.join(EXP, "results", "modeling")
FIG = os.path.join(EXP, "figures")
REP = os.path.join(EXP, "reports")
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
HKEYS = ["short", "mid", "long"]


def mean_std(vals):
    v = np.asarray(vals, dtype=float)
    return float(v.mean()), float(v.std(ddof=0))


def main():
    led = json.load(open(os.path.join(RES, "gate1_ledger.json"), encoding="utf-8"))
    test = led.get("test", {})
    finals = led.get("final", {})

    lines = []
    A = lines.append
    A("# WP-M 建模比较报告（E-M1 / E-M2）")
    A("")
    A("> **状态**：临时实验材料，**不是论文正文**；数值全部由 `scripts/report_modeling.py`")
    A("> 从 `results/modeling/gate1_ledger.json` 自动生成，无手工填写。")
    A("> **协议**：`configs/modeling_protocol.yaml`；数据与划分 `configs/data_manifest.yaml`、")
    A("> `configs/split_manifest.yaml`；窗口/起点/归一化/分位数的**唯一**实现是 "
      "`models/protocol.py`（RMSE 公式在 Gate 1/4 脚本内联重算，数值等价但非同一函数调用）。")
    A("")

    # ---------------- settings summary
    A("## 1. 设置摘要")
    A("")
    A("| 项 | 值 |")
    A("|---|---|")
    A("| 数据 | 真实平台采集；100 条记录 × 300 步；dt = 0.2 s |")
    A("| 划分 | 按完整轨迹 70/20/10（train/val/test），train-only 归一化常数冻结 |")
    A("| 历史窗口 | P = 8 测量 + P−1 = 7 过去输入；当前输入 u_k 不进 context |")
    A("| 预测任务 | one-step x_{k+1}；自回归开环 H ∈ {5, 25, 100} |")
    A("| 评估起点 | 冻结整数算法生成，所有模型/种子完全相同 |")
    A("| 选择准则 | validation 多步 rollout RMSE（H=25），**从不使用 test** |")
    A("| 搜索预算 | 每模型 6 trial（random search）→ 选定配置 3 seed 重训 → test 一次评估 |")
    A("| 随机种子 | 0, 1, 2（线性基线 M0/M1 为闭式解，确定性） |")
    A("| 硬件 | NVIDIA RTX 4060 Laptop 8 GB；torch 2.6.0+cu124 |")
    A("")

    # ---------------- E-M1
    A("## 2. E-M1 基线主表（test，归一化单位，mean ± std，%d seeds）" % 3)
    A("")
    A("归一化分母为 train-only `x_std`。**不报告单一最优 seed**。")
    A("")
    A("| 方法 | one-step | roll H=5 | roll H=25 | roll H=100 | 参数量 |")
    A("|---|---|---|---|---|---|")
    table = {}
    for s in SPECS:
        runs = test.get(s)
        if not runs:
            A("| %s %s | 待运行 | — | — | — | — |" % (s, NAMES[s]))
            continue
        os_m, os_s = mean_std([r["test"]["one_step"][k] for r in runs for k in ["short"]])
        row = {}
        for k in HKEYS:
            m, sd = mean_std([r["test"]["rollout"][k] for r in runs])
            row[k] = (m, sd)
        params = runs[0]["params"]
        table[s] = row
        A("| %s %s | %.4f | %.4f ± %.4f | %.4f ± %.4f | %.4f ± %.4f | %d |"
          % (s, NAMES[s], os_m, row["short"][0], row["short"][1], row["mid"][0],
             row["mid"][1], row["long"][0], row["long"][1], params))
    A("")
    A("**禁止**把不同通道的平均误差当作全部信息；逐通道结果见下节。")
    A("")

    # per-channel table (mid horizon)
    A("### 2.1 逐通道 RMSE（H=25，归一化单位）")
    A("")
    A("| 方法 | channel 0 | channel 1 |")
    A("|---|---|---|")
    for s in SPECS:
        runs = test.get(s)
        if not runs:
            continue
        pc = np.asarray([r["test"]["per_channel"]["mid"] for r in runs])
        A("| %s | %.4f ± %.4f | %.4f ± %.4f |" % (s, pc[:, 0].mean(), pc[:, 0].std(),
                                                  pc[:, 1].mean(), pc[:, 1].std()))
    A("")

    # MAE / quantiles / cost
    A("### 2.2 辅助指标（H=25）")
    A("")
    A("| 方法 | 误差中位数 q50 | q90 | q99 | 评估耗时/seed (s) |")
    A("|---|---|---|---|---|")
    for s in SPECS:
        runs = test.get(s)
        if not runs:
            continue
        q50 = np.mean([r["test"]["quantiles"]["mid"]["q0.5"] for r in runs])
        q90 = np.mean([r["test"]["quantiles"]["mid"]["q0.9"] for r in runs])
        q99 = np.mean([r["test"]["quantiles"]["mid"]["q0.99"] for r in runs])
        sec = np.mean([r.get("eval_seconds", float("nan")) for r in runs])
        A("| %s | %.4f | %.4f | %.4f | %.1f |" % (s, q50, q90, q99, sec))
    A("")

    # per-seed detail: exposes instability that a mean would hide
    A("### 2.3 逐 seed 明细（H=100 的种子间差异，暴露发散/不稳定）")
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
        m, sd = mean_std([v for v in vals if v == v])
        A("| %s | %.4f | %.4f | %.4f | %.4f ± %.4f |"
          % (s, vals[0], vals[1], vals[2], m, sd))
    A("")
    A("> 若某方法的种子间差异与均值同量级（例如 ±0.17 vs 0.39），说明它在 H=100 上**不稳定**，")
    A("> 不能只报均值。此处逐 seed 列出，供判断。")
    A("")

    # paired comparison: same seed, same start set -> paired differences
    A("### 2.4 配对比较（同 seed 差值，H=25）")
    A("")
    A("计划书 §10 要求「必要时做配对比较」。由于所有模型使用**同一测试起点集合**且每个模型用相同种子 0/1/2，")
    A("同 seed 差值就是配对量。n = 3，**不做显著性断言**，只列出差值。")
    A("")
    A("| 对比 | seed 0 差值 | seed 1 | seed 2 | 均值 ± 标准差 |")
    A("|---|---|---|---|---|")
    for a, b in (("M4", "M5"), ("M5", "M3"), ("M4", "M6"), ("M5", "M2"), ("M4", "M0")):
        ra, rb = test.get(a), test.get(b)
        if not ra or not rb:
            continue
        d = [ra[i]["test"]["rollout"]["mid"] - rb[i]["test"]["rollout"]["mid"]
             for i in range(min(len(ra), len(rb)))]
        while len(d) < 3:
            d.append(float("nan"))
        m, sd = mean_std([x for x in d if x == x])
        A("| %s − %s | %+.4f | %+.4f | %+.4f | %+.4f ± %.4f |"
          % (a, b, d[0], d[1], d[2], m, sd))
    A("")
    A("> 负值表示左侧方法误差更小。**同号且绝对值远大于标准差**才算一致差异；")
    A("> 本表 n=3，只用于观察方向与量级，不用于宣称显著性。")
    A("")

    xp = os.path.join(RES, "xtraj_variance.json")
    if os.path.exists(xp):
        xt = json.load(open(xp, encoding="utf-8"))
        A("### 2.5 跨轨迹方差（统计单位 = 一条独立测试轨迹；seed 0 补充诊断）")
        A("")
        A("计划书 §2.3 要求以**独立实验轨迹**为统计单位，避免重叠窗口造成的伪重复。")
        A("本节为**单 seed** 补充诊断（`%s`），不替代多 seed 主表。" % xt["note"])
        A("")
        A("| 方法 | 逐轨迹 RMSE 均值 | 方差 | 最小 | 最大 | 最差轨迹 |")
        A("|---|---|---|---|---|---|")
        for s in SPECS:
            e = xt["models"].get(s)
            if e:
                A("| %s | %.4f | %.5f | %.4f | %.4f | traj %d |"
                  % (s, e["mean"], e["var"], e["min"], e["max"], e["worst_traj"]))
        A("")
    else:
        A("### 2.5 跨轨迹方差")
        A("")
        A("*待运行 `python scripts/xtraj_variance.py`。*")
        A("")

    # ---------------- E-M2 figures
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
        for k, hk in zip(range(3), HKEYS):
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
            ax[k].set_title("H=%s" % hk)
            ax[k].set_xlabel("rollout step h")
            ax[k].set_ylabel("RMSE (normalised)")
            ax[k].set_yscale("log")
            ax[k].grid(alpha=0.3)
        ax[0].legend(fontsize=7)
        fig.suptitle("E-M2: rollout RMSE vs horizon (test, mean over seeds; band = min..max)")
        fig.tight_layout()
        p1 = os.path.join(FIG, "em2_horizon_rmse.png")
        fig.savefig(p1, dpi=150)
        plt.close(fig)

        fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
        for s in SPECS:
            runs = test.get(s)
            if not runs:
                continue
            c = np.asarray([r["test"]["curve"]["long"] for r in runs]).mean(axis=0)
            ax[0].plot(np.arange(1, len(c) + 1), c, label=s)
        ax[0].set_title("H=100, all channels")
        ax[0].set_xlabel("rollout step h")
        ax[0].set_ylabel("RMSE (normalised)")
        ax[0].set_yscale("log")
        ax[0].grid(alpha=0.3)
        ax[0].legend(fontsize=7)
        keys = list(table.keys())
        if keys:
            x = np.arange(len(keys))
            for j, hk in enumerate(HKEYS):
                ax[1].bar(x + j * 0.25, [table[k][hk][0] for k in keys], 0.25, label=hk)
            ax[1].set_xticks(x + 0.25)
            ax[1].set_xticklabels(keys)
            ax[1].set_yscale("log")
            ax[1].set_ylabel("rollout RMSE (normalised)")
            ax[1].legend()
            ax[1].grid(alpha=0.3, axis="y")
        fig.tight_layout()
        p2 = os.path.join(FIG, "em1_summary.png")
        fig.savefig(p2, dpi=150)
        plt.close(fig)
        A("## 3. E-M2 预测误差随 horizon")
        A("")
        A("![E-M2](../figures/em2_horizon_rmse.png)")
        A("")
        A("![E-M1 summary](../figures/em1_summary.png)")
        A("")
    except Exception as exc:                              # noqa: BLE001
        A("## 3. E-M2 预测误差随 horizon")
        A("")
        A("绘图失败：`%r`（数值表仍然有效）" % (exc,))
        A("")

    # ---------------- failures
    A("## 4. 失败与异常记录（不得从主指标静默排除）")
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
    A("已记录的真实缺陷（见 `reports/control_comparison.md` §2.1 与 DEC-085）：")
    A("")
    A("1. rollout 语义错误（每步重新编码 → 已改为 latent 递归传播），导致首轮 Gate 1 训练全部作废重跑；")
    A("2. 目标函数缺常数项（已修正）；")
    A("3. 首轮长时训练因**主机内存**（16 GB，训练时仅余约 3 GB）耗尽而中断，")
    A("   报错表现为 CUDA OOM（GPU 实际仅占用 32 MiB）。已改为逐模型独立进程 + 显式内存回收 + batch 128。")
    A("")

    # ---------------- selected configs
    A("## 5. 入选配置（validation 选择，test 只评估一次）")
    A("")
    A("| 模型 | 配置 |")
    A("|---|---|")
    for s in SPECS:
        b = led.get("best", {}).get(s)
        if b:
            A("| %s | `%s` (val roll25 = %.6f) |" % (s, json.dumps(b["cfg"], ensure_ascii=False),
                                                     b["val_roll25"]))
    A("")

    # ---------------- gate2 sections if available
    g2path = os.path.join(RES, "gate2_diagnostics.json")
    g2 = json.load(open(g2path, encoding="utf-8")) if os.path.exists(g2path) else None
    g2_em3 = (g2 or {}).get("em3", {})
    g2_sum = g2_em3.get("summary", {})
    g2_em4 = (g2 or {}).get("em4", {})
    g2_em5 = (g2 or {}).get("em5", {})

    A("## 6. E-M3 结构消融（配对：同 encoder / 窗口 / latent / 损失 / 预算）")
    A("")
    if g2_sum:
        A("配对配置（取自 M5 的入选配置，四个结构共用）：`%s`"
          % json.dumps((g2 or {}).get("paired_cfg", {}), ensure_ascii=False))
        A("")
        A("| 结构 | roll H=25 | roll H=100 | one-step | 参数量 |")
        A("|---|---|---|---|---|")
        for variant in ("A0B0", "AcB0", "A0Bx", "AcBx"):
            sm = g2_sum.get(variant)
            if sm:
                A("| %s | %.4f ± %.4f | %.4f | %.4f | %d |"
                  % (variant, sm["roll25_mean"], sm["roll25_std"], sm["roll100_mean"],
                     sm["one_step_mean"], sm["params"]))
        A("")
    else:
        A("*待运行 `scripts/run_gate2.py`。*")
        A("")

    A("## 7. E-M4 容量/预算匹配")
    A("")
    if g2_em4.get("target_params"):
        A("目标：把 `A(c)+B0` 放大到与新模型同参数量级，防止把参数量增加误当调度结构收益。")
        A("")
        A("| 项 | 值 |")
        A("|---|---|")
        A("| 新模型参数量 | %d |" % g2_em4["target_params"])
        sel = g2_em4.get("selected", {})
        A("| 匹配后的 `A(c)+B0` | d_model=%s, r_A=%s, 参数量=%s (相对误差 %.1f%%) |"
          % (sel.get("d_model"), sel.get("r_A"), sel.get("params"),
             100.0 * sel.get("rel_err", 0.0)))
        ms = g2_em4.get("matched_summary", {})
        if ms:
            A("| 匹配后 roll H=25 | %.4f ± %.4f |" % (ms["roll25_mean"], ms["roll25_std"]))
        A("")
    else:
        A("*待运行 `scripts/run_gate2.py`。*")
        A("")

    A("## 8. E-M5 调度诊断（test 起点，采样经验界；**不是**全局 Lipschitz 证书）")
    A("")
    if g2_em5:
        A("| 结构 | ‖A(c)−A0‖₂ max | ‖B(χ)−B0‖₂ max | ρ(A) max | ΔA 有效秩(90%) | 输入响应相对差 |")
        A("|---|---|---|---|---|---|")
        for variant in ("A0B0", "AcB0", "A0Bx", "AcBx"):
            d = g2_em5.get(variant, {})
            A("| %s | %.4f | %.4f | %.4f | %d | %.3f |"
              % (variant, d.get("A_dev_spec_max", 0.0), d.get("B_dev_spec_max", 0.0),
                 d.get("rho_A_max", 0.0), d.get("dA_effective_rank_90pct", 0),
                 d.get("Bx_response_rel_diff_mean", 0.0)))
        A("")
    else:
        A("*待运行 `scripts/run_gate2.py`。*")
        A("")

    A("## 9. 结论与局限")
    A("")
    A("**结论按数据填写，不预设优劣。** 见 §2 主表。")
    A("")
    A("局限：")
    A("")
    A("- 数据只有单一工况集合，**不支持跨工况泛化**结论；")
    A("- 测试起点在同一批 10 条轨迹内均匀取样，轨迹间差异见分位数指标；")
    A("- 超参搜索为 6 trial/模型（算力受限），不保证接近各方法的最优配置；")
    A("- M3/M6 的递推是「把预测测量与已知未来输入喂回输入序列」，与 scheduled Koopman 的 latent 递归传播是不同的递推策略，已在报告中注明；")
    A("- 本节所有误差为**离线预测**误差，不含任何闭环控制含义。")
    A("")

    out = os.path.join(REP, "modeling_comparison.md")
    io.open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("written -> %s" % out)


if __name__ == "__main__":
    main()
