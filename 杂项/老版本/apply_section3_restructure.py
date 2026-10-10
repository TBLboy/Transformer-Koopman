# -*- coding: utf-8 -*-
"""Apply the Section III-B / III-C deep-review restructuring to Main.tex.

P0-1  delete the standalone III-B "Background on Transformer Encoders"
P0-2  rewrite III-C as a clean III-B "Learning Problem"
P0-3  dataset now explicitly carries the past-input history U_k^in
P0-4  dataset defined over trajectories / length-H training segments (not isolated
      one-step tuples), so Stage 0 (H=1) and Stage 1 (H=H_R) are both supported
P0-5  remove Section IV-A dependencies on sec:transformer_background,
      eq:general_embed, eq:pos_enc and eq:dataset
P0-6  fix the U notation collision: the EDMD input snapshot matrix becomes U_data
P1-7/8/9  the problem statement no longer enumerates A_0,U,V,g,C_phi; it uses the
      abstract A_psi(X_k,U_k^in) and a finite-horizon recursive-error objective
P2-13 generic "measured task-space state" -> "measured state"
P2-14 drop the overstated computational-efficiency claim for patch tokenization
Also: Section III opening paragraph no longer promises a Transformer tutorial.
"""
import re
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")


def splice(text, start_marker, end_marker, new, occurrence=1):
    """Replace the span [start_marker, end_marker] inclusive with new."""
    start = -1
    for _ in range(occurrence):
        start = text.index(start_marker, start + 1)
    end = text.index(end_marker, start) + len(end_marker)
    return text[:start] + new + text[end:]


NEW_PROBLEM = r"""We assume that the available data consist of recorded state--input trajectories
\begin{equation}
    \mathcal{D} = \{\tau^{(j)}\}_{j=1}^{N_{\mathrm{tr}}}, \qquad
    \tau^{(j)} = \{(\vx_t^{(j)}, \vu_t^{(j)})\}_{t=0}^{T_j}.
    \label{eq:trajectory_dataset}
\end{equation}
For each admissible time index $k$, the state-history window $\mX_k$ is defined by \eqref{eq:history_window}, and the aligned past-input history is
\begin{equation}
    \mU_k^{\mathrm{in}} = [\vu_{k-P+1}^{\top}, \ldots, \vu_{k-1}^{\top}]^{\top}
    \in \mathbb{R}^{(P-1)m}.
    \label{eq:input_history_problem}
\end{equation}
A length-$H$ training segment therefore contains $(\mX_k, \mU_k^{\mathrm{in}}, \vu_{k:k+H-1}, \vx_{k+1:k+H})$ and is extracted without crossing trajectory boundaries.

The learning objective is to construct a state-preserving temporal lifting
\begin{equation}
    \vz_k = g_\theta(\mX_k), \qquad \mC\vz_k = \vx_k,
    \label{eq:problem_lifting}
\end{equation}
together with a history-conditioned lifted predictor of the form
\begin{equation}
    \hat{\vz}_{k+1} = \mathcal{A}_{\psi}(\mX_k, \mU_k^{\mathrm{in}})\,\vz_k + \mB\vu_k,
    \qquad \hat{\vx}_{k+1} = \mC\hat{\vz}_{k+1},
    \label{eq:problem_predictor}
\end{equation}
where the current control input enters through a context-independent linear channel. We seek a predictor that maintains small finite-horizon recursive prediction error when the history is updated from its own predicted outputs, while retaining a conditional-linear structure suitable for predictive control. Section~\ref{sec:methodology} instantiates $\mathcal{A}_{\psi}$ using the proposed history-conditioned low-rank transition and specifies the Transformer lifting map."""

REPLACE = [
    # --- P0-2: rename the subsection ---------------------------------------------
    (r"\subsection{Problem Formulation}", r"\subsection{Learning Problem}"),

    # --- Section III opening paragraph -------------------------------------------
    (r"In this section, we briefly review the Koopman framework for nonlinear systems and introduce the key idea of temporal lifting, which forms the core of our proposed method and will be detailed in Section~\ref{sec:methodology}. We also provide the necessary background on Transformer encoders and formulate the learning problem addressed in this work.",
     r"In this section, we review the controlled Koopman formulation, introduce finite-history lifting, and state the data-driven learning problem considered in this work. The specific Transformer realization and the history-conditioned low-rank transition are developed in Section~\ref{sec:methodology}."),

    # --- P2-13: generic state terminology ----------------------------------------
    (r"where $\vx_k \in \mathbb{R}^n$ is the measured task-space state,",
     r"where $\vx_k \in \mathbb{R}^n$ is the measured state,"),
    (r"particularly when the measured task-space state does not by itself characterize the underlying dynamics.",
     r"particularly when the measured state does not by itself characterize the underlying dynamics."),

    # --- P0-6: U notation collision (EDMD input snapshot matrix) ------------------
    (r"and $\mU = [\vu_1, \ldots, \vu_M]$;",
     r"and $\mU_{\mathrm{data}} = [\vu_1, \ldots, \vu_M]$;"),
    (r"    [\mA \; \mB] = \mZ^+ \mOmega^\dagger, \qquad \mOmega = \begin{bmatrix} \mZ \\ \mU \end{bmatrix},",
     r"    [\mA \; \mB] = \mZ^+ \mOmega^\dagger, \qquad \mOmega = \begin{bmatrix} \mZ \\ \mU_{\mathrm{data}} \end{bmatrix},"),

    # --- P0-5: remove IV-A dependency on the deleted III-B -----------------------
    (r"which serves as the concrete instantiation of the generic token $\mathbf{v}^{(i)}$ introduced in Section~\ref{sec:transformer_background}. In this framework, each token corresponds to a vectorized temporal patch extracted from the history window. These tokens are then mapped into the Transformer embedding space through a shared linear layer, as defined in \eqref{eq:general_embed}, with $\mathbf{v}^{(i)} = \vq_k^{(i)}$ and $d_{\mathrm{in}} = pn$.",
     r"which is then mapped into the Transformer embedding space through a shared linear layer,"),

    # --- P0-5: remove IV-A dependency on eq:pos_enc / III-B ----------------------
    (r"After the vectorization process, the temporal patch sequence is formed, where each token corresponds to a vectorized temporal patch. This sequence of tokens is then augmented with sinusoidal positional encoding, as defined in \eqref{eq:pos_enc}, to incorporate positional information. The resulting sequence is then processed by the $L$-layer Transformer encoder described in Section~\ref{sec:transformer_background}. ",
     r"The token sequence is augmented with sinusoidal positional encoding \cite{vaswani2017attention} to incorporate temporal order, and is then processed by an $L$-layer Transformer encoder:"),

    # --- P0-5: Algorithm 1 dataset reference -------------------------------------
    (r"\STATE \textbf{Input:} Dataset $\mathcal{D}$ \eqref{eq:dataset}",
     r"\STATE \textbf{Input:} Trajectory dataset $\mathcal{D}$ \eqref{eq:trajectory_dataset}"),
    (r"    \FOR{each mini-batch $\mathcal{B} \subset \mathcal{D}$}",
     r"    \FOR{each mini-batch of length-$H_R$ segments $\mathcal{B}$ drawn from $\mathcal{D}$}"),
]


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    assert "\ufeff" not in text, "unexpected BOM"
    nl = "\r\n" if "\r\n" in text else "\n"

    # ---- P0-1: delete the standalone Transformer background subsection ----------
    sub_marker = r"\subsection{Background on Transformer Encoders}"
    next_sub = r"\subsection{Problem Formulation}"
    start = text.index(sub_marker)
    # back up over the preceding comment separator line
    start = text.rindex("% ---------------------------------------------------------", 0, start)
    end = text.index(next_sub)
    removed = text[start:end]
    assert "permutation-invariant" in removed and r"\label{eq:pos_enc}" in removed
    text = text[:start] + text[end:]
    print("deleted III-B (%d chars)" % len(removed))

    # ---- P0-2: rewrite the problem-formulation body -----------------------------
    text = splice(text,
                  r"Given the system \eqref{eq:nonlinear_system}",
                  r"(Section~\ref{sec:control}).",
                  NEW_PROBLEM)
    print("rewrote Learning Problem body")

    # ---- remaining textual replacements -----------------------------------------
    for old, new in REPLACE:
        n = text.count(old)
        assert n == 1, "expected 1 occurrence, got %d for: %s" % (n, old[:80])
        text = text.replace(old, new)
    print("applied %d replacements" % len(REPLACE))

    # ---- P2-14: drop the overstated efficiency claim (spans source lines) -------
    text, n = re.subn(
        r"This patch-based\s+tokenization reduces the sequence length from \$P\$ to \$N=P/p\$, thereby\s+"
        r"improving computational efficiency while preserving local temporal\s+structure within each patch\.",
        r"This patch-based tokenization reduces the sequence length from $P$ to $N=P/p$ "
        r"while preserving local temporal structure within each patch.",
        text)
    assert n == 1, "P2-14 replacement matched %d times" % n
    print("applied P2-14 efficiency wording fix")

    assert "eq:general_embed" not in text
    assert "sec:transformer_background" not in text
    assert "eq:dataset" not in text

    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(text.replace("\r\n", "\n").split("\n")))
    print("OK")


if __name__ == "__main__":
    main()
