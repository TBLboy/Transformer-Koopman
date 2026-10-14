# Proof verification record

## Structural and dimension checks

- `A` is `d x d`, `B` is `d x m`.
- `U_A,V_A` are `d x r_A`; `U_B` is `d x r_B`; `V_B` is `m x r_B`.
- `W_A,W_A^pi` are `r_A x d_c`; `W_B,W_B^pi` are `r_B x n`.
- The formulas remain dimensionally valid for `r_A=r_B=1`; the softmax map is then constant.

## Prediction recurrence

The proof now explicitly decomposes the A branch into state and schedule differences and uses `M_Z` only on the schedule term. The B branch uses `L_B ||C_x e_i|| M_U`. Shared pre-horizon measurement slots are represented by zero-index errors only; no negative-time latent state is introduced. The output bound is `||x_{k+i}-C_x zhat_i|| <= ||C_x|| ||e_i||`.

Boundary cases recorded in the source: `H=1`, `P=2`, `L=0`, `L=1`, and `delta=0`. No claim of asymptotic boundedness is made.

## Three-trajectory freezing check

For arbitrary candidate `U` and nominal `bar U`, the recursions are `g_{i+1}=bar A_i g_i+bar B_i(u_i-bar u_i)` and the full-minus-frozen recursion in the appendix. Common initial histories imply `g_0=e_0=0`, `g_1=bar B_0(u_0-bar u_0)`, and, crucially, `e_1=0`.

The candidate stage envelope uses `D_i`, `G_i^st`, the history envelope `Ghat_i=max_{max(0,i-P+1)<=j<=i}G_j^st`, and the robust maximum recursion `E_{i+1}=max(E_i,L E_i+d_i)`. This history maximum is necessary because `G_i^st` need not be monotone. No monotonicity of input-window deviations is assumed; no claim `E_i <= K_i` is made.

Illustrative low-dimensional check (not a system experiment): take `P=2`, scalar `z=x`, `A(c)=0.5+0.1c`, constant `B=1`, initial history `(x_{-1},x_0)=(0,0)`, nominal inputs `(0,0)`, and candidate inputs `(1,0)`. Both full and frozen trajectories give `z_1=1`, so `e_1=0`; at the next stage the candidate context is `1` while the frozen nominal context is `0`, giving `z_2^full=0.6`, `z_2^fr=0.5`, and `e_2=0.1`. With `M_A=0.6`, `M_B=1`, `L_A=0.1`, `L_phi=1`, `L_B=0`, and `M_Z=M_U=1`, the corrected history envelope gives `d_0=0`, `E_1=0`, and `d_1=0.1`, hence `E_2=0.1`; the old horizon-wide driver is nonzero already at stage one. This verifies the first-step identity and illustrates conservatism; it is not evidence about a trained system.

## QP and cost gap

The QP source now uses `q=2f` in standard `1/2 U^T H U+q^T U` form. The input increment starts at `u_0-u_{-1}`. The cost gap uses common input terms cancellation and only measurement tracking terms. The `2 epsilon_J` chain is explicitly restricted to a common nonempty fixed feasible set, uniform cost approximation, and global minimizers.

## Environment verification

`latexmk -xelatex -interaction=nonstopmode -halt-on-error Main_theory_revised.tex` completed and generated `Main_theory_revised.pdf` (9 pages). A subsequent XeLaTeX pass completed without fatal errors or undefined-reference/citation warnings. Remaining messages are layout warnings in the bibliography only. No numerical theorem certificate for `M_Z`, `M_U`, `L_phi`, or `delta` is claimed by this document.
