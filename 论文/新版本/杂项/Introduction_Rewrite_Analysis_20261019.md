# 引言论证链重写：参照分析与修改记录

2026-10-19。修改对象：当前活跃 `../Main.tex` 的 Introduction 文字、贡献列表；不是重写理论，也不是只增加连接词。原理图起始处至文末、引言之前的摘要/前言均逐字不变。

## 1. 实际阅读的原论文及组织方式

以下评价是本次对引言组织的分析，不把论文的所有主张自动当作已证事实。访问日期均为2026-10-19。

| 原论文/证据 | 实际阅读范围 | 论证组织及本次取舍 |
|---|---|---|
| Korda & Mezić, *Linear predictors for nonlinear dynamical systems: Koopman operator meets model predictive control*, Automatica 93 (2018), 149–160；https://arxiv.org/html/1611.03537 | 原文HTML §1全文，以及§3.1–3.2/§4有关受控EDMD与DMDc区别的说明 | 先定义所需的预测器及“为什么要线性结构”，再解释lifting为何能提供这种结构，接着受控扩展/数值构造，最后落到MPC在线优化。借鉴“先有控制用途，再有Koopman结构”；不把它表述成凭Koopman解决部分观测。原文明确受控EDMD也构造有限维近似，因此不能附和“带输入的模型一律不能有限维化”。 |
| Liu et al., *Koopa: Learning Non-stationary Time Series Dynamics with Koopman Predictors*, NeurIPS 2023；https://arxiv.org/html/2305.18803 | 原文HTML §1全文，§4 Time-variant KP说明 | 从预测任务进入非平稳性这个具体困难，再引出动力学视角，最后以不同分量/局部算子回应困难；不是先列工具再找问题。借鉴“每个模块必须回应上一段留下的具体困难”；仅引用其context-aware forecasting，不将其当作闭环MPC证明。 |
| Li et al., *MamKO: Mamba-based Koopman operator for modeling and predictive control*, ICLR 2025；https://proceedings.iclr.cc/paper_files/paper/2025/file/e99847f8d8006806fd35d6f536136c0d-Paper-Conference.pdf | 官方PDF下载后用已有pdfminer提取，§1全文、§2相关段及§3.2历史矩阵生成与非凸性说明 | Koopman结构的控制便利→固定参数化的表达需求→数据生成矩阵→MPC。借鉴“新增灵活性须同时解释控制代价”；不照搬其LLM泛论、不沿用无条件有限维线性化说法，也不将其已知历史矩阵生成与本文候选内递归更新混为一谈。 |
| Forootani et al., *DeepKoopFormer*, npj Artificial Intelligence 2,35 (2026)；https://www.nature.com/articles/s44387-026-00085-3 | 官方HTML Introduction全文 | 预测需求→时序网络→结构化动力学→Transformer与传播器分工。借鉴“表示学习与演化模型承担不同职责”；原文有重复动机段和大量贡献项，本次不模仿这些写法，不移用其优越性/稳定性/首创断言。 |

**未冒充引言精读的资料：** Shenoy等ACC2025论文只在TUHH官方出版页核对摘要（https://tore.tuhh.de/entities/publication/af31dc8a-e981-424a-97f7-9a62137effb3），用于确认TCN/LSTM/GRU时序编码与控制任务，不计入上述原论文引言阅读。Cisneros的quasi-LPV论文使用出版/作者机构摘要核对迭代QP的定位，不声称本轮已精读其引言。

EDMD/DMDc另核对原作者arXiv记录：Williams等 https://arxiv.org/abs/1408.4408 ，Proctor等 https://arxiv.org/abs/1409.6358 。前者需要快照对和观测字典构造算子近似，后者着重区分内在演化与外部驱动作用；二者不是“有限维化方法”和“加控制输入方法”的同义词。

## 2. 原问题—修改目的—替换逻辑

原稿的问题不是句子短，而是换了讨论对象却没有说明换题原因：先部分观测，随后无限维算子，接着神经网络，又切到调度和闭环。读者不知道每一步解决哪一个需求。

新引言按六个段落承担以下责任，随后给贡献与导航：

1. **定义控制任务的双重要求。** MPC需要比较候选输入的未来效果；识别得到的预测器既需要信息充分的初始化，也需要便于在线优化的演化结构。第二段因此有明确入口，而不是先抛出隐藏状态问题后突然讲线性化。
2. **解释为什么选Koopman结构，以及结构如何落地。** 从矩阵演化的控制便利引出lifting；有限维字典是计算需要，EDMD承担近似，外部输入通道是受控建模的另一层要求；DMDc/controlled EDMD分别给出对应引用。字典选择决定结构是否实用，因此再引入学习坐标，不以一句空泛accuracy总结跳题。
3. **指出学坐标仍无法补足缺失输入信息。** 若同一测量对应不同后续响应，任何仅以该测量为输入的映射无法区分；由此自然引出历史、delay/recurrent/Transformer提升。这里只说历史可提供额外信息，不假设有限历史必然可观测或重构真实状态。
4. **区分历史进入初值与历史进入转移。** 有限参数模型可用数据相关矩阵增加表达灵活性，已有Koopa/MamKO说明这一路线；本文递归预测时历史还会随候选输入变化，故固定context的线性不能推出整体优化凸性。这是后续冻结的明确原因，不声称所有固定算子都失败。
5. **从候选耦合引出冻结，再说明冻结未解决的跨轮问题。** 一次名义rollout提供固定系数形成QP；下一采样重编码/重新生成矩阵，单个冻结问题内的下降不能直接跨轮复用。RTI引用仅说明保证依赖特定更新规则，不把所有QP方法混称RTI，不宣称文献从未研究稳定性。
6. **给出本文一一对应的回应。** history lift/caches→递归调度；一次冻结→一次QP；完整增广成本和参考相对增量→shift实际输出加参考tail→跨轮值比较；可构造公共收缩族与独立重编码/参考残差条件共同构成适用边界。

贡献三项仍对应模型、控制律、条件闭环分析，不将常规Transformer或训练技巧宣称首创，不新增实验结论。没有新增或修改文献条目/引用键。

## 3. 文件与核验

- 修改文件：活跃 `../Main.tex` 的 Introduction 文字/贡献，以及相应重新编译的 `../Main.pdf`。引言之前、从原理图开始到全文结束的字节分别与备份一致，图/公式/文献/方法/定理/实验无改动。
- 修改前Main与PDF保存在 `历史版本/pre-introduction-rewrite-20261019/`，没有在论文根部增加候选版本。
- Node检查：79个唯一标签、73处ref/eqref、26引用键均有对应bibitem且全部使用；括号、环境和非引言不变检查通过。
- 对最终源用已有Tectonic0.17.0 `--only-cached` 连续编译两次，exit0；10页，最终log各为0致命错误/未定义引用/缺字/字体加载失败/Overfull，6条Underfull保留。
- 用已有uv Python3.11和缓存pdfminer/pypdfium2提取全文并渲染，实际查看第1–3页，检查完整引言跨栏、贡献、与II章衔接和原理图，无可见裁切/越栏。
- 没有安装依赖或更改字体/前言；只实际运行Tectonic/XeTeX，其他引擎未测。Fontconfig/缓存算法包注释UTF8/系统字体路径警告仍在。论文仍为无实验结果的条件理论稿。
- 独立strict复审：`ses_eab6dd116ffeBpxBdRJiz8HAVU` 返回 **go，findings=[]**。实际核读当前/备份引言、Task、阅读分析及相关正文定义/控制律/定理；未重新访问外部论文，临时日志访问受限，阅读过程、编译/版面/字节对照采用主Agent证据，未独立复编或视觉核验。

### 版本绑定

- 修改前Main SHA256：`6348beeff76945d8f693345f19c36d7ca1b72c3c2c49ad00de5ebba9233c57bf`。
- 新Main SHA256：`db5e665dd642ec9ff00170a3252c517dd301d2090186c804b37b8933ca9e72d1`。
- 新PDF SHA256：`ad029ba09bbadc64737f1a548d278ba34d4718e8b8eed2a34ba9172316ab4f6e`。
- 构建日志/提取文本/页面：`C:/Users/12187/AppData/Local/Temp/opencode/intro-rewrite-build/`；MamKO官方PDF/提取文本在相邻`intro-rewrite-research/`。
