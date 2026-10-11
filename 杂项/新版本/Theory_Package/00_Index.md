# 00 — Theory_Package 装配索引（阶段八）

> **本文件的性质**：前期工作的**装配索引与自检记录**。它描述 `01`–`09` 九件套的清单、依赖关系、禁止清单扫描结果与复现方法。
>
> **状态**：前期材料，**不是论文正文**；不含实验数值；**不进论文**（REQ-002 / BA-003）。
>
> **权威来源**：用户计划书 `杂项/新版本/Transformer_Scheduled_Koopman_MPC_Research_Plan.md`（冲突以计划书为准，`DEC-079`）；任务契约见 `ARCH-002`（done_when 只在那里）；材料布局见 `ARCH-001`。
>
> **本阶段禁止事项**（计划书 + REQ-002）：不动论文的摘要 / Introduction / 实验 / 标题；不使用「bilinear Koopman」名称；不声称实时性、闭环稳定性、递归可行性。`DEC-079`（术语与次优性形式）、`DEC-080`（谱范数）、`DEC-081`（文献调研降级为尽力而为）、`DEC-082`（阶段七 plant 未定时的临时口径）。

---

## 1. 九件套清单

| # | 文件 | 字节 | sha256（前 16 位） | 内容 |
|---|---|---|---|---|
| 01 | `01_Model_Definition.md` | 9874 | `da6456a4173846fa` | 模型定义、context 与窗口约定（`u_k` 不进 context）、$A(c)$/$B(\chi)$ 的低秩调制形式 |
| 02 | `02_Assumptions.md` | 7561 | `920565ddf5d80211` | A1–A5 假设、常数对应关系、**不声称**清单 |
| 03 | `03_Low_rank_Boundedness.md` | 5121 | `bd99786ff274510f` | 命题 1：$\|A(c)-A_0\|_2\le g_A$、$\|B(\chi)-B_0\|_2\le g_B$（**有界性，非稳定性**） |
| 04 | `04_Scheduling_Lipschitz.md` | 6841 | `6f59b55aee8712a3` | 命题 2：$L_A$、$L_B$ 的显式表达与证明 |
| 05 | `05_Prediction_Error_Bound.md` | 10853 | `af556ab4b888bfee` | 定理 1：开环有限时域预测误差界、$L$ 的定义 |
| 06 | `06_Frozen_LTV_QP_Proof.md` | 11848 | `739dc7f8f9f32e74` | 冻结 LTV 问题、命题 4：$H=2(G^{\mathsf T}\bar QG+\bar R+\hat D^{\mathsf T}\bar S\hat D)\succeq0$、§6 第 8 条 $c_0$ |
| 07 | `07_Freezing_Error_Bound.md` | 11157 | `05c8dcaaea323630` | 定理 2：同一输入序列下完整 vs 冻结 rollout 的误差界、三对象区分、$\delta_{\mathrm{frz}}$、§7 第 3 条 |
| 08 | `08_Conditional_Suboptimality.md` | 10010 | `aeb9f5f4d88b75d3` | 定理 3：条件次优性 $0\le J_{\mathrm{full}}(u^{\mathrm{fr}})-J_{\mathrm{full}}(u^\*)\le 2\varepsilon_J$、$\varepsilon_J$ 显式化 |
| 09 | `09_Reference_List.md` | 25896 | `90b7960e37449cbd` | 四主题文献清单（支撑 / 竞争 / 待核实）、controlled Koopman 代理的合理性论证、旧稿参考文献核对 |

**辅助文件**（不属于九件套，但同目录）：
- `00_assembly_scan.py` — 本索引的**可复现扫描器**（只用标准库）。
- `00_assembly_scan.txt` — 扫描器的原始输出（由脚本以 UTF-8 自行写出，不经 shell 重定向）。

> 清单中的字节数与 sha256 由 `00_assembly_scan.py` 每次运行重新计算，**完整哈希见 `00_assembly_scan.txt`**。上表数字对应 `00_assembly_scan.txt` 的 `scanned` 时间戳。

---

## 2. 依赖与交叉引用

由 `00_assembly_scan.py` 扫描每件里 `` `NN` `` 形式的引用，**全部指向存在的件，无悬空引用**（`dangling internal refs: none`）：

```
01_Model_Definition.md             -> 03
02_Assumptions.md                  -> 01,03,04,05,06,07,08
03_Low_rank_Boundedness.md         -> 01
04_Scheduling_Lipschitz.md         -> 01,02,03,05,07
05_Prediction_Error_Bound.md       -> 01,02,03,04
06_Frozen_LTV_QP_Proof.md          -> 01,02,04,06,07,08     （含自引，属正常）
07_Freezing_Error_Bound.md         -> 01,02,03,04,05,06,08
08_Conditional_Suboptimality.md    -> 01,02,03,04,06,07
09_Reference_List.md               -> 01,02,03,04,06,07,08
```

逻辑依赖链（与 `ARCH-002` 的 `depends_on` 一致）：

```
01 → 02 → 03 → 04 → 05 ─┐
                        ├→ 06 → 07 → 08
                    01/02┘
09 独立（文献），但 §2 的论证引用 03/04 的结论
```

件外引用（**核对方式分三种，如实标注**：`00_assembly_scan.py` 只对 `notes/literature/*` 与 `validation/*` 做 `exists?` 存在性核对；`论文/` 它只报告「被提及」不核对；`citation_audit_report.md` / `_audit_bib.json` **不在扫描器覆盖内**，由主 Agent 用 glob 另行核对）：

| 被引路径 | 出现在 | 存在性核对方式 |
|---|---|---|
| `notes/literature/`（检索日志与旧稿引用扫描） | `09` | 扫描器 `exists?` 全部 True |
| `validation/`（临时验证脚本与结果） | `07` | 扫描器 `exists?` 全部 True |
| `论文/`（用户备忘与旧稿） | `01`、`09` | 扫描器只报告「被提及」；由 §4 的 mtime 清单佐证 |
| `citation_audit_report.md`、`_audit_bib.json`（既有 strict 审计） | `09` | **扫描器不覆盖**；主 Agent 用 glob 核对，两者均存在 |

> **口径说明（重要）**：§2 的引用图只统计 `` `NN` ``（两位数字）形式的引用，因此是**部分图**。九件套中另有多处**完整文件名**互引（例如 `01` §8 → `02`/`03`/`04`/`06`，`02`/`03` 的接口表 → `04`–`08`）；独立复核者逐一核对这些完整文件名，**目标全部存在**，故按更宽口径亦**无悬空引用**。

---

## 3. 禁止清单扫描

**扫描口径**：对九件套逐行匹配 `bilinear/双线性`、`real-time/实时/截止时间/deadline`、`closed-loop stability/闭环稳定/递归可行/recursive feasibility`、`摘要/abstract`、`Introduction`、`实验/experiment`、`标题/title`。分类器**故意保守**（只看关键词前 40 / 后 20 字符内的否定标记），因此会有假阳性，未分类命中**逐条人工裁定**（下表）。

**结果**：`TOTAL hits=43, unclassified=9`。9 处未分类命中的裁定：

| 文件:行 | 关键词 | 原文要点 | 裁定 |
|---|---|---|---|
| `01`:143 | bilinear | 「把 $(c_k,\chi_k)$ 视为外部调度信号时，本模型是**调度线性**的……只有当把 $u$ 与 $z$ 的乘积项显式……」（技术澄清句） | **非声称**：陈述模型结构，未主张「本文即 bilinear Koopman」 |
| `01`:148 | bilinear | 「旧路线文件中的 bilinear 框架**推迟**到论文阶段由用户裁决，**不是**被判为错误（`DEC-079`）」 | **登记**：否定标记在窗口之外 |
| `02`:85 | closedloop | 表格行「递归可行性 \| 同上」——上一行是「计划书禁止清单明确排除」 | **否定**：跨行表格引用 |
| `02`:86 | realtime | 表格行「实时性 / 满足截止时间 \| 同上；且本阶段没有任何计时数据」 | **否定**：同表 |
| `07`:218 | experiment | 「前者可由输入序列直接算出，后者只能由数据或辨识实验界定」 | **非声称**：描述模型误差项的来源，非实验结论 |
| `09`:31 | bilinear | §0 命名提示：说明形式上的族属关系，并明确「本阶段**不使用**「bilinear Koopman」」 | **否定** |
| `09`:115 | bilinear | 小节标题「关于「双线性 Koopman」与计划书 §6.1 的那篇文献」 | **术语讨论**：标题本身是讨论对象 |
| `09`:117 | bilinear | 引述计划书 §6.1 用户原话 | **引述** |
| `09`:202 | bilinear | 「计划书 §6.1 所指「双线性 Koopman 论文」的**具体身份**」 | **未决问题** |

**结论：无任何肯定式越级声称。** 其余 34 处命中均为显式否定句（如「不声称闭环稳定」「不作任何实时性声称」「不含实验数值」）或禁止清单本身的引用。

**硬标记**（论文专用结构，九件套中必须不存在）：

```
\begin{abstract}         ABSENT
\section{Introduction}   ABSENT
\title{                  ABSENT
\maketitle               ABSENT
```

---

## 4. 论文目录未被改动（git 层面）

本阶段**未**修改 `论文/` 下任何文件。核验方式与结果见 `TASK-041` 的证据（主 Agent 执行）：

- `git rev-parse --short HEAD` → `65f7bbe`（分支 `paper`）；
- `git status --porcelain -- 论文` → **空**（零改动）；
- `git status --porcelain` → 仅三个未跟踪目录：`杂项/新版本/Theory_Package/`、`杂项/新版本/notes/`、`杂项/新版本/validation/`。

`00_assembly_scan.py` 另输出 `论文/` 全部文件的 mtime 供交叉参考（最近的 `论文/老版本/Main.tex` 与 `Main.pdf` 为 2026-10-10 21:04，早于本阶段的工作时间；`论文/新版本/新版本.txt` 为用户备忘，2026-10-10 16:46）。

---

## 5. 复现方法

```bash
D:\conda\envs\vibe-coding\python.exe 00_assembly_scan.py
```

脚本只用标准库，自行以 UTF-8 写出同目录的 `00_assembly_scan.txt`，并打印一行 `ok`（含 `unclassified=` 计数）。**不要**用 shell 重定向到该文件（PowerShell 控制台编码会污染中文）。

件内自检与数值复现见：
- `../notes/literature/02_ref_scan.py` — 旧稿参考文献扫描（`09` §3 的全部数字）；
- `../validation/validate_theory.py` — 理论包的数值验证（种子 20261011；含两条自检）。

---

## 6. 未解决项与登记项（汇总）

| # | 事项 | 位置 | 状态 |
|---|---|---|---|
| 1 | **被控对象（plant）未定** —— `TASK-040` 的 `done_when#1` 因此未达成 | `validation/results.md` §6；`DEC-082`；`REQ-002` open_items | **阻塞于用户**（唯一阻塞性 C 级问题） |
| 2 | 计划书 §6.1 所指「双线性 Koopman 论文」的具体身份未定（检索未找到唯一对应物） | `09` §2.4、§4 第 5 条 | 待用户提供线索 |
| 3 | 旧稿参考文献的 4 个遗留点：55(报告)/50(json)/52(当前) 三快照关系无法判定；报告 44 条 PASS 未逐条留快照；`han2024robust` 与 `shenoy2025temporal` 从未被审计；历次编辑后引用↔主张对应未重核 | `09` §3.4 | 论文阶段处理 |
| 4 | `09` §1 中仍标 `待核实` 的条目（T2-3、T2-4、T3-3、T3-5 的 5 个草稿键） | `09` §1、§4 | 论文阶段逐条核对 |
| 5 | `09` 的 `01_search_log.md` 一处并集措辞（「核对宇宙 = 52 ∪ 11 = 63」，按并集读应为 59） | `../notes/literature/01_search_log.md` | 复核者判**非阻塞**，按项目惯例只登记不改字节 |
| 6 | `validation/replay_counterexample.py` 硬编码系统临时目录路径 | `../validation/replay_counterexample.py:17` | 复核者判**仅登记**（改它会使其字节失效） |
| 7 | 08 的 N1–N5 编辑性遗留。**位置列偏窄**：按 `REV-TASK039-003`，N1–N5 还含跨文件项（`07` 的 validation 相对路径、`02` A1 的三对象命名） | `08_Conditional_Suboptimality.md`（并涉 `07`、`02`） | 复核者判**非阻塞**，为避免使已复核字节失效而不改 |
| 8 | `01` L139 把用户备忘路径写作 `论文/新版本.txt`，实际为 `论文/新版本/新版本.txt`（少一级） | `01_Model_Definition.md` | 复核者判**仅登记**；不改 `01` 以免使其已复核字节（`EV-TASK034-MODEL-002`）失效 |
| 9 | `09` §0/§2.3 的「本工作引入的扩展」属**尽力而为检索下的新颖性表述**，与 §5「没有对优先权作判断」有轻微张力 | `09_Reference_List.md` | 复核者判**仅登记**；`09` §2.3 已要求论文写成 "introduced in this work" |

---

## 7. 本阶段**没有**做的事（避免误读）

- 没有写论文：未改摘要 / Introduction / 实验 / 标题，未新建 `.bib`，未改 `Main.tex`（§4 有 git 层面核验）。
- 没有声称 bilinear Koopman / 实时性 / 闭环稳定性 / 递归可行性（§3 有逐条扫描与裁定）。
- 没有把 `validation/` 的任何数值写进 `01`–`09`（临时验证结果不进论文，也不进理论包）。
- 没有对文献的**实验设置、结果数字或优先权**作判断（`09` §5）。
- 没有做被控对象（plant）的任何物理声明（§6 第 1 条）。
