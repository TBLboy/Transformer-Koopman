# -*- coding: utf-8 -*-
"""Move the numerical diagnostics out of Theory into Experiments, and compress
Scope and Non-Goals into a short remark (user rulings on the theory review).

- The 'Numerical Diagnostics for the Theoretical Analysis' subsection (intro,
  table, mechanism figure, three observations) moves into the Experiments section
  and is retitled 'Mechanism and Theory Diagnostics'.  Its label
  subsec:diagnostics is preserved so all existing references still resolve.
- 'Scope and Non-Goals' becomes a short remark at the end of the theory section;
  its label subsec:scope is preserved.
"""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")

EXP_LEADIN = ("This section reports the empirical diagnostics that assess the assumptions and "
              "quantities of the consistency analysis of Section~\\ref{sec:theory}.\n\n")

SCOPE_REMARK = r"""\begin{remark}[Scope of the analysis]
\label{subsec:scope}
The analysis is finite-horizon and concerns predictor consistency and local linearization accuracy. It does not establish global closed-loop stability, a common Lyapunov function, terminal invariant sets, or recursive feasibility under learned uncertainty. The regularity constants used for the empirical assessment are operating-region diagnostics rather than global certificates, all bounds concern the rolled-out latent predictor rather than true-plant tracking error, and $\mA(\vc)$ is a latent linearization parameterization rather than an exact Koopman invariant-subspace operator.
\end{remark}"""


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    assert "\ufeff" not in text, "unexpected BOM"
    nl = "\r\n" if "\r\n" in text else "\n"

    scope_start = text.index(r"\subsection{Scope and Non-Goals}")
    diag_start = text.index(r"\subsection{Numerical Diagnostics for the Theoretical Analysis}")
    control_start = text.index(r"\section{Real-Time Predictive Control}")
    comment_before_control = text.rindex("% =========================================================",
                                         0, control_start)

    diag_block = text[diag_start:comment_before_control]
    assert r"\label{subsec:diagnostics}" in diag_block
    assert r"\label{tab:diagnostics}" in diag_block
    assert r"\label{fig:mechanism}" in diag_block

    # remove both subsections from the theory section; append the scope remark there
    text = text[:scope_start] + SCOPE_REMARK + "\n\n" + text[comment_before_control:]
    print("theory: scope compressed to a remark, diagnostics removed")

    # retitle the diagnostics block and insert it into the experiments section
    diag_block = diag_block.replace(
        r"\subsection{Numerical Diagnostics for the Theoretical Analysis}",
        r"\subsection{Mechanism and Theory Diagnostics}", 1)
    assert diag_block.startswith(r"\subsection{Mechanism and Theory Diagnostics}")

    exp_marker = ("\\label{sec:experiments}\n"
                  "% =========================================================\n")
    i = text.index(exp_marker) + len(exp_marker)
    text = text[:i] + "\n" + EXP_LEADIN + diag_block.rstrip() + "\n\n" + text[i:]
    print("experiments: diagnostics subsection inserted")

    # the scope reference in the theory introduction now points to a remark
    old_ref = r"(Section~\ref{subsec:scope})"
    assert text.count(old_ref) == 1, "unexpected scope references: %d" % text.count(old_ref)
    text = text.replace(old_ref, r"(see the scope remark below)")

    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(text.replace("\r\n", "\n").split("\n")))
    print("OK")


if __name__ == "__main__":
    main()
