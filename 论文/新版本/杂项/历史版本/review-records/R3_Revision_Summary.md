# 六章论文 R3 精修记录

2026-10-19。依据用户附件 `Transformer_Koopman_R2_Review_20261019.md`，从真实 R2 另存精修；不重新规划论文或扩展理论路线。

## 修改：原问题—目的—替换

| 位置 / 审稿项 | 原问题与目的 | R3 内容 |
|---|---|---|
| IV.B、附录 B / P1.1 | B-EXACT 是内部标签，论文感不足 | 全文去掉该名称，直接说明冻结预测沿名义输入序列与完整 rollout 一致；仍明确任意候选仅首步一致，不将性质扩大 |
| IV.B / P1.2 | proof object 像证明笔记 | 改为辅助完整轨迹仅用于分析，不在下一采样的唯一名义 rollout 之外额外计算 |
| 主定理、证明、推论、附录 C / P1.3 | 状态上界不能直接反推价值上界，原稿没有把已有推导显式连接 | 在原 `eq:squared_tracking_bound` 明确定义 Xi_k，并写成 `||e_k||_Pi^2 <= W_k <= Xi_k`；正文证明明确由标量递推得 `W_k<=Xi_k`；输入推论明确串起 `Jhat<=W_k+delta_k<=Xi_k+delta_k`；附录使用同一定义，保留当期 delta_k |
| 定理前、附录 B/C / P1.4 | epsilon 定义在定理证明内部，读者需要回找 | d_j、tau_ref、epsilon 的精确定义统一放到附录 B；A/B 保留附录 C；定理前给出精确公式和附录入口。正文保留误差递推、尾下降、实际值下降和比较主线，不新增小节或恢复常数清单 |
| III.B / P1.5、P2.6 | 需要一致表达可构造性边界；末句含旧路线元叙述 | 删除 competing finite-history error hypothesis；明确命题构造非空受约束模型类，不保证任意训练结果属于该类，小残差与收缩同时成立仍是独立适用条件。原多步误差估计保留 |
| 附录 A / P2.8 | 示例 gamma 与调度 gamma_A/gamma_B 容易混淆 | 特征标量统一改为 alpha_d，涵盖特征定义、矩阵行和编码图等式；调度符号不改 |
| 导言区 / 引擎意见 | 旧 XeTeX 字体文件无检查，缺失时直接失败 | 固定本轮实际验证路线为已有 Tectonic 0.17.0；四个 Termes 资源完整可用时优先，否则回退到系统 Times New Roman 的命名 OpenType 字体。mathsf 优先 TeX Gyre Heros，缺失时用 Arial。无新包/依赖，保留 IEEEtran 必需的预类字体声明 |
| 附录 B/C / P2.7 | 移动常数后应避免重复膨胀 | 压缩已在主证明给出的域保持/名义一致性重复解释；不删严格凸性、冻结差、tail、成本连续性或比较推导 |

## 数学与范围核验

- 六章与小节数 `[0,2,2,2,0,0]`、三附录、一个主定理、一个在线算法和原理图不变；定理前源码仍为 53 行。图、全部 26 条文献、全部 79 个标签接口与 R2 一致。
- 对照 R2 的 57 个带标签公式块：55 个规范空白后内容相同，包括移至附录的 d_j/epsilon；仅两块变化：显式加入已有价值上界/Xi_k、示例系数改名。没有新增假设或控制律。
- 正文仍分析实际逐轮重新冻结的 W_k：任意候选首步一致→名义输入序列全程一致→shift 实际返回序列加绝对参考 tail→初始 wbar/中间 etabar/尾部 lambda*d_(N-1)→值下降仅加 delta_k→价值比较和标量递推。
- 完整非重复 q/F、统一域和全部名义冻结系数量词、独立残差、参考相对增量、beta Pi、仅输入硬约束与一次 rollout/freeze/QP 不改。N=1、精确参考权重、四误差全零条件与当前输入 gap 保留。
- Main、首版、R2、V3 A/B/C/D/IEEE 原件保留；未改训练/控制代码、checkpoint、实验或原图片。第 V 章仍无结果，不是完整投稿稿；不宣称当前模型、plant、安全或实时性已认证。

## 实际验证

1. Node 静态检查通过：79 个唯一标签、72 处 ref/eqref、26 个引用键与 bibitem 完全对应；环境/括号/UTF-8、旧标签保留、内部术语删除、Xi 定理/证明/推论/附录连接及公式差异检查通过。
2. 最终真实 R3 源连续两次执行已有 Tectonic 0.17.0，参数为 `--only-cached --keep-logs --keep-intermediates --outdir <build>`，退出码均 0，生成 **9 页 PDF**。两次最终引擎日志均为 0 致命错误、0 未定义引用、0 缺字、0 字体加载失败、0 Overfull；各保留 **9 条 Underfull**。没有抑制警告来伪装通过。
3. 正常构建实际选择 **TeX Gyre Termes + Arial**。另外使用临时测试入口模拟 `texgyretermes-regular.otf` 不存在，输入同一最终 R3 源、不改源或缓存，实际走 **Times New Roman + Arial** 回退并编译成功，9 页、0 未定义引用/缺字/字体加载失败/Overfull；该测试副本不是交付 PDF。
4. 用已有 uv Python 3.11 和缓存 pdfminer/pypdfium2 提取/渲染并查看最终 PDF 第 1–9 页，核查框图、定理/推论、常数入口、附录与文献，没有可见裁切越栏。
5. Main 与 V3 A/B/C/D/IEEE 哈希保持原合订本绑定，首版与 R2 TeX/PDF 哈希保持旧交付；内层 Git 的受跟踪文件 diff 为空，无提交或推送。
6. 独立 strict 复审返回 **go，findings=[]**（`ses_eabedc5cbffeKrd13cN71e0tcC`）。reviewer 独立核读 R3/R2 全文、修订记录、Task/项目规则及相关 V3-C/D，核对 Xi 价值递推、当期 delta、常数入口和数学边界。附件及临时日志访问受限、工具不支持 PDF；其编译/字体回退/版面/哈希/Git 结论采用主 Agent 实际证据，未自行复编或视觉核验。

证据目录：`C:/Users/12187/AppData/Local/Temp/opencode/sixsection-r3-build/` 内有两次 console/log、aux、提取文本和逐页 PNG；相邻 `sixsection-r3-fallback-build/` 保留回退测试 console/log/PDF。

### 实际编译边界

- 本轮只实际运行 **Tectonic 0.17.0 / XeTeX**，没有运行独立 XeLaTeX、pdfLaTeX 或 LuaLaTeX；附件对 R2 的 pdfLaTeX 结果不是主 Agent 本轮证据。
- 字体资源检查改善了缺失回退，但系统回退仍要求已安装 Times New Roman/Arial；当前缓存没有 Heros，故未实际测试其优先分支。Times New Roman 回退以普通正体代替 small caps，不能保证与 Termes 完全同版。
- Fontconfig 默认配置缺失、缓存算法包注释 UTF-8 和 Windows 字体绝对路径警告仍在。没有安装包或修改系统字体/缓存，也不声称在所有机器/引擎可编译。
- 这是条件理论写作精修与静态/实际排版核验，不是形式证明、外部学术同行评审、全量文献核验或真实模型适用性认证。

## 文件绑定

| 文件 | SHA256 |
|---|---|
| R3 TeX | `18bb80f90f937849ea7f476d5414865e2cb5dd830f2cc6b75e4a7cb294858c58` |
| R3 PDF | `0303da09f95ecbe56d5345992f87171c4d2290df1da87e35a8dbc23f5677a19f` |
| 未改 R2 TeX | `8c2291ef079ee0588795865420bfe7fef1052f261c1f9d2809186748fb7b686c` |
| 未改 Main.tex | `1ee01187dfdad058746fe9fb3e2489c467b96de09ead0ef67be7a3f2855aee69` |
