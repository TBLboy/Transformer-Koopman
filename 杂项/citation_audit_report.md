# Main.tex 全量引用支撑审计报告（P2-15）

- 任务：TASK-006（strict） / 决策：DEC-030 / 证据：EV-PHASE2-CITATION-AUDIT-002
- 审计对象：`Transformer-Koopman/论文/新版本/Main.tex` 参考文献区（原 L855–L1046）
- 审计方法：程序化抽取全部 bibitem 与正文引用键 → 6 个并行 research 子代理按批次逐条与 Crossref / OpenAlex / arXiv / 出版社页对拍 → 主代理对两处 FAIL 独立复核
- 结果：**63 条 → 55 条；55 条全部被正文引用；0 条未引用；重编译 0 undefined citation**

---

## 1. 删除的条目（8 条）

### 1.1 不存在的条目（FAIL，必须删）

| key | 判定 | 说明 |
|---|---|---|
| `yuan2022variational` | **伪造/拼合** | "Variational Koopman models" 标题前缀来自 Wu et al., *J. Chem. Phys.* 146(15) 154104, 2017；"uncertainty quantification" 概念来自 Morton et al.；声称的作者与卷期页 IEEE TAC 67(11) 5905–5920 **均不存在**。该条**在正文中被引用**（CTX 44 附近 "data-driven methods learn the representations instead" 引用簇），已同时从引用簇中移除 |
| `rank2019recurrent` | **不存在** | 无任何数据库记录；且从未被引用 |

> 若作者本意是引用 Wu et al. 2017 的 variational Koopman 工作，可另行补入正确的 bibitem 并加引用。

### 1.2 从未被引用的条目（dead entries，删）

`brunton2016sindy`、`zeng2023transformers`、`liu2024itransformer`、`forootani2026compact`、`forootani2025synthetic`、`katharopoulos2020transformers`

> `forootani2026compact` 与 `forootani2025synthetic` 是**真实存在**的工作，但从未被正文引用；如需覆盖相关主题，必须连同实际引用一起重新加入。

---

## 2. 元数据修正（10 条）

| key | 修正内容 |
|---|---|
| `morton2019deep` | 页码 5113–5119 → **3173–3179** |
| `klus2018data` | 作者名单补全为真实 7 人：S. Klus, F. Nüske, P. Koltai, H. Wu, I. Kevrekidis, C. Schütte, F. Noé |
| `forgione2021dynonet` | 页码 612–629 → **612–626** |
| `nelles2020nonlinear` | 副标题补全为 "Neural Networks, Fuzzy Models, and Gaussian Processes" |
| `kamb2020timedelay` | 补卷期页：**vol. 19, no. 2, pp. 886–917** |
| `han2020deep` | 由 arXiv 预印本升级为**正式发表版**：Proc. IEEE CDC 2020, pp. 1890–1895 |
| `mezic2005spectral` | 补 issue：**no. 1–3** |
| `otto2021koopman` | 补 issue：**no. 1** |
| `das2019delay` | 补 issue：**no. 6** |
| `ljung1999system` | 出版社 imprint 改为 **Prentice Hall PTR** |

---

## 3. 引用键与主张支撑修正（2 处）

1. **引用键年份不一致**：`forootani2026deepkoopformer` → **`forootani2025deepkoopformer`**（正文 `\cite` 与 `\bibitem` 同步修改）。
2. **主张支撑错配**（CTX 44）：原文把"高效注意力变体"与"patch tokenization"混为一谈，声称这些工作都"通过聚合局部时序结构提升效率"。改为两句：
   - 高效注意力变体与分解类模型（`zhou2021informer`, `wang2020linformer`, `choromanski2021performer`, `wu2021autoformer`, `zhou2022fedformer`）降低长序列建模成本；
   - patch-based tokenization（`nie2023time`）在全局注意力之前聚合局部时序结构。

---

## 4. 审计后状态

- 参考文献：**55 条，全部被引用，无 dead entry**
- 编译：`build/Main.pdf`，**12 页**，0 undefined reference / 0 undefined citation（仅 4 条已知 TU/ptm 字体探测警告）
- 产物指纹：
  - `Main.tex` sha256 `0DA30C3EDC56`（80917 B）
  - `build/Main.pdf` sha256 `A2510E4B9573`（297113 B）
- 未改动：全部科学内容、理论、数值、文档结构；剩余 55 条的键名与顺序

## 5. 审计边界

- 本报告只覆盖 `Main.tex` 的参考文献条目与"引用—主张"对应关系，**不覆盖**正文非引用类事实主张的正确性。
- 44 条未标记条目在本轮对拍中判定 PASS（元数据与主张支撑均无问题），但未逐条记录对拍快照；如需可复现的逐条证据链，需要二次取证。
