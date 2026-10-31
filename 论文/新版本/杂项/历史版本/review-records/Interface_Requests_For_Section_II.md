# Interface requests for Section II

No Section II prose was rewritten in the theory branch. The following minimal interfaces should be reconciled when the sections are merged:

- Keep `P` for history length, `H` for prediction horizon, `N` for control horizon, and `P_x` for terminal cost.
- State that `g_theta` consumes measurement history `X` only, while `C_phi` consumes the joint `(X,U^{in})` window.
- Preserve `C_x=[I_n 0]` and the common-history convention used to establish `e_j=0` for pre-horizon history slots.
- State that the current input is excluded from `U^{in}` and enters the scheduled update separately.
