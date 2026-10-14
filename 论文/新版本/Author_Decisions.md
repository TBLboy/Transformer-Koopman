# Author decisions required

These choices are intentionally not invented by the revision agent:

1. Confirm whether the actual training objective is one-step only or includes the optional multi-step objective in `eq:multistep_training_loss`.
2. Confirm whether re-encoded latent targets participate in backpropagation or are stop-gradient targets.
3. Confirm how low-rank factor column norms are enforced in training (projection, reparameterization, regularization, or only analysis assumption).
4. Confirm the online nominal-input policy: warm start, shifted previous solution, reference/hold input, or another policy.
5. Confirm whether the online controller freezes once and solves one QP per sample, or performs iterative re-freezing. The theory currently covers only fixed nominal freezing.
6. Provide analytical or certified values/domains for `M_Z`, `M_U`, `L_phi`, and `delta` if these are to be reported numerically. Finite-data estimates must not be presented as uniform certificates.
