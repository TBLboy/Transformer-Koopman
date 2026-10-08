# -*- coding: utf-8 -*-
"""Fix the defects found by the independent verification review.

D1 (major)  L559 claimed a Section VII spectral-stabilization experiment that the
            paper did not report -> report it in Section VII-A (data already
            recorded in gate14_result.json) and point L559 at that subsection.
D2 (minor)  "1.6x faster than RTI-RE" contradicted Table I (182/78 = 2.33x at
            p50, 253/120 = 2.11x at p95).
D3 (minor)  the reference training retains the best-validation checkpoint and
            applies no spectral penalty; Section IV-B did not say so.
D4 (minor)  "seed spread at most 0.0011" is the standard deviation, not the range.
D5 (minor)  "A-only" collided with ablation strategy A.
"""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")
R = []

# ---- D1: point the spectral claim at the subsection that now reports it
R.append((
    "This explains our experimental observation (Section~\\ref{sec:experiments}) that constraining $\\rho(\\mA)\\le0.99$ fails to restore scheduled-rollout accuracy, whereas changing the training objective does.",
    "This explains our experimental observation (Section~\\ref{subsec:schedule_ablation}) that constraining $\\rho(\\mA)\\le0.99$ fails to restore scheduled-rollout accuracy, whereas changing the training objective does."
))

# ---- D1: report the spectral-stabilization comparison in Section VII-A
R.append((
    "The separation of B from C and D exceeds the seed spread, whereas C and D are statistically indistinguishable.",
    "The separation of B from C and D exceeds the seed-to-seed standard deviation, whereas C and D are statistically indistinguishable.\n\nWe also verify that the deployment failure is not an artifact of unbounded latent dynamics. A variant trained on the one-step objective with an explicit spectral constraint $\\rho(\\mA(\\vc))\\le0.99$ attains an $H=20$ rollout RMSE of $1.5681$, whereas the same constrained model trained under the scheduled-rollout objective attains $0.0412$. Enforcing spectral stability therefore does not repair the failure, whereas changing the training objective does."
))

# ---- D4: caption wording
R.append((
    "The seed spread at $H=20$ is at most $0.0011$ for B--D.",
    "The standard deviation at $H=20$ is at most $0.0011$ for B--D."
))

# ---- D2: reconcile the speed-up with Table I
R.append((
    "Second, RTI-SP is roughly $1.6\\times$ faster than RTI-RE because it avoids a full Transformer lifting-encoder evaluation per stage, and its $p95$ latency ($120$~ms) is well below the $\\sim200$~ms soft-robot sampling period.",
    "Second, RTI-SP is roughly $2.3\\times$ faster than RTI-RE at the median and $2.1\\times$ at $p95$, because it avoids a full Transformer lifting-encoder evaluation per stage, and its $p95$ latency ($120$~ms) is well below the $\\sim200$~ms soft-robot sampling period."
))

# ---- D3: document checkpoint selection and the absence of a spectral penalty
R.append((
    "The complete procedure is summarized in Algorithm~\\ref{alg:training}.",
    "For the reported predictor, the checkpoint with the lowest validation rollout loss over the fine-tuning stage is retained, and no spectral penalty is applied; the ablation of Section~\\ref{subsec:schedule_ablation} instead trains each variant for a fixed number of epochs without checkpoint selection. The complete procedure is summarized in Algorithm~\\ref{alg:training}."
))

# ---- D5: remove the "A-only" / strategy-A collision
R.append((
    "Table~\\ref{tab:diagnostics} reports the diagnostics measured on the frozen deployment predictor ($\\mA$-only, $r=2$, scheduled propagation) on the soft-robot validation set",
    "Table~\\ref{tab:diagnostics} reports the diagnostics measured on the frozen deployment predictor (strategy~C of Section~\\ref{subsec:schedule_ablation}: all parameters optimized, $r=2$, scheduled propagation) on the soft-robot validation set"
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
