# Theory review V2 change log

Source: `Theory_Review_For_Agent_v2.md`. Revised source: `Main_theory_revised.tex`. The original `Main.tex` is not overwritten.

## Item status

| Item | Status | Change / boundary |
|---|---|---|
| V2-01 | corrected with author TODOs | Added explicit one-step objects and losses, optional multi-step definition, separate `g_theta`/`C_phi` interfaces, and stated that finite MSE is not Assumption A5. Stop-gradient and optional-loss adoption remain TODO(author). |
| V2-02 | corrected | Added dimensions, nonnegative gains, rank conditions, explicit factor-norm assumption, rank-one spectral-norm proof, and clarified that this is not stability. Enforcement mechanism remains TODO(author). |
| V2-03 | corrected | Retained and clarified fixed-model Lipschitz constants, `r=1` case, conservative/non-tight status, and proof support in the appendix. |
| V2-04 | corrected | Separated window/input/context domains; removed unused A2/A4 from the primary assumption chain and replaced them with remarks; clarified fixed prediction versus uniform control quantifiers. |
| V2-05 | corrected | Expanded transition decomposition, history-slot reasoning, output error bound, boundary cases, and no-long-horizon claim. |
| V2-06 | corrected with author TODO | Added implementable receding-horizon cycle and explicitly left nominal-input policy / iterative re-freezing as TODO(author). |
| V2-07 | corrected | Standardized QP form to `1/2 U^T H_QP U + q^T U`, with `q=2f`; added dimensions, stacked polyhedral constraints, empty-product convention, initial increment, and `N=1` note. The source uses `\mathcal H` to avoid collision with prediction horizon `H`. |
| V2-08 | corrected | Appendix now distinguishes nominal, frozen, and full trajectories and tracks input-history differences. |
| V2-09 | corrected | Added exact `e_1=0` identity and corrected candidate stage-dependent envelope `E_i` to use the maximum nominal drift over the active history window; no unproved pointwise dominance over the old bound is claimed. |
| V2-10 | corrected | Added a uniform objective-approximation proposition as a sufficient certificate, separated from the abstract assumption, and clarified optimizer/existence and solver-gap conditions. The certificate explicitly requires both context regularity (A2) and the uniform control domain (A4). |
| V2-11 | corrected | Added per-sampling-time/fixed-nominal limitation and explicitly excluded closed-loop guarantees. |
| V2-12 | corrected | Distinguished mathematical assumptions, possible certification, finite-data estimates, and unknown constants. |
| V2-13 | corrected in revised source | Added local trajectory notation and domain/interface clarifications; Introduction and Section II were not rewritten. |

## Not errors retained

- The original QP algebra was consistent; only the solver-facing linear coefficient notation was normalized (`q=2f`).
- The finite-horizon geometric bound does not require `L<1`; no asymptotic stability claim was added.
- The `2 epsilon_J` result remains conditional on a common fixed nonempty feasible set, uniform approximation, and global minimizers.
