# Transformer-Scheduled Koopman MPC 新理论路线前期研究计划

## 0. 项目目标

当前研究路线调整为：

> Learning a history-conditioned scheduled Koopman predictor with
> measurement-dependent input modulation and developing a convex LTV-MPC
> approximation with finite-horizon error characterization.

核心模型：

\[ z\_{k+1}=A(c_k)z_k+B(x_k)u_k \]

其中：

-   (c_k)：由历史窗口生成的 scheduling context；
-   (A(c_k))：历史条件动力学演化；
-   (B(x_k))：当前测量条件输入作用矩阵。

控制思想：

1.  根据当前历史生成 nominal rollout；
2.  得到未来调度序列： \[
    `\bar `{=tex}A_i=A(`\bar `{=tex}c_i),`\quad `{=tex}`\bar `{=tex}B_i=B(`\bar `{=tex}x_i)
    \]
3.  冻结调度；
4.  得到 LTV 模型： \[ z\_{i+1}=`\bar `{=tex}A_i z_i+`\bar `{=tex}B_i
    u_i \]
5.  求解凸 QP MPC。

理论目标：

-   建立 scheduled Koopman predictor 的有限时域预测误差界；
-   建立 frozen scheduling LTV-MPC 相对于完整 scheduled MPC
    的条件性优化次优性界。

------------------------------------------------------------------------

# 第一阶段：模型数学结构确认

## 1. History-conditioned transition

定义：

\[ c_k=C\_`\phi`{=tex}(X_k,U_k\^{in}) \]

其中：

\[ X_k=\[x\_{k-P+1},...,x_k\] \]

\[ U_k\^{in}=\[u\_{k-P+1},...,u\_{k-1}\] \]

需要明确：

-   当前输入 (u_k) 不进入 context；
-   context 只描述过去轨迹信息。

------------------------------------------------------------------------

## 2. Low-rank scheduled transition

定义：

\[ A(c)=A_0+U_A diag(`\gamma`{=tex}\_A(c))V_A\^T \]

需要证明：

\[ \|A(c)-A_0\|`\le `{=tex}g_A \]

并明确：

-   低秩因子归一化方式；
-   rank (r_A)；
-   调制函数形式。

------------------------------------------------------------------------

## 3. Measurement-dependent input modulation

定义：

\[ B(x)=B_0+U_Bdiag(`\gamma`{=tex}\_B(x))V_B\^T \]

理论动机：

固定输入矩阵假设：

\[ `\Delta `{=tex}u`\rightarrow`{=tex}`\Delta `{=tex}z \]

作用固定。

对于软体机器人，输入效果随当前形态变化，因此：

\[ B=B(x) \]

用于描述状态相关输入效能。

注意：

暂不使用严格 bilinear Koopman 术语。

推荐术语：

-   scheduled Koopman predictor；
-   measurement-dependent input modulation。

------------------------------------------------------------------------

# 第二阶段：文献调研任务

## 1. Koopman controlled systems

重点：

-   Koopman with control；
-   input-affine Koopman；
-   finite-dimensional Koopman approximation。

目标：

回答：

> 为什么 (A(c)z+B(x)u) 是合理的 controlled Koopman surrogate？

------------------------------------------------------------------------

## 2. LPV / scheduling MPC

重点：

-   scheduling variable；
-   frozen parameter approximation；
-   LPV-MPC；
-   quasi-LPV systems。

目标：

支撑冻结调度控制思想。

------------------------------------------------------------------------

## 3. Prediction error bounds

寻找：

-   Koopman approximation error；
-   finite horizon prediction bound；
-   Lipschitz error propagation。

------------------------------------------------------------------------

## 4. Approximate MPC theory

寻找：

-   model mismatch MPC；
-   frozen model MPC；
-   suboptimality bound；
-   approximate optimization MPC。

------------------------------------------------------------------------

# 第三阶段：第五章理论包

## Proposition 1：Low-rank boundedness

证明：

\[ \|A(c)-A_0\|`\le `{=tex}g_A \]

\[ \|B(x)-B_0\|`\le `{=tex}g_B \]

------------------------------------------------------------------------

## Proposition 2：Scheduling Lipschitz continuity

证明：

\[ \|A(c)-A(`\bar `{=tex}c)\| `\le `{=tex}L_A\|c-`\bar `{=tex}c\| \]

\[ \|B(x)-B(`\bar `{=tex}x)\| `\le `{=tex}L_B\|x-`\bar `{=tex}x\| \]

------------------------------------------------------------------------

## Proposition 3：Recursive prediction consistency

分析：

encoder latent：

\[ z\^{enc} \]

propagated latent：

\[ z\^{prop} \]

之间误差传播。

需要重新考虑 (B(x)) 引入后的影响。

------------------------------------------------------------------------

## Theorem 1：Finite-horizon prediction error bound

目标：

建立：

\[ \|e\_{k+H}\| `\le`{=tex} L\^H\|e_k\|
+`\sum`{=tex}\_iL\^{H-1-i}`\delta`{=tex}\_i \]

其中：

-   lifting residual；
-   transition residual；
-   input modulation residual。

------------------------------------------------------------------------

# 第四阶段：第六章控制理论包

## 1. Complete scheduled MPC model

完整预测：

\[ z\_{i+1}=A(c_i)z_i+B(x_i)u_i \]

------------------------------------------------------------------------

## 2. Nominal rollout

给定：

\[ `\bar `{=tex}U \]

得到：

\[ `\bar `{=tex}x_i,`\bar `{=tex}c_i \]

并计算：

\[ `\bar `{=tex}A_i,`\bar `{=tex}B_i \]

------------------------------------------------------------------------

## 3. Frozen LTV model

冻结：

\[ z\_{i+1}=`\bar `{=tex}A_i z_i+`\bar `{=tex}B_i u_i \]

------------------------------------------------------------------------

## Proposition：Convexity of frozen LTV-MPC

证明：

预测：

\[ X=F+GU \]

代价 Hessian：

\[ H=2(G^TQG+R+D^TSD) \]

满足：

\[ H`\succeq0`{=tex} \]

因此冻结 MPC 为凸 QP。

------------------------------------------------------------------------

# 第五阶段：冻结调度误差理论

## Theorem 2：Finite-horizon freezing error bound

定义：

完整预测：

\[ z_i\^{full} \]

冻结预测：

\[ z_i\^{fr} \]

误差：

\[ e_i=z_i^{full}-z_i^{fr} \]

递推：

\[ e\_{i+1} = `\bar `{=tex}A_i e_i + (A(c_i)-`\bar `{=tex}A_i)z_i +
(B(x_i)-`\bar `{=tex}B_i)u_i \]

目标：

得到：

\[ \|e_i\|`\le `{=tex}K_i \]

------------------------------------------------------------------------

# 第六阶段：优化次优性理论

定义：

完整代价：

\[ J\_{full}(u) \]

冻结代价：

\[ J\_{fr}(u;`\bar `{=tex}u) \]

若：

\[ \|J\_{full}(u)-J\_{fr}(u;`\bar `{=tex}u)\|
`\le`{=tex}`\epsilon`{=tex}\_J \]

则：

\[ 0`\le`{=tex} J\_{full}(u\^{fr}) - J\_{full}(u\^`\star`{=tex})
`\le2`{=tex}`\epsilon`{=tex}\_J \]

该结论为条件性次优性界。

------------------------------------------------------------------------

# 第七阶段：代码验证计划

## Model verification

验证：

-   (A(c)) 范围；
-   (B(x)) 范围；
-   低秩修正大小。

------------------------------------------------------------------------

## Prediction verification

比较：

完整 rollout：

\[ z\^{full} \]

冻结 rollout：

\[ z\^{fr} \]

验证误差：

\[ \|e_i\| \]

------------------------------------------------------------------------

## Control verification

比较：

-   Frozen LTV-MPC；
-   Full scheduled MPC。

指标：

-   tracking error；
-   computation time；
-   cost gap。

------------------------------------------------------------------------

# 第八阶段：最终理论输出结构

    Theory_Package/

    ├── Model_Definition
    ├── Assumptions
    ├── Low_rank_Boundedness
    ├── Scheduling_Lipschitz
    ├── Prediction_Error_Bound
    ├── Frozen_LTV_QP_Proof
    ├── Freezing_Error_Bound
    ├── Conditional_Suboptimality
    └── Reference_List

------------------------------------------------------------------------

# 当前禁止修改事项

在理论包完成之前：

禁止：

-   修改摘要；
-   修改 Introduction；
-   修改实验；
-   修改标题；
-   声称 bilinear Koopman；
-   声称实时保证；
-   声称闭环稳定。

------------------------------------------------------------------------

# 当前优先确认问题

## Question 1

(B(x)) 的调度变量：

推荐：

\[ x_k=Cz_k \]

保持 measurement-dependent。

------------------------------------------------------------------------

## Question 2

冻结误差比较对象：

推荐：

同一输入序列下：

完整模型 vs 冻结模型。

不要直接比较两个优化器。

------------------------------------------------------------------------

## Question 3

次优性证明：

推荐采用：

\[ 2`\epsilon`{=tex}\_J \]

形式。

不要直接假设：

\[ CN(`\delta`{=tex}\_A+`\delta`{=tex}\_B) \]

------------------------------------------------------------------------

# 最终研究目标

形成完整理论链：

学习 history-conditioned scheduled Koopman predictor

↓

measurement-dependent input modulation

↓

scheduled rollout training

↓

frozen LTV-MPC

↓

finite-horizon freezing error bound

↓

conditional optimization suboptimality bound
