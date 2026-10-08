# -*- coding: utf-8 -*-
"""Second-round fixes from the focused re-verification.

N1 (moderate, introduced by the previous D5 edit) the diagnostics paragraph
   misattributed the frozen deployment predictor to "strategy C" of the
   Section VII-A ablation. The reported predictor is the gate14_stabilize.py
   checkpoint A_stab_openloop_lam0.0_rho0.99.pt (nominal pretraining from
   fixed.pt, then full scheduled-rollout fine-tuning with best-validation
   checkpoint selection and no spectral penalty). It follows the same SCHEDULE
   as ablation variant C but is a different run, so the paper must not claim
   identity. The same overstatement appears in the Section VII-A closing.
N2 (minor) the two percentages for the B-vs-C comparison used different bases
   ((B-C)/B for the RMSE, (B-C)/C for the MSE). Both are now relative to C.
N3 (minor) the spectral-stabilization comparison is single-seed; disclose it.
"""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")
R = []

# ---- N1: do not claim the deployment predictor IS ablation strategy C
R.append((
    "as an optimization initialization rather than a necessity of the model, and all remaining results use the predictor of strategy~C, whose training schedule is the one described there.",
    "as an optimization initialization rather than a necessity of the model. All remaining results use the deployment predictor described in Section~\\ref{sec:methodology}, which was trained with the same schedule as variant~C; the ablation variants isolate the contribution of each element of that schedule."
))

# ---- N1: describe the diagnostics predictor without misattributing it
R.append((
    "Table~\\ref{tab:diagnostics} reports the diagnostics measured on the frozen deployment predictor (strategy~C of Section~\\ref{subsec:schedule_ablation}: all parameters optimized, $r=2$, scheduled propagation) on the soft-robot validation set",
    "Table~\\ref{tab:diagnostics} reports the diagnostics measured on the frozen deployment predictor of Section~\\ref{sec:methodology} (all parameters optimized under the scheduled-rollout objective, $r=2$, scheduled propagation) on the soft-robot validation set"
))

# ---- N2: use a single percentage base (relative to C) for both quantities
R.append((
    "variant~B is worse than variant~C at every horizon and in every seed, by $5.6\\%$ at $H=20$, with a $24\\%$ higher rollout MSE.",
    "variant~B is worse than variant~C at every horizon and in every seed, with a $5.9\\%$ higher rollout RMSE and a $24\\%$ higher rollout MSE at $H=20$."
))

# ---- N3: disclose that the spectral comparison is single-seed
R.append((
    "A variant trained on the one-step objective with an explicit spectral constraint $\\rho(\\mA(\\vc))\\le0.99$ attains an $H=20$ rollout RMSE of $1.5681$, whereas the same constrained model trained under the scheduled-rollout objective attains $0.0412$.",
    "A variant trained on the one-step objective with an explicit spectral constraint $\\rho(\\mA(\\vc))\\le0.99$ attains an $H=20$ rollout RMSE of $1.5681$ (single seed), whereas the same constrained model trained under the scheduled-rollout objective attains $0.0412$."
))


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    assert "\ufeff" not in raw, "unexpected BOM"
    nl = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")
    for i, (old, new) in enumerate(R, 1):
        c = text.count(old)
        assert c == 1, "item %d: expected 1, found %d\n--- %s" % (i, c, old[:130])
        text = text.replace(old, new)
        print("applied %d" % i)
    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(text.split("\n")))
    print("OK")


if __name__ == "__main__":
    main()
