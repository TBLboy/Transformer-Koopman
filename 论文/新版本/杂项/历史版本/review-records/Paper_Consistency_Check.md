# 六章论文候选稿一致性检查

日期：2026-10-19。检查对象：同目录`Main_SixSection_TheoryRewritten.tex`。本文只记录实际执行结果，不替代独立数学审查。

## 1. 版本和权限

- 现行母稿SHA256=`1ee01187dfdad058746fe9fb3e2489c467b96de09ead0ef67be7a3f2855aee69`，与合订本Main附录规范换行后全文一致。原Main不覆盖、不改写；新稿由其内容迁移重构，路径与迁移对照见Change Summary。
- 指定MAKO参考在用户微信文件目录找到，经已有uv Python3.11及缓存pdfminer提取文本，核对引言与4.1/4.2安排。直接PDF输入不受模型支持，外部文档工具路径权限受限，实际采用本机文本提取；不声称视觉精读参考PDF，不复用其定理。
- 只新增候选tex、两份短md及真实编译PDF；无训练/控制代码、checkpoint、实验数据或图片改动，无V4或新理论分支。

## 2. 结构、迁移和论文阅读路径

- Node静态检查实际通过：正文六章；小节数为`[0,2,2,2,0,0]`；无subsubsection；附录A/B/C共三个；一个在线Algorithm、一个主Theorem。III.B有Constructible contractive model class命题；IV.B为闭环主定理和连续Proof。
- 原patch线性嵌入、sinusoidal positions、Transformer、mean pooling、低秩softmax×tanh、Stage0/Stage1与测量/提升联合损失均保留。原长训练算法压缩为两段训练定义；训练target明确stop-gradient，预测只初始化编码一次。
- 主Agent按委托的阅读路径核读摘要→引言贡献/导航→III两节首末→IV.A首末→IV.B定理及证明→结论：历史可区分信息→候选调度非凸→冻结QP→公共收缩/成本/shift→实际Frozen值下降的因果链已在正文呈现，不需读V3报告才知道设计动机。
- 第V章只保留短占位，无数据、比较优越性、硬件或时延结论；三幅方法图沿用合法占位框，未生成任何结果图。正文与附录未出现Gate/GO/NO-GO/P5/BLOCKER/reviewer等研究报告语言。

## 3. 数学一致性逐项核查（主Agent）

| 红线 | 候选稿定位 | 核查结果 |
|---|---|---|
| q/F与cache | III.A，eq:augmented_state / complete_control_model / residual_definition | a仅过去状态，追加当前Cxz；v追加当前u；q^E采样重编码，预测q递归；w含编码图缺陷 |
| 可构造而非直接假定DF小 | III.B prop:contractive_class；附录A eq:full_derivative / gain_choice | Schur→Pi，完整DA Dc z及DB dx u项，先M后严格正t；非零历史调度/两周期解析例，与B一致 |
| 全部Frozen量词及非循环域 | IV.B ass:domain，附录B | Q×U×S_Q统一，实际w仅要求当前合法；先nominal再候选再实际下一点，未假设未来已留域 |
| 唯一成本与控制器 | IV.A eq:stage_cost / quadratic_template / nominal_shift | 完整q正定+参考相对增量+beta终端+input-only；一次full/freeze/QP，shift实际返回同一序列 |
| 严格凸性 | IV.A Hessian及附录B | 首个非零输入扰动写下一缓存，受阶段/终端正定惩罚，R/S仅PSD亦唯一 |
| 参考/终端 | II.B、IV.B ass:reference / terminal_weight | 固定绝对时间，Eprev qref=u_ref,prev，输入可行，dref界及theta/beta完整 |
| 首步与B-EXACT | IV.B正文Proof及附录B | 任意候选仅首步精确，名义同序列全程精确，不消去实际w |
| shift尾项及N=1 | eq:shift_error / shift_comparison / epsilon_closed_loop | d0=wbar、尾lambda d_{N-1}无额外eta，N=1空和明确 |
| W真实依赖及下降 | IV.B开头/eq:value_descent | W含q^E/nominal/绝对时刻，非单独状态函数；下降非理想full目标的2epsilon_J |
| 比较常数/递推 | eq:value_constants / value_comparison，附录C | 参考整段候选，i>=1相对增量零；A/B/epsilon/rho全定义，初值B合并正确 |
| 次优与输入投影 | eq:solver_gap / squared_tracking_bound / input_tracking，附录C | 原始可行目标差delta_k、shift同返回；输入界另加当前delta_k；R奇异不可除 |
| 零误差/边界 | IV.B Remark、Conclusion | 四误差零才以通用界断言指数至零；保留eta>0一般不能精确跟踪的限定；不推隐藏物理状态/ISS/安全/实时性 |

未发现需修改V3数学契约的新漏洞；这里只迁移和重述既有条件定理。新收缩参数化/硬帽以proposed design呈现，不声称现有无约束训练已满足。原代码的Stage1骨架可训练性与新设计最后固定模型后重算Pi的要求有明确区分。

## 4. LaTeX静态、引用及依赖

- 已执行临时检查脚本：UTF-8/控制字符、花括号、begin/end环境、80个唯一label及57处ref/eqref全部通过，无未定义/重复标签，无重复theorem宏。
- 26个实际引用键均有bibitem；26条保留条目与母稿规范空白后逐字一致，无新增引用键或新文献事实。删除13条新版不引用的备列文献，引用按剩余条目编号；不把这一文本一致性声称为重新核验原论文全部元数据。
- 旧Q_x/P_x、J_full正式控制目标、2epsilon_J、旧任意跨轮名义政策和独立旧预测假设体系已从新稿移除；原Main保持完整。
- 无外部includegraphics、input或独立bib依赖：图为源内占位，参考文献内嵌；在同目录使用已有IEEEtran.cls及声明的TeX包即可构建。XeTeX body Times映射继承母稿，mathsf使用明确Arial映射；其他标准LaTeX引擎保留默认mathsf。跨机器字体和TeX包可用性仍需对应环境。

## 5. 真实编译与PDF检查

实际使用PATH外已有`Tectonic 0.17.0`，命令为：

```text
C:\Users\12187\AppData\Local\Temp\opencode\tectonic\tectonic.exe --only-cached --keep-logs --keep-intermediates --outdir C:\Users\12187\AppData\Local\Temp\opencode\sixsection-paper-build Main_SixSection_TheoryRewritten.tex
```

- 最后一次由Node spawnSync取得真实进程退出码`0`，完成TeX重跑及xdvipdfmx，生成9页PDF。未安装依赖、未联网下载包。临时log/console/aux均保存在上述临时目录，不写入论文源目录。
- 最后TeX日志：无undefined citation/reference、无缺字/字体加载失败、无Overfull hbox/vbox。保留7条Underfull hbox排版警告（关键词、贡献换行及少量段落）；不是无法编译或数学缺失。
- 环境警告：Fontconfig默认配置未找到但实际字体加载和PDF输出成功；缓存algorithm.sty/algorithmic.sty第11行有非法UTF-8注释警告；系统字体绝对路径使跨环境字节级可复现性有限。未篡改系统/缓存包以压制这些警告。
- 用已有缓存pdfminer提取PDF（9页、约4.7万字符），并以pypdfium2渲染第1/5/6/7/8/9页核查正文、主定理与证明、附录及参考版面；已看到单次QP算法、主定理和式值下降/比较界位于正文，公式未越栏。PDF不是单页片段，也未伪造结果图。

## 6. 状态与限制

独立strict最终审查已返回`go`，无required finding：reviewer独立核读候选TeX、两份对照材料及母稿/V3契约，复核正文和附录数学链，未发现必需修复项。其未独立复编或复算哈希，PDF输入不受支持且临时日志不可访问，故编译/版面结果采用主Agent真实验证证据；外部写作委托读取受限，依据冻结Task及明确传入要求验收。主Agent已直接核对委托原文。

代码/实验/当前plant认证不在本轮范围；本稿是可审阅的独立理论候选，结果章仍空缺。重启后再次核对母稿、候选tex/pdf哈希均与编译版一致；内层Git仍只有四个新增交付文件。本文件不把编译成功或Agent审稿等同于形式验证、实验认证或外部学术同行评审。
