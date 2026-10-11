# -*- coding: utf-8 -*-
"""Generate reports/control_comparison.md (Gate 3 / Gate 4 / Gate 5) from raw artifacts.

Inputs (all produced by earlier steps, nothing typed by hand):
  results/control/gate3_unit_tests.txt        (Gate 3 raw output)
  results/control/control_test.json           (Gate 4, test scenarios)
  results/control/control_val_search.json     (Gate 4, sensitivity on validation)
  results/theory_diagnostics/freezing_diagnostics.json   (Gate 5)

Run:  python scripts/report_control.py
"""
from __future__ import annotations

import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
CTRL = os.path.join(EXP, "results", "control")
THEO = os.path.join(EXP, "results", "theory_diagnostics")
REP = os.path.join(EXP, "reports")
FIG = os.path.join(EXP, "figures")


def load(path):
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return None


def agg(runs, plant, ctrl, kind, key):
    """Mean of ``key`` over scenarios of one kind (skips missing)."""
    vals = []
    for name, mm in runs.get(plant, {}).get(ctrl, {}).items():
        if name.startswith("setpoint") == (kind == "setpoint") and key in mm:
            vals.append(mm[key])
    return (sum(vals) / len(vals)) if vals else float("nan")


def main():
    L = []
    A = L.append
    A("# 控制实验报告（WP-C）：Gate 3 / Gate 4 / Gate 5")
    A("")
    A("> **状态**：临时实验材料，**不是论文正文**；本文件由 `scripts/report_control.py`")
    A("> 从 `results/control/*.json`、`results/theory_diagnostics/*.json` 与单测原始输出自动生成，")
    A("> 数值无手工填写。")
    A(">")
    A("> **诚实边界（先读）**：本报告只包含**离线闭环仿真**（控制器输出驱动一个仿真 plant 的下一步状态），")
    A("> **没有**任何真实硬件实验。所有控制结论只对所用 plant 成立。")
    A("> 离线 QP 求解耗时**不等于**闭环控制周期。")
    A("")

    A("## 1. 实验框架与不声称清单")
    A("")
    A("| 类别 | 定义 | 本报告是否包含 |")
    A("|---|---|---|")
    A("| 离线预测回放 | 用真实记录的控制序列评价模型 | ✅（Gate 1/2，见 `modeling_comparison.md`） |")
    A("| 闭环仿真 | 控制器输出影响仿真 plant 的下一步状态 | ✅（§3 Gate 4） |")
    A("| 真实硬件闭环 | 控制器驱动真实执行器并实时获取反馈 | ❌ **未做**，无独立安全审核 |")
    A("")
    A("不声称：闭环稳定性、递归可行性、实时性/截止时间、真实硬件控制、非凸完整问题的全局最优性。")
    A("")
    A("**plant 独立性**：plant A = M3（GRU 受控预测器），plant B = M6（Controlled Transformer），")
    A("与三个控制器的内部模型（`A0/B0`、M4、M5）**属于不同模型族**。计划书禁止的")
    A("「用被测试控制器自身的同一个学习模型当唯一 plant」因此被避免；M5 的**非冻结**完整模型")
    A("只作 sanity 参考，不作唯一 plant。")
    A("")

    # ------------------------------------------------------------------ Gate 3
    A("## 2. Gate 3 — 控制器单元测试")
    A("")
    raw = ""
    p = os.path.join(CTRL, "gate3_unit_tests.txt")
    if os.path.exists(p):
        raw = io.open(p, encoding="utf-8").read()
    m = re.search(r"(\d+)/(\d+) tests passed", raw)
    A("**命令**")
    A("")
    A("```powershell")
    A("D:\\conda\\envs\\edmddl2\\python.exe -u tests\\test_ltv_qp.py   # cwd = 杂项/新版本/Temporary_Experiments")
    A("```")
    A("")
    if m:
        A("**结果：%s/%s 通过。** 原始输出 `results/control/gate3_unit_tests.txt`，" % (m.group(1), m.group(2)))
        A("文件哈希见 `results/control/gate3_hashes.txt`；证据 `EV-GATE3-QP-001`。")
    else:
        A("**结果**：未找到单测原始输出（`results/control/gate3_unit_tests.txt`）。")
    A("")
    A("| 测试组 | 验证内容 |")
    A("|---|---|")
    A("| T1 / T1b / T1c / T1d | 冻结预测矩阵 `Z = F + G U` 与显式冻结 rollout 逐位一致；`F` 为零输入响应；`G[r,r]=B_r`；`G[r,t>r]=0` |")
    A("| T2 / T2b / T2c | 目标函数 `UᵀMU + 2fᵀU + const` 与直接求和一致；解析梯度对有限差分；`M` 对称 |")
    A("| T3 / T3b / T3c / T3d / T3e | OSQP 求解状态；与 **cvxpy 独立参考**目标值/解一致；盒约束满足；紧盒饱和 |")
    A("| T4 / T4b / T4c / T4d | `nominal_rollout` 调度与状态自洽；冻结仿射映射复现冻结 rollout；`B(χ)` 依赖测量状态；`U/V` 列范数 ≤ 1 |")
    A("| T5 / T5b | `A0B0` 调度时域恒定；**LTI 情形冻结模型与完整 rollout 完全一致** |")
    A("| T6 / T6b…T6g | 控制器端到端：首输入有限、QP 求解、代价自洽、盒约束、确定性、warm-start 移位与尾填充、warm-start 确实改变冻结调度 |")
    A("| T7 / T7b / T7c | **latent 递归传播**：一次 rollout 内 encoder 恰好调用 1 次；首步等于 one-step 预测；rollout 依赖未来控制输入 |")
    A("")
    A("### 2.1 单测发现的真实缺陷（已修正并记录）")
    A("")
    A("首轮 19 项中 7 项失败，其中 **2 项是实现缺陷**：")
    A("")
    A("1. **目标函数缺与 `U` 无关的常数项** → `UᵀMU + 2fᵀU` 与直接求和不一致。已让 `cost_matrices`")
    A("   返回 `const`；控制器内 `J_quad` 与 `J_direct` 现逐位一致。")
    A("2. **rollout 语义错误**：原实现对每个预测步重新调用 encoder（re-encoding），使 `z_{i+1}` 不再是")
    A("   `A(c_i)z_i + B(χ_i)u_i` 的结果。`Theory_Package/01` §4.3 与 `06` §2 明确规定 `z` **递归传播**、")
    A("   `X̄_i` 由 `z̄` 的 x 槽位构成；`06` §4 的 `F/G` 推导亦以此为前提。项目论文规则 E 节要求")
    A("   「latent 递归传播与每步重新编码是不同策略，不能混写」。已改为 latent 传播（DEC-085），")
    A("   并新增 T7 断言防回归；**该修正使 Gate 1 全部训练作废重跑**。")
    A("")
    A("### 2.2 与理论的一处已登记差异")
    A("")
    A("计划书 §7.1 把状态代价写成**测量空间** `‖C z_i − x_i^ref‖_Q²`，`Theory_Package/06` §1 写成")
    A("**latent 空间** `‖z_i − z_i^ref‖_Q²`。数据不提供 latent 参考，故实现采用计划书口径；")
    A("已在 `controllers/ltv_mpc.py` 文件头与本报告登记（`ALIGN-001`）。若论文采用 latent 空间形式，")
    A("必须先定义 `z^ref`。")
    A("")

    # ------------------------------------------------------------------ Gate 4
    A("## 3. Gate 4 — 控制场景评估（离线闭环仿真）")
    A("")
    test = load(os.path.join(CTRL, "control_test.json"))
    val = load(os.path.join(CTRL, "control_val_search.json"))
    if not test:
        A("*待运行：`python scripts/run_gate4.py --split test`。*")
        A("")
    else:
        A("**命令**：`python scripts/run_gate4.py --split val --search` → `python scripts/run_gate4.py --split test`")
        A("")
        A("**控制器**：C0 = 固定线性模型（`A0,B0`）+ LTI-MPC；C1 = M4 `A(c)+B0` + 冻结调度 LTV-MPC；")
        A("C2 = M5 `A(c)+B(x)` + 冻结调度 LTV-MPC。三者使用**相同代价权重、相同约束、相同求解器**。")
        A("")
        A("### 3.1 plant 保真度（来自 Gate 1 的 test rollout RMSE）")
        A("")
        A("| plant | one-step | roll H=5 | roll H=25 | roll H=100 |")
        A("|---|---|---|---|---|")
        for pn, pf in (test.get("plant_fidelity") or {}).items():
            if pf:
                A("| %s | %.4f | %.4f | %.4f | %.4f |" % (pn, pf["one_step"], pf["roll5"],
                                                          pf["roll25"], pf["roll100"]))
        A("")
        A("> 闭环结论的强度受此限制：plant 本身的 H=25 rollout RMSE 就是上表的量级。")
        A("")

        runs = test["runs"]["default"]
        A("### 3.2 定点调节（setpoint，3 个目标，100 步 = 20 s）")
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
        A("### 3.3 轨迹跟踪（tracking，3 条轨迹，200 步 = 40 s）")
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
        A("学习到的 plant 只在训练数据分布内可信；控制器把 plant 推出该范围时，结果属于外推。")
        A("")
        A("| plant | 控制器 | 状态越界比例 | 输入越界比例 |")
        A("|---|---|---|---|")
        for pn in runs:
            for cn in ("C0", "C1", "C2"):
                A("| %s | %s | %.3f | %.3f |"
                  % (pn, cn, agg(runs, pn, cn, "tracking", "plant_state_out_of_train_range_frac"),
                     agg(runs, pn, cn, "tracking", "input_out_of_train_range_frac")))
        A("")
        A("u 限幅（归一化）：`%s`（冻结 ±100 物理量）与 `%s`（train 经验范围，敏感性设置 `data_range_u`）。"
          % (json.dumps(test.get("u_limits_normalised", {}).get("frozen")),
             json.dumps(test.get("u_limits_normalised", {}).get("data_range"))))
        A("")

        if val:
            A("### 3.5 敏感性分析（validation 场景，权重对三个控制器**同时**改变）")
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
            A("> 该表用于检验排序是否依赖某一组权重；**不用于挑选用权重**。主比较使用 `default`。")
            A("")
        else:
            A("### 3.5 敏感性分析")
            A("")
            A("*待运行 `python scripts/run_gate4.py --split val --search`。*")
            A("")

    # ------------------------------------------------------------------ Gate 5
    A("## 4. Gate 5 — 理论—实验交叉核验（冻结调度误差）")
    A("")
    fr = load(os.path.join(THEO, "freezing_diagnostics.json"))
    if not fr:
        A("*待运行：`python scripts/run_gate5.py`。*")
        A("")
    else:
        A("**定义（计划书 §9）**：对**同一个候选输入序列** `U` 与名义序列 `Ū`：")
        A("")
        A("- `z_full(U)`：每一步重算 `A(c_i), B(χ_i)`；")
        A("- `z_fr(U; Ū)`：先用 `Ū` 做名义 rollout 得到 `Ā_i, B̄_i`，再在候选 rollout 中冻结。")
        A("")
        A("**不得**把两个控制器各自轨迹的差异称为冻结误差。")
        A("")
        A("模型 `%s`，时域 H=%d，起点数 %d。" % (fr["model"], fr["horizon"], fr["n_starts"]))
        A("")
        A("| ‖U−Ū‖ 水平 | 实测 ‖U−Ū‖ | max‖z_full−z_fr‖ | max‖c_full−c̄‖ | ‖A_full−Ā‖₂ max | ‖B_full−B̄‖₂ max | 代价差 max |")
        A("|---|---|---|---|---|---|---|")
        for r in fr["deltas"]:
            A("| %.2f | %.3f | %.3e | %.3e | %.3e | %.3e | %.3e |"
              % (r["delta"], r["u_mismatch_mean"], r["z_err_max_max"], r["c_err_max"],
                 r["A_dev_spec_max"], r["B_dev_spec_max"], r["cost_gap_max"]))
        A("")
        tc = fr["theory_checks"]
        A("**理论一致性检查**")
        A("")
        A("- P1（`U = Ū` 时冻结误差恒为 0，07 §2：驱动量是输入不匹配而非 δ_A/δ_B 本身）：**%s**"
          % ("成立" if tc["P1_zero_mismatch_gives_zero_error"] else "不成立"))
        A("- P2（冻结误差随 ‖U−Ū‖ 增长）：**%s**" % ("成立" if tc["P2_monotone_growth"] else "不成立"))
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

    A("## 5. 未验证项与待确认问题")
    A("")
    A("- `u_limit = ±100` 仅来自旧部署配置，**尚未由用户确认**（Q3）；所有控制结论以此假设为前提，")
    A("  并额外给出 `data_range_u` 敏感性设置以隔离外推影响。")
    A("- 未做真实硬件实验；无急停/传感器异常/控制超时回退的实测。")
    A("- 控制权重为**先验固定**（`configs/control_protocol.yaml`），另做敏感性分析；")
    A("  不以控制器相对优劣为准则调参。")
    A("- C3（完整非线性 MPC）与 C4（多次调度更新）未实现，原因已登记在 `configs/control_protocol.yaml`，")
    A("  **不是**被静默丢弃。")
    A("")

    out = os.path.join(REP, "control_comparison.md")
    io.open(out, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print("written -> %s" % out)


if __name__ == "__main__":
    main()
