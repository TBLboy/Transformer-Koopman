# -*- coding: utf-8 -*-
"""Theory consolidation pass (review: definitions closure + final consolidation).

P0-1  w_k (data-consistency residual) is no longer equated with epsilon_k
P0-2  Theorem 1 restated on a reference SEQUENCE: F* removed, bound uses the
      one-step reference discrepancy delta*_k, uniform-epsilon form is a corollary
P0-3  L_R moved from Theory into the Methodology training procedure; L_con deleted
P1    measured-state clarification; common prescribed input sequence; Prop.1 and
      RTI proposition renamed; C^2 -> piecewise C^2 (ReLU feed-forward blocks);
      empirical estimates written with hats
P2    r_k -> r^z_k and Taylor remainder r_i -> R_i; section retitled
"""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")

NEW_LR_BLOCK = r"""\begin{definition}[Rollout-Aware Scheduled Objective]
\label{def:rollout_aware}
With the scheduled rollout $\vz^{P}$ (latent propagated, context re-scheduled from the decoded history) and uniform weights $w_i=1/H_R$,
\begin{equation}
    \mathcal{L}_R=\sum_k\sum_{i=1}^{H_R} w_i\,\big\|\mC\vz^{P}_{k+i}-\vx_{k+i}\big\|_2^2 .
    \label{eq:loss_rollout}
\end{equation}
\end{definition}

At deployment the transition consumes \emph{propagated} latents $\vz^{P}$, whose distribution differs from the encoder-generated one-step distribution on which Stage~0 is fitted. Definition~\ref{def:rollout_aware} is an \emph{algorithmic design} rather than a theoretical result: no statement in Section~\ref{sec:theory} uses $\mathcal{L}_R$, and we do not claim that minimizing it implies any bound on the rollout-consistency defect $\epsilon_k$, the normalized rollout defect $d_{\mathcal M}(H)$, or the Lipschitz constant $\mLf$ of Section~\ref{sec:theory}. We claim only that $\mathcal{L}_R$ \emph{mitigates} latent rollout inconsistency and improves deployment-distribution accuracy; we do not claim it guarantees strict manifold invariance. The claim that one-step training insufficiently constrains the rollout distribution is supported by the \emph{conjunction} of four observations: $\epsilon_k>0$, increasing $d_{\mathcal M}(H)$, failure of naive latent propagation, and recovery under rollout-aware training. No single observation is sufficient on its own.

\textbf{Stage~1 (rollout-aware scheduled training).} We then activate"""

REPLACE = [
    # ---------------- P0-1: w_k is not epsilon_k ------------------------------
    (r"In general, $\vw_k \neq \mathbf{0}$ even after training; its norm equals the one-step consistency defect, $\|\vw_k\|_2=\epsilon_k$, of Proposition~\ref{prop:propagation} (both are evaluated at the encoder-consistent latent).",
     r"In general, $\vw_k \neq \mathbf{0}$ even after training. It is a \emph{data-consistency} residual, evaluated on the recorded histories, and is therefore distinct from the \emph{rollout}-consistency defect $\epsilon_k$ of Proposition~\ref{prop:propagation}, which is evaluated on predictor-generated histories; the two are not identified."),

    # ---------------- P1: measured state need not be Markov --------------------
    (r"and $F:\mathbb{R}^n \times \mathbb{R}^m \to \mathbb{R}^n$ is an unknown nonlinear transition map. State-input trajectories $\{(\vx_k, \vu_k)\}$ are assumed to be available for data-driven modeling.",
     r"and $F:\mathbb{R}^n \times \mathbb{R}^m \to \mathbb{R}^n$ is an unknown nonlinear transition map. Here $\vx_k$ is the measured state used for data-driven prediction; it need not constitute a complete Markov state of the underlying physical system, and \eqref{eq:nonlinear_system} is used as an effective input--output description rather than as a full-state model. State-input trajectories $\{(\vx_k, \vu_k)\}$ are assumed to be available for data-driven modeling."),

    # ---------------- P0-3: move L_R into Methodology -------------------------
    (r"\textbf{Stage~1 (rollout-aware scheduled training).} We then activate", NEW_LR_BLOCK),

    # ---------------- P2: retitles --------------------------------------------
    (r"\section{Finite-Horizon Theory}", r"\section{Finite-Horizon Consistency Analysis}"),
    (r"\begin{proposition}[Finite-History Markovization]",
     r"\begin{proposition}[Finite-History Predictor Markovization]"),
    (r"\begin{proposition}[RTI Local Approximation]",
     r"\begin{proposition}[Local Linearization Remainder Bound]"),

    # ---------------- P1: C^2 -> piecewise C^2 --------------------------------
    (r"On a neighborhood of the nominal RTI trajectory, $\mF_\Theta$ is twice continuously differentiable with bounded second derivative, $\|\mathrm{D}^2\mF_\Theta\|_2\le\mMF$, where $\|\cdot\|_2$ denotes the operator norm of the second-derivative bilinear form.",
     r"On a neighborhood of the nominal RTI trajectory, $\mF_\Theta$ is piecewise twice continuously differentiable with bounded second derivative, $\|\mathrm{D}^2\mF_\Theta\|_2\le\mMF$ wherever it exists, where $\|\cdot\|_2$ denotes the operator norm of the second-derivative bilinear form. The nominal point and its perturbation segment are assumed to meet finitely many smooth regions, so that the integral remainder below is well defined."),
    (r"we take these as standing regularity conditions on the learned components, satisfied by the smooth networks used here.",
     r"we take these as standing regularity conditions on the learned components. They hold for the networks used here: the context map and the modulation use $\tanh$ activations, the patch embedding, pooling and projection layers are affine, and the Transformer feed-forward blocks are piecewise affine with ReLU units, so $\mF_\Theta$ is Lipschitz and piecewise smooth rather than globally $\mathcal{C}^2$."),

    # ---------------- P2: symbol cleanup --------------------------------------
    (r"\vr_k=\mA(\vc_k)\vz^{E}_k+\mB\vu_k-\vz^{E}_{k+1}",
     r"\vr^{z}_k=\mA(\vc_k)\vz^{E}_k+\mB\vu_k-\vz^{E}_{k+1}"),
    (r"where $\|\vr_k\|_2=\epsilon_k$.", r"where $\|\vr^{z}_k\|_2=\epsilon_k$."),
    (r"\mA_{k+H-1}\cdots\mA_{k+i+1}\,\vr_{k+i},",
     r"\mA_{k+H-1}\cdots\mA_{k+i+1}\,\vr^{z}_{k+i},"),
    (r"with $\|\ve_k\|_2=d_k$ and $\|\vr_{k+i}\|_2=\epsilon_{k+i}$",
     r"with $\|\ve_k\|_2=d_k$ and $\|\vr^{z}_{k+i}\|_2=\epsilon_{k+i}$"),
    (r"\mF_\Theta(\bar\eta_i)+\mathrm{D}\mF_\Theta(\bar\eta_i)\,\delta\eta_i+\vr_i ,",
     r"\mF_\Theta(\bar\eta_i)+\mathrm{D}\mF_\Theta(\bar\eta_i)\,\delta\eta_i+\mathcal{R}_i ,"),
    (r"    \vr_i=\int_0^1(1-s)\,\mathrm{D}^2\mF_\Theta\big(\bar\eta_i+s\delta\eta_i\big)\big[\delta\eta_i,\delta\eta_i\big]\,\mathrm{d}s ,",
     r"    \mathcal{R}_i=\int_0^1(1-s)\,\mathrm{D}^2\mF_\Theta\big(\bar\eta_i+s\delta\eta_i\big)\big[\delta\eta_i,\delta\eta_i\big]\,\mathrm{d}s ,"),
    (r"    \|\vr_i\|_2 \le \frac{\mMF}{2}\big\|\delta\eta_i\big\|_2^2",
     r"    \|\mathcal{R}_i\|_2 \le \frac{\mMF}{2}\big\|\delta\eta_i\big\|_2^2"),
    (r"    \|\vr_i\|_2" + "\n" + r"    &\le\int_0^1(1-s)\,\big\|\mathrm{D}^2\mF_\Theta(\bar\eta_i+s\delta\eta_i)\big\|_2\,\|\delta\eta_i\|_2^2\,\mathrm{d}s \\",
     r"    \|\mathcal{R}_i\|_2" + "\n" + r"    &\le\int_0^1(1-s)\,\big\|\mathrm{D}^2\mF_\Theta(\bar\eta_i+s\delta\eta_i)\big\|_2\,\|\delta\eta_i\|_2^2\,\mathrm{d}s \\"),

    # ---------------- P0-2: remark updated (F* no longer exists) ---------------
    (r"The uniform mismatch bound $\epsilon$ in Theorem~\ref{thm:fh} and the encoder-consistency defect $\epsilon_k$ in Proposition~\ref{prop:propagation} serve different purposes and should not be identified. The former bounds the discrepancy between the reference finite-history augmented transition $\mF^{\star}$ and the learned transition $\mF_\Theta$ over the operating set, whereas the latter measures the one-step discrepancy between the propagated and the encoder-consistent latent states along sampled trajectories. Accordingly, the empirical statistics of $\epsilon_k$ are not used as a certified estimate of $\epsilon$.",
     r"The uniform bound $\epsilon$ in Theorem~\ref{thm:fh} and the encoder-consistency defect $\epsilon_k$ in Proposition~\ref{prop:propagation} serve different purposes and should not be identified. The former bounds the one-step reference discrepancy $\delta^{\star}_k$ between the recorded reference augmented sequence and the learned transition $\mF_\Theta$ over the operating set, whereas the latter measures the one-step discrepancy between the propagated and the encoder-consistent latent states along the predictor's own rollout. The data-consistency residual $\vw_k$ of Section~\ref{subsec:modeling_error} is a third quantity, evaluated on the recorded histories, and coincides with neither. Accordingly, the empirical statistics of $\epsilon_k$ are not used as a certified estimate of $\epsilon$."),
    (r"\begin{remark}[$\epsilon$ versus $\epsilon_k$]", r"\begin{remark}[$\epsilon$, $\epsilon_k$, and $\vw_k$]"),

    # ---------------- P1: hat the empirical estimate --------------------------
    (r"Since the empirical Lipschitz constant satisfies $\mLf\approx1.45>1$",
     r"Since the empirical Lipschitz constant satisfies $\widehat{\mLf}\approx1.45>1$"),
]


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    assert "\ufeff" not in text, "unexpected BOM"
    nl = "\r\n" if "\r\n" in text else "\n"

    # ---- P0-3: delete the Theory subsection that redefined L_R and L_con -------
    start = text.index(r"\subsection{Rollout-Aware Scheduled Training}")
    end = text.index(r"\subsection{Finite-Horizon Prediction Error Bound}")
    removed = text[start:end]
    assert r"\mathcal{L}_{\mathrm{con}}" in removed and r"\label{def:rollout_aware}" in removed
    text = text[:start] + text[end:]
    print("deleted Theory training subsection (%d chars)" % len(removed))

    # ---- P0-2: reference-sequence reformulation of Theorem 1 ------------------
    setup_start = text.index(r"To state the bound we place the reference and learned transitions")
    setup_end = text.index(r"\begin{assumption}[Operating-set model mismatch]")
    new_setup = (
        "To state the bound we compare the learned predictor with a \\emph{reference augmented "
        "sequence} built directly from the recorded observations, rather than postulating a "
        "deterministic reference transition for the plant. Let\n"
        "\\begin{equation}\n"
        "    \\vxi^{\\star}_k=\\mathrm{col}\\big(\\vx_{k-P+1:k},\\,\\vu_{k-P+1:k-1},\\,g_\\theta(\\mX_k)\\big)\n"
        "    \\label{eq:true_augmented}\n"
        "\\end{equation}\n"
        "denote the reference augmented state built from the true observations and the "
        "encoder-consistent latent, and let $\\vxi^{\\star}_{k+1}$ be its successor along the "
        "recorded trajectory. The reference sequence consists of measured quantities; no "
        "deterministic reference map is assumed to generate it, so the finite observed history is "
        "never asserted to Markovize the underlying plant. The learned augmented transition "
        "$\\mF_\\Theta$ is the map of Proposition~\\ref{prop:markov}, which propagates the latent "
        "and feeds back the decoded output $\\hat{\\vx}=\\mC\\vz^{P}$. We therefore measure the "
        "learned model by its one-step discrepancy on the reference sequence,\n"
        "\\begin{equation}\n"
        "    \\delta^{\\star}_k=\\big\\|\\vxi^{\\star}_{k+1}-\\mF_\\Theta(\\vxi^{\\star}_k,\\vu_k)\\big\\|_2 .\n"
        "    \\label{eq:ref_discrepancy}\n"
        "\\end{equation}\n"
        "This quantity bundles the physical modeling error, the finite-history truncation error, "
        "the learned transition error, and the difference between the encoder-consistent and the "
        "propagated latent updates.\n\n")
    text = text[:setup_start] + new_setup + text[setup_end:]

    # assumption as:mismatch
    as_start = text.index(r"\begin{assumption}[Operating-set model mismatch]")
    as_end = text.index(r"\begin{assumption}[Lipschitz continuity of the learned transition]")
    new_as = (
        "\\begin{assumption}[Operating-set reference discrepancy]\n"
        "\\label{as:mismatch}\n"
        "There exist a compact operating set $\\Omega$ and a finite constant $\\epsilon\\ge0$ such "
        "that, along the reference sequence and at every step of the considered horizon, the "
        "one-step reference discrepancy \\eqref{eq:ref_discrepancy} satisfies "
        "$\\delta^{\\star}_k\\le\\epsilon$, equivalently\n"
        "\\begin{equation}\n"
        "    \\big\\|\\vxi^{\\star}_{k+1}-\\mF_\\Theta(\\vxi^{\\star}_k,\\vu_k)\\big\\|_2\\le\\epsilon .\n"
        "    \\label{eq:as_mismatch}\n"
        "\\end{equation}\n"
        "We additionally require that the reference and predicted trajectories remain in $\\Omega$ "
        "over the considered horizon; this condition is used explicitly in Theorem~\\ref{thm:fh}.\n"
        "\\end{assumption}\n\n")
    text = text[:as_start] + new_as + text[as_end:]

    # theorem statement
    thm_start = text.index(r"\begin{theorem}[Finite-Horizon Prediction Error Bound]")
    proof_anchor = text.index("For one step,")
    thm_end = text.rindex(r"\begin{proof}", 0, proof_anchor)
    new_thm = (
        "\\begin{theorem}[Finite-Horizon Prediction Error Bound]\n"
        "\\label{thm:fh}\n"
        "For a common prescribed input sequence $\\{\\vu_k,\\ldots,\\vu_{k+H-1}\\}$, suppose that the "
        "reference and predicted trajectories remain in the operating set $\\Omega$ over the horizon "
        "$H$. Under Assumptions~\\ref{as:mismatch} and \\ref{as:lipschitz}, and with "
        "$e_k=\\vxi^{\\star}_k-\\hat{\\vxi}_k$,\n"
        "\\begin{equation}\n"
        "    \\|e_{k+H}\\|_2 \\le \\mLf^{H}\\|e_k\\|_2+\\sum_{i=0}^{H-1}\\mLf^{H-1-i}\\,\\delta^{\\star}_{k+i}.\n"
        "    \\label{eq:fh_bound}\n"
        "\\end{equation}\n"
        "If in addition the reference discrepancy is uniformly bounded by $\\epsilon$ as in "
        "Assumption~\\ref{as:mismatch}, then\n"
        "\\begin{equation}\n"
        "    \\|e_{k+H}\\|_2 \\le \\mLf^{H}\\|e_k\\|_2+\\epsilon\\sum_{j=0}^{H-1}\\mLf^{j}.\n"
        "    \\label{eq:fh_bound_uniform}\n"
        "\\end{equation}\n"
        "If the horizon is initialized from the same measured history and the corresponding "
        "encoder-consistent latent state, i.e. $\\hat{\\mX}_k=\\mX_k$ and "
        "$\\vz^{P}_k=g_\\theta(\\mX_k)$, then $e_k=0$ and "
        "$\\|e_{k+H}\\|_2\\le\\epsilon\\sum_{j=0}^{H-1}\\mLf^{j}$. The bound compares the learned "
        "predictor with the recorded reference trajectory under a \\emph{common} input sequence; it "
        "is not a closed-loop tracking-error or robustness statement. Here $\\epsilon$ is the "
        "uniform bound of Assumption~\\ref{as:mismatch}, not the trajectory-wise encoder-consistency "
        "defect $\\epsilon_k$ of Proposition~\\ref{prop:propagation}, nor the data-consistency "
        "residual $\\vw_k$ of Section~\\ref{subsec:modeling_error}.\n"
        "\\end{theorem}\n\n")
    text = text[:thm_start] + new_thm + text[thm_end:]

    # theorem proof
    proof_anchor = text.index("For one step,")
    pf_start = text.rindex(r"\begin{proof}", 0, proof_anchor)
    pf_end = text.index(r"\begin{remark}[$\epsilon$ versus $\epsilon_k$]")
    new_pf = (
        "\\begin{proof}\n"
        "For one step, using the recorded successor $\\vxi^{\\star}_{k+1}$,\n"
        "\\begin{align*}\n"
        "    \\|e_{k+1}\\|_2\n"
        "    &=\\big\\|\\vxi^{\\star}_{k+1}-\\mF_\\Theta(\\hat{\\vxi}_k,\\vu_k)\\big\\|_2 \\\\\n"
        "    &\\le\\big\\|\\vxi^{\\star}_{k+1}-\\mF_\\Theta(\\vxi^{\\star}_k,\\vu_k)\\big\\|_2\n"
        "      +\\big\\|\\mF_\\Theta(\\vxi^{\\star}_k,\\vu_k)-\\mF_\\Theta(\\hat{\\vxi}_k,\\vu_k)\\big\\|_2 \\\\\n"
        "    &\\le\\delta^{\\star}_k+\\mLf\\|e_k\\|_2 ,\n"
        "\\end{align*}\n"
        "by \\eqref{eq:ref_discrepancy} and Assumption~\\ref{as:lipschitz}, which applies at every "
        "step because the trajectories remain in $\\Omega$ over the horizon. Unrolling the recursion "
        "yields \\eqref{eq:fh_bound}; bounding each $\\delta^{\\star}_{k+i}$ by $\\epsilon$ yields "
        "\\eqref{eq:fh_bound_uniform}.\n"
        "\\end{proof}\n\n")
    text = text[:pf_start] + new_pf + text[pf_end:]

    # ---- remaining literal replacements ---------------------------------------
    for old, new in REPLACE:
        cnt = text.count(old)
        assert cnt == 1, "expected 1 occurrence, got %d for: %s" % (cnt, old[:80])
        text = text.replace(old, new)
    print("applied %d replacements" % len(REPLACE))

    for gone in [r"\mF^{\star}", r"\mathcal{L}_{\mathrm{con}}", r"eq:loss_con"]:
        assert gone not in text, "still present: %s" % gone

    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(text.replace("\r\n", "\n").split("\n")))
    print("OK")


if __name__ == "__main__":
    main()
