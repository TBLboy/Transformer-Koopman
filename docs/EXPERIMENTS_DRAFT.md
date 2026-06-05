## Section V. Experiments

This section evaluates the proposed Transformer-Koopman framework from three complementary perspectives. First, we compare its open-loop trajectory prediction performance against representative baselines to verify whether temporal lifting improves modeling accuracy. Second, we conduct ablation studies to isolate the contributions of the major design choices in the proposed framework. Third, we assess whether the identified model is suitable for feedback control by embedding it into a common LQR-based tracking framework and comparing the resulting closed-loop tracking performance with several alternative controllers.

### A. Experimental Setup

We evaluate the proposed method on two controlled nonlinear dynamical systems. The first platform is a 6-state manipulator system, and the second platform is a 2-state soft robotic system. For each platform, trajectory data are collected under varying control inputs and then split into training, validation, and test sets. All learning-based models are trained on the same data partitions and evaluated under the same normalization procedure to ensure a fair comparison.

The compared models in the open-loop prediction experiments include: 1) the proposed Transformer-Koopman method, which uses a patch-based Transformer encoder to construct the lifting map from a finite history window; 2) traditional EDMD with hand-crafted observables; 3) MLP-Koopman, which replaces the Transformer encoder with a multilayer perceptron; and 4) LSTM-Koopman, which replaces the Transformer encoder with an LSTM-based temporal encoder. For the Koopman-based learned models, the overall prediction pipeline is unified as an encoder-lifting stage, a linear Koopman propagation stage, and a fixed linear decoder that recovers the physical state from the lifted state.

For all learned lifting models, training follows the protocol described in Section IV, including joint optimization of the encoder and the linear Koopman dynamics, together with a final closed-form refit of the Koopman matrices when applicable. The main evaluation metrics are the root-mean-square error (RMSE) and mean absolute error (MAE) computed over multi-step autoregressive rollout trajectories. Since the purpose of the proposed method is to improve temporal lifting for controlled systems, we emphasize multi-step rollout accuracy rather than only one-step prediction performance.

The implementation details for each platform, including the history-window length, latent dimension, encoder size, batch size, learning rate, and training epochs, will be reported in the final version together with the exact data statistics.

**[Placeholder: Table 1. Summary of datasets, train/validation/test splits, and main hyperparameters for both platforms.]**

### B. Open-Loop Prediction Comparison

We first compare the proposed method with EDMD, MLP-Koopman, and LSTM-Koopman in open-loop trajectory prediction. This experiment is intended to answer the following question: does explicitly encoding finite trajectory history through a structured temporal lifting map improve the quality of the identified Koopman dynamics model?

Table **[Placeholder: Table 2]** summarizes the prediction results on both platforms. Overall, the proposed Transformer-Koopman model achieves the best rollout accuracy among the compared methods. In particular, it consistently reduces the long-horizon prediction error relative to EDMD and the neural Koopman baselines, indicating that the learned temporal lifting map better captures the short-term dynamical context needed for accurate linear evolution in the lifted space.

The performance gap is especially meaningful in the autoregressive rollout setting. Although one-step prediction can often be improved by local fitting, long-horizon rollout accuracy is more sensitive to whether the lifted state preserves the dynamical information required for repeated propagation. The results therefore suggest that the patch-based Transformer encoder provides a more effective lifting representation than instantaneous-state observables or simpler learned encoders.

Figure **[Placeholder: Fig. 4]** shows representative rollout comparisons on the two platforms. The proposed method tracks the ground-truth trajectories more closely over extended horizons, while the baseline methods exhibit more pronounced error accumulation. This trend is consistent with the motivation of the paper: by incorporating a finite history window into the lifting map, the proposed method reduces the ambiguity associated with instantaneous-state lifting and improves the consistency of the identified Koopman dynamics.

It is worth emphasizing that better open-loop prediction accuracy is not automatically guaranteed by using a larger encoder. Rather, the improvement arises from the combination of three factors: 1) explicit use of recent trajectory history; 2) patch-based tokenization that preserves local temporal structure while reducing sequence length; and 3) linear propagation in a structured lifted space that remains compatible with model-based control design.

**[Placeholder: Table 2. Quantitative open-loop prediction results on both platforms.]**

**[Placeholder: Fig. 4. Representative multi-step rollout comparisons on Platform 1 and Platform 2.]**

### C. Ablation Study

We next analyze which components of the proposed framework are responsible for the observed performance gains. The ablation study is conducted on both platforms and is organized into two groups: module ablations and hyperparameter ablations.

The module ablations remove or modify major components of the proposed architecture, including the patch-based tokenization mechanism, the self-attention module, and the positional encoding. These experiments are designed to determine whether the advantage of the proposed model comes from the complete architecture or merely from increased representation capacity. The results show that removing any of these components degrades performance, which confirms that the final accuracy gain depends on the coordinated use of temporal patching, attention-based sequence modeling, and positional information.

The hyperparameter ablations further examine the roles of the history-window length, patch length, encoder depth, and latent dimension. These experiments help characterize the sensitivity of the model to the amount of temporal context and representation capacity. The results indicate that finite history is essential for accurate prediction, but excessively large or poorly matched hyperparameter choices do not necessarily improve performance further. This trend supports the central claim of the paper: what matters is not simply increasing model size, but constructing a lifting map that preserves the relevant short-term temporal information in a structured manner.

The ablation results also provide an interpretation of why the proposed approach outperforms the baselines. When the history mechanism is weakened or the patch-based temporal structure is removed, the resulting model becomes less capable of organizing recent trajectory information into a lifted state that evolves linearly. The performance degradation observed in these variants is therefore consistent with the methodological motivation in Sections III and IV.

**[Placeholder: Fig. 5. Module ablation results on Platform 1 and Platform 2.]**

**[Placeholder: Fig. 6. Hyperparameter ablation results on Platform 1 and Platform 2.]**

### D. Closed-Loop Tracking Comparison

Open-loop prediction accuracy is important, but it does not by itself guarantee improved control performance. We therefore further evaluate whether the identified models lead to better closed-loop trajectory tracking when embedded into a common control framework.

In this experiment, the learned or identified models are combined with an LQR-based controller derived from their corresponding lifted linear dynamics. Specifically, Transformer-Koopman, EDMD, MLP-Koopman, and LSTM-Koopman each provide an explicit lifted dynamics model of the form $z_{k+1} = A z_k + B u_k$, which is then used to construct a feedback controller under a common tracking formulation. In addition, a PID controller is included as a classical baseline. All controllers are evaluated on the same set of reference trajectories and under the same actuator constraints. The final paper will report the exact tuning protocol and controller parameters used for all methods.

We select several representative reference trajectories for evaluation, including trajectories with sharp corners and rapidly changing directions. In particular, polygonal and star-shaped paths are useful stress tests because they require both accurate transient response and stable error correction. These trajectories therefore reveal more clearly whether improvements in model identification translate into meaningful control benefits.

Figure **[Placeholder: Fig. 7]** will present representative tracking comparisons for one or two typical trajectories, such as a square trajectory and a five-pointed-star trajectory. The final figure will include the reference path, the actual tracked trajectories of all compared methods, and local zoom-in views around the most challenging segments. Such visualization is important because it reveals not only the overall tracking trend but also the local behavior near corners, turning points, and high-curvature segments.

Table **[Placeholder: Table 3]** will summarize the average tracking error of each controller on all test trajectories. Based on the current experimental design, this comparison is intended to answer whether the improved temporal lifting quality of Transformer-Koopman yields lower closed-loop tracking error than alternative Koopman-based controllers and a classical PID baseline. If confirmed by the final quantitative results, this would provide direct evidence that the proposed modeling framework is not only better for prediction but also more useful for control.

From a conceptual standpoint, this experiment serves as the bridge between the modeling and control parts of the paper. The goal is not merely to demonstrate that the proposed controller can track a trajectory, but to examine whether a more accurate and better-structured lifting map leads to a more effective linear control model in practice. In this sense, the closed-loop comparison complements the open-loop prediction results and strengthens the control-oriented significance of the proposed method.

**[Placeholder: Fig. 7. Closed-loop trajectory-tracking comparisons on representative reference trajectories, with local zoom-in views.]**

**[Placeholder: Table 3. Average tracking error of Transformer-Koopman + LQR, EDMD + LQR, MLP-Koopman + LQR, LSTM-Koopman + LQR, and PID.]**

### E. Discussion

Taken together, the three groups of experiments are designed to support the main claims of this paper from complementary angles. The open-loop prediction results evaluate whether the proposed temporal lifting strategy improves the identified Koopman model. The ablation results explain which architectural and temporal-design choices are responsible for the gain. The closed-loop tracking results then assess whether the improved model quality translates into practical control advantages.

If the final control comparison confirms that the proposed method achieves lower average tracking error than the competing controllers, the overall conclusion of the experimental section will be that Transformer-Koopman provides a more control-relevant lifting representation than the baseline methods. If some trajectories remain challenging, those cases will also be informative, since they can reveal which classes of motion are most sensitive to modeling residuals, input saturation, or limitations of the linear control approximation.

Overall, the experiments are intended to show that the proposed method should not be viewed merely as a forecasting architecture. Rather, it is a temporal lifting framework for controlled nonlinear systems, designed to improve both the identification of linear Koopman dynamics and the downstream effectiveness of model-based control.
