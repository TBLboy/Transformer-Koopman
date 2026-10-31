# 六章论文候选稿修改对照

## 范围与母稿

- 委托：`Agent_Brief_MainTex_SixSection_Paper_Rewrite_20261019.md`（2026-10-19）。本次仅写独立论文候选源文件，不改当前`Main.tex`、V3原件、训练/控制代码或实验图片。
- 母稿：同目录`Main.tex`，SHA256=`1ee01187dfdad058746fe9fb3e2489c467b96de09ead0ef67be7a3f2855aee69`。与V3原始资料合订本Main附录规范换行后全文一致，无版本差异需要覆盖。
- 新稿：`Main_SixSection_TheoryRewritten.tex`。继承IEEEtran、原英文题名/作者、现有宏/包、内嵌参考文献及合法方法图占位；不覆盖母稿，母稿保留即可恢复。
- V3-C约束控制定义，V3-D约束定理，V3-B提供构造，V3-A作量词/边界核查。不把原研究报告叙述移入论文。
- 指定MAKO PDF已在用户微信文件目录找到，读取文本核对其紧凑引言及4.1控制/4.2稳定性安排。仅借鉴组织，不引用或复用其渐近稳定论证。模板仍为IEEEtran。

## 逐块迁移图（已按候选稿核对）

| 母稿块/原行 | 原问题与修改目的 | 新位置与处理 |
|---|---|---|
| 标题/摘要/关键词，86–97 | 旧摘要只到有限时域及full-MPC单轮成本差 | 保留题名，摘要改为历史调度→单次QP→可构造公共收缩→条件闭环界，无实验声称 |
| Introduction，100–128 | 保留输入输出历史问题及Koopman/时延/时序网络文献；旧三贡献不匹配闭环主线 | I：保留可用背景，局部重写缺口和方法；三贡献为模型、single-freeze控制器、构造性与闭环；overview占位说明同步q/成本/shift |
| Koopman Modeling and Temporal Lifting，138–195 | 避免无限维算子与有限预测矩阵混同 | II.A：精简受控Koopman和测量状态关系，保留测量保留提升定义/标签 |
| Learning Problem and Design Objectives，198–218 | 原任务只界定预测，控制参考信息缺失 | II.B：数据、已知历史、输入多面体、时域、完整参考/输入缓存关系，训练细节留III.B |
| Temporal Lifting / Low-Rank，227–326 | 最可复用的方法主体；缺完整非重复状态接口 | III.A：保留patch/position/mean-pooling、context和softmax×tanh低秩头；定义q/F、编码初值、w；P统一为P_h |
| Two-Stage Training，328–416 | 保留joint测量/提升损失，训练伪代码不再占据主视觉；新增约束不能冒充旧实现 | III.B：保留Stage0/Stage1与stop-gradient编码targets，用q递归统一训练预测；学习损失不等于域残差；Schur/增益/谱帽为proposed constrained design，骨架变化后重算Pi/预算 |
| Finite-Horizon Prediction，418–514 | 两套工作域与不同范数会竞争新假设 | 不再单列；支持性预测估计在III.B简述并由同一公共Pi收缩递推；移除旧A1–A3/L/max误差体系 |
| Scheduled/Frozen，523–573 | 保留同初值名义rollout与首步精确 | IV.A：改为完整q的名义系数和Frozen仿射递推；冻结来自名义而非候选 |
| Condensed QP，575–631 | 旧measurement-only/absolute increment/任意跨轮nominal与新主定理冲突 | IV.A：完整q成本、参考相对增量、beta终端、input-only QP和实际返回shift；保留一组凝聚Hessian，证明PD不依赖R>0 |
| Freezing/Suboptimality，633–729 | 旧2epsilon_J不是跨采样闭环定理 | IV.B：主定理/连续正文证明，B-EXACT→shift d_j→reference tail→DeltaW→比较递推；旧full目标/2epsilon_J主线删除 |
| Experiments，732–748 | 只有待补占位，不可编造结果或长计划书 | V Numerical Results：保留诚实短占位，不设小节，不输出数值/图像 |
| Conclusion，751–759 | 旧“仅open-loop”总结过时 | VI：总结新模型/单次QP/条件实际指数跟踪，不写实验或当前plant认证 |
| Proof Details，761–807 | 旧证明及成本展开不再适用 | 附录A构造/网络/残差/解析例，B域/首步/strict凸性/tail连续界，C价值常数/求解误差/输入界；不是V3原文拼接 |
| 39条bibitem，811–930 | 原参考文献可复用，不能造新条目 | 保留26条正文实际引用的原条目，规范空白后逐字未改；删13条原稿备列但新版未引用条目，不增造文献或声称重新认证原书目信息 |

## 主数学修改

1. 唯一模型为`q=col(z,a,v)`、测量保留`z`、缓存追加当前`C_x z`及当前u；实际重新编码差异统一为w。encoder只用于采样/训练rollout初始化，潜状态递归与每步重编码分开。
2. III.B收缩构造命题：Schur增广骨架→离线Lyapunov Pi→完整链式导数与Frozen统一界→先域后非零增益。附录写出k_F/k_fr/k_b与严格t预算，并明确真实残差不是训练loss的推论。
3. IV.A唯一控制成本是完整q误差、输入误差、参考相对增量及beta Pi终端；只含逐步输入硬约束，名义必须shift实际返回序列+绝对时间tail。
4. IV.B条件主定理分析每轮重新冻结的W，正文保留值下降和比较界；附录精确给A/B/epsilon/rho等常数。可行目标差delta_k只进入当轮下降；输入界还含当前delta_k。
5. 保留测量投影与适用性限定；不推出隐藏物理状态稳定、任意参考重规划、安全硬约束或硬件实时性。

## 交付说明

新稿是论文候选而非当前代码已实现的说明；训练/模型中新增约束均作为设计定义，不将现有无约束A0训练声称为已经满足收缩。结果章保持占位，未触及冻结实验或造图。已用已有Tectonic 0.17.0离线缓存真实编译出9页PDF，未安装依赖；保留原XeTeX Times兼容逻辑，并仅为mathsf增加显式Arial字体映射以避免缺失cmss10度量。实际执行的检查与剩余限制统一见`Paper_Consistency_Check.md`；最终严格审查结果记录于本次Task，不在论文中写审稿流水。
