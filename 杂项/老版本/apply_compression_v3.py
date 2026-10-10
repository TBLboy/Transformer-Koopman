# -*- coding: utf-8 -*-
"""v3 compression pass: reduce narrative density and defensive wording.

P0  II-C merged into II-B; Related Work back to three subsections
P0  III-A ending compressed to one bridge sentence
P0  III-B R1/R2/R3 labels removed
P0  III-B length-H training segment moved to the training procedure (as H_R)
P0  Section IV opening compressed to one sentence
P0  L_R defence compressed; the no-bound disclaimer relocated to the theory scope remark
P1  EDMD pseudoinverse regression removed from III-A
P1  lifting-vs-context explanation compressed
P1  Definition keeps only the formal definition; the reading moves after it
P1  negative descriptions ("not an exact invariant-subspace operator", "not fixed LTI") removed
P1  spectral-stabilization discussion trimmed out of the training procedure
P1  Modeling Error Characterization shortened
P2  IV-A subsection retitled; Eq. (1) non-Markov note compressed
"""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")
R = []

# ---------------------------------------------------------------- Related Work
R.append((
    "\\subsection{Representation: Instantaneous versus History-Based Lifting}",
    "\\subsection{History-Based Koopman Representation}"
))
R.append((
    "\\subsection{Transition Adaptation: Context-Aware and Time-Varying Operators}",
    "\\subsection{Context-Dependent Koopman Dynamics and Recursive Prediction}"
))
R.append((
    "\\subsection{Real-Time and Scheduled Predictive Control}",
    "\\subsection{Real-Time Predictive Control}"
))
R.append((
    "\\subsection{Recursive Multi-Step Deployment}\n\n"
    "Multi-step training is also used in learned Koopman models to mitigate error accumulation under recursive "
    "prediction \\cite{lusch2018deep, otto2019linearly, azencot2020forecasting, wu2026multistep}, and is standard "
    "in neural system identification more broadly \\cite{forgione2021dynonet}; we therefore do not claim multi-step "
    "loss itself as novel. The issue is specific to history-conditioned dynamics: during recursive deployment the "
    "transition is repeatedly rescheduled from the predicted history, so the propagated latent state and conditioning "
    "context can depart from the encoder-consistent one-step distribution. Our rollout-aware procedure reproduces that "
    "scheduled propagation during training rather than merely extending a one-step objective over several horizons.",
    "Multi-step objectives have also been used in learned Koopman models to reduce recursive prediction error "
    "\\cite{lusch2018deep, otto2019linearly, azencot2020forecasting, wu2026multistep}, and are standard in neural "
    "system identification more broadly \\cite{forgione2021dynonet}, so multi-step loss itself is not the focus here. "
    "The additional issue in history-conditioned dynamics is that recursive prediction reschedules future transitions "
    "from predicted histories, causing both the latent state and the conditioning context to depart from their one-step "
    "training distribution. Our rollout-aware training targets this specific deployment mismatch."
))

# ---------------------------------------------------------------- Eq. (1) note
R.append((
    "where $\\vx_k \\in \\mathbb{R}^n$ is the measured state, $\\vu_k \\in \\mathbb{R}^m$ is the control input, and $F:\\mathbb{R}^n \\times \\mathbb{R}^m \\to \\mathbb{R}^n$ is an unknown nonlinear transition map. Here $\\vx_k$ is the measured state used for data-driven prediction; it need not constitute a complete Markov state of the underlying physical system, and \\eqref{eq:nonlinear_system} is used as an effective input--output description rather than as a full-state model. State-input trajectories $\\{(\\vx_k, \\vu_k)\\}$ are assumed to be available for data-driven modeling.",
    "where $\\vx_k \\in \\mathbb{R}^n$ is the measured state, $\\vu_k \\in \\mathbb{R}^m$ is the control input, and $F:\\mathbb{R}^n \\times \\mathbb{R}^m \\to \\mathbb{R}^n$ is an unknown nonlinear transition map. Here $\\vx_k$ denotes the measured coordinates used by the predictor; finite history is introduced below when these coordinates are not Markov-complete. State-input trajectories $\\{(\\vx_k, \\vu_k)\\}$ are assumed to be available for data-driven modeling."
))

# ---------------------------------------------------------------- EDMD regression removed
R.append((
    "The lifted dynamics are then approximated by a linear system $\\vz_{k+1} \\approx \\mA \\vz_k + \\mB \\vu_k$, with $\\mA$ and $\\mB$ identified from data. Given $M$ transitions, let $\\mZ = [\\vz_1, \\ldots, \\vz_M]$, $\\mZ^+ = [\\vz_2, \\ldots, \\vz_{M+1}]$, and $\\mU_{\\mathrm{data}} = [\\vu_1, \\ldots, \\vu_M]$; the finite-dimensional matrices are obtained from the least-squares problem\n"
    "\\begin{equation}\n"
    "    [\\mA \\; \\mB] = \\mZ^+ \\mOmega^\\dagger, \\qquad \\mOmega = \\begin{bmatrix} \\mZ \\\\ \\mU_{\\mathrm{data}} \\end{bmatrix},\n"
    "    \\label{eq:edmd_regression}\n"
    "\\end{equation}\n"
    "with $(\\cdot)^\\dagger$ the Moore--Penrose pseudoinverse. Instantaneous-state lifting may miss temporal information",
    "The lifted dynamics are then approximated by a linear system $\\vz_{k+1} \\approx \\mA \\vz_k + \\mB \\vu_k$, with $\\mA$ and $\\mB$ identified from data. Instantaneous-state lifting may miss temporal information"
))

# ---------------------------------------------------------------- III-A bridge compressed
R.append((
    "where $\\vw_k$ denotes the lifted-space approximation residual. In this work, $g_\\theta$ is implemented using a Transformer encoder. Temporal lifting makes recent trajectory information available in the latent state, but it does not by itself remove the restriction imposed by a single global lifted transition: a fixed $\\mA$ requires every history-dependent latent state to evolve under the same linear operator, which may be unnecessarily restrictive when the effective dynamics vary with recent trajectory context. Replacing the lifted dynamics by a fully nonlinear black-box predictor would remove that restriction but would discard the conditional-linear structure that makes the model usable for predictive control. These considerations motivate the prediction problem formulated next.",
    "where $\\vw_k$ denotes the lifted-space approximation residual. In this work, $g_\\theta$ is implemented using a Transformer encoder. Temporal lifting introduces recent trajectory information into the latent state; the remaining question is how to accommodate history-dependent variations in the lifted dynamics without abandoning a control-compatible structure."
))

# ---------------------------------------------------------------- III-B: segment moved out
R.append((
    "    \\label{eq:input_history_problem}\n\\end{equation}\nA length-$H$ training segment therefore contains the tuple $(\\mX_k,\\allowbreak \\mU_k^{\\mathrm{in}},\\allowbreak \\vu_{k:k+H-1},\\allowbreak \\vx_{k+1:k+H})$ and is extracted without crossing trajectory boundaries.\n\n",
    "    \\label{eq:input_history_problem}\n\\end{equation}\n\n"
))

# ---------------------------------------------------------------- III-B: R1/R2/R3 -> prose
R.append((
    "These considerations lead to three requirements for a control-oriented predictor. \\emph{R1:} the lifted representation should incorporate recent trajectory information while preserving the current measured state. \\emph{R2:} the lifted transition should be allowed to adapt to trajectory context, while remaining linear in the lifted state and the current input for a given context. \\emph{R3:} because future contexts are generated from the model's own predicted histories during recursive deployment, the predictor should remain accurate under this scheduled rollout rather than only on encoder-consistent one-step transitions.",
    "A control-oriented predictor should therefore exploit finite history to represent temporal information that the instantaneous measurement does not provide, allow the lifted transition to adapt to recent trajectory context while retaining linear propagation for a fixed context, and remain accurate when its own predicted histories are recursively fed back during multi-step prediction."
))

# ---------------------------------------------------------------- III-B closing pointer
R.append((
    "where the current control input enters through a context-independent linear channel. Section~\\ref{sec:methodology} realizes these requirements through a patch-based Transformer lifting map, a low-rank history-conditioned modulation of a shared nominal transition, and deployment-consistent scheduled training.",
    "where the current control input enters through a context-independent linear channel. Section~\\ref{sec:methodology} instantiates this predictor."
))

# ---------------------------------------------------------------- IV opening compressed
R.append((
    "Section~\\ref{sec:problem} identifies three requirements: history-aware representation, context-adaptive conditional-linear propagation, and consistency under recursively scheduled deployment. The proposed framework addresses them in three corresponding steps. A patch-based Transformer first constructs a state-preserving temporal lifting; a low-rank history-conditioned modulation then adapts a shared nominal lifted transition; finally, the model is trained under the same scheduled rollout used at deployment. We describe the lifting architecture, the training procedure, and the modeling error characterization in turn.",
    "We instantiate the predictor of Section~\\ref{sec:problem} using a patch-based temporal lifting, a history-conditioned low-rank transition, and deployment-consistent scheduled training."
))

# ---------------------------------------------------------------- IV-A subsection retitle
R.append((
    "\\subsection{Patch-Based Temporal Lifting Architecture}",
    "\\subsection{Temporal Lifting and History-Conditioned Transition}"
))

# ---------------------------------------------------------------- IV-A context roles compressed
R.append((
    "where $C_\\phi$ is a context network that observes the same state and input history carried by the augmented predictor state. The lifting map and the context map deliberately use different information. The lifting map consumes only the measured state history, so that the lifted state remains a compact, state-preserving representation of the current dynamical condition. The context map additionally consumes the past inputs, because the effective latent transition can depend not only on the current condition but also on how that condition was reached, and because past inputs are information that the state-history lifting map does not itself observe.",
    "where $C_\\phi$ is a context network. The lifting map uses the state history to construct a state-preserving representation, whereas the context map additionally uses the past inputs to condition the effective transition on how the current dynamical condition was reached."
))

# ---------------------------------------------------------------- Definition: definition only
R.append((
    "Throughout, $r=2$. The decomposition separates shared dynamics from context-dependent variation: $\\mA_0$ captures the nominal lifted evolution common across histories, while the low-rank correction restricts history-dependent adaptation to a small learned transition subspace, so that history selectively adjusts the nominal transition rather than regenerating the entire operator. History dependence is deliberately confined to the lifted transition: the current-input channel $\\mB$ is held context-independent, so that the internal evolution can adapt to the recent trajectory without changing the affine dependence on the current decision variable, which keeps the predictor control-affine for a given context.",
    "Throughout, $r=2$."
))

# ---------------------------------------------------------------- post-Definition reading
R.append((
    "Given $\\vc_k$, the lifted dynamics \\eqref{eq:temporal_dynamics} remain linear in $(\\vz_k,\\vu_k)$; history dependence enters only through $\\mA(\\vc_k)$. This is a \\emph{history-conditioned, low-rank parameter-varying} Koopman family rather than an exact Koopman invariant-subspace operator, and it is not a fixed linear time-invariant (LTI) model. The fixed projection \\eqref{eq:decoder_projection} still recovers the physical state exactly. Ablations (Section~\\ref{sec:experiments}) show that the predictive benefit is concentrated in the $\\mA$-modulation and that $r=2$ is the minimal near-optimal rank.",
    "$\\mA_0$ represents the shared nominal lifted dynamics, while the low-rank term provides a structured context-dependent correction. Context dependence is confined to $\\mA(\\vc)$, while $\\mB$ remains fixed so that the current input enters through a common affine channel. The resulting model is a history-conditioned parameter-varying lifted system that remains linear in $(\\vz_k,\\vu_k)$ for a fixed context, and the fixed projection \\eqref{eq:decoder_projection} recovers the physical state exactly. Ablations (Section~\\ref{sec:experiments}) show that the predictive benefit is concentrated in the $\\mA$-modulation and that $r=2$ is the minimal near-optimal rank."
))

# ---------------------------------------------------------------- training: segment introduced
R.append((
    "The projection $\\mC$ is structurally fixed throughout training, as in Definition~\\ref{def:hcltk}.",
    "The projection $\\mC$ is structurally fixed throughout training, as in Definition~\\ref{def:hcltk}. Training operates on length-$H_R$ segments cut from single trajectories: each segment provides the history window $\\mX_k$, the past-input history $\\mU^{\\mathrm{in}}_k$, the future inputs $\\vu_{k:k+H_R-1}$, and the future states $\\vx_{k+1:k+H_R}$ as prediction targets, and segments do not cross trajectory boundaries."
))

# ---------------------------------------------------------------- L_R defence compressed
R.append((
    "At deployment the transition consumes \\emph{propagated} latents $\\vz^{P}$, whose distribution differs from the encoder-generated one-step distribution on which Stage~0 is fitted. Definition~\\ref{def:rollout_aware} is an \\emph{algorithmic design} rather than a theoretical result: no statement in Section~\\ref{sec:theory} uses $\\mathcal{L}_R$, and we do not claim that minimizing it implies any bound on the rollout-consistency defect $\\epsilon_k$, the normalized rollout defect $d_{\\mathcal M}(H)$, or the Lipschitz constant $\\mLf$ of Section~\\ref{sec:theory}. We claim only that $\\mathcal{L}_R$ \\emph{mitigates} latent rollout inconsistency and improves deployment-distribution accuracy. The evidence for that claim, and its limits, are discussed with the diagnostics in Section~\\ref{sec:experiments}.",
    "At deployment the transition consumes \\emph{propagated} latents $\\vz^{P}$, whose distribution differs from the encoder-generated one-step distribution on which Stage~0 is fitted. The rollout objective is an algorithmic training mechanism rather than a theoretical guarantee: no statement in Section~\\ref{sec:theory} uses $\\mathcal{L}_R$, and Section~\\ref{sec:theory} analyzes rollout consistency independently through finite-horizon error propagation."
))

# ---------------------------------------------------------------- spectral discussion trimmed
R.append((
    "Minimizing $\\mathcal{L}_R$ trains the operator on the propagated-latent distribution that arises at deployment, rather than on the encoder-generated one-step distribution---precisely the distribution shift analyzed in Section~\\ref{subsec:rollout}. We deliberately do \\emph{not} apply a closed-form EDMD refit: once the transition is history-conditioned, the regression target is no longer a single operator $(\\mA,\\mB)$ shared across all contexts, and the scheduled objective already constrains the propagated distribution. We also do not rely on spectral stabilization; Remark~\\ref{rem:spectral} and Section~\\ref{sec:experiments} show that constraining $\\rho(\\mA(\\vc))<1$ does not restore scheduled-rollout accuracy, whereas changing the training objective does.",
    "Minimizing $\\mathcal{L}_R$ trains the operator on the propagated-latent distribution that arises at deployment, rather than on the encoder-generated one-step distribution---precisely the distribution shift analyzed in Section~\\ref{subsec:rollout}. No closed-form EDMD refit is applied after the transition is activated, since the regression target is no longer a single operator shared across all contexts. Spectral stabilization is not relied upon: Remark~\\ref{rem:spectral} shows that constraining $\\rho(\\mA(\\vc))<1$ does not restore scheduled-rollout accuracy."
))

# ---------------------------------------------------------------- modeling error shortened
R.append((
    "where $\\vz_{k+1} = g_\\theta(\\mX_{k+1})$ and $\\vz_k=g_\\theta(\\mX_k)$. In general, $\\vw_k \\neq \\mathbf{0}$ even after training. It is a \\emph{data-consistency} residual, evaluated on the recorded histories, and is therefore distinct from the \\emph{rollout}-consistency defect $\\epsilon_k$ of Proposition~\\ref{prop:propagation}, which is evaluated on predictor-generated histories; the two are not identified. When the state and input remain within a compact set, the residual is bounded, and in practice it is estimated on a held-out validation set. Crucially, a small one-step residual does \\emph{not} guarantee accurate recursive rollout; the propagation of this residual is analyzed in Section~\\ref{subsec:rollout} and motivates the rollout-aware objective \\eqref{eq:loss_rollout}. The projection identity $\\mC\\vz^{E}_{k+1}=\\vx_{k+1}$ holds \\emph{structurally} for the encoder-consistent latent state, because the lifted state carries the physical state in its first $n$ coordinates. In contrast, consistency of the dynamically propagated latent with the next observation, $\\mC(\\mA(\\vc_k)\\vz_k+\\mB\\vu_k)\\approx\\vx_{k+1}$, is enforced only approximately, through the prediction objectives \\eqref{eq:loss_one_step} and \\eqref{eq:loss_rollout}.",
    "where $\\vz_{k+1} = g_\\theta(\\mX_{k+1})$ and $\\vz_k=g_\\theta(\\mX_k)$. Here $\\vw_k$ is evaluated on recorded histories and measures one-step data consistency. It is distinct from the rollout-consistency defect $\\epsilon_k$ of Proposition~\\ref{prop:propagation}, which is evaluated on predictor-generated histories. A small one-step residual alone does not imply accurate recursive rollout; the propagation of this residual is analyzed in Section~\\ref{subsec:rollout} and motivates the rollout-aware objective \\eqref{eq:loss_rollout}."
))

# ---------------------------------------------------------------- scope remark gains the disclaimer
R.append((
    "and $\\mA(\\vc)$ is a latent linearization parameterization rather than an exact Koopman invariant-subspace operator.",
    "and $\\mA(\\vc)$ is a latent linearization parameterization rather than an exact Koopman invariant-subspace operator. The rollout objective $\\mathcal{L}_R$ of Section~\\ref{sec:training} is likewise an algorithmic training mechanism: minimizing it is not claimed to imply any bound on $\\epsilon_k$, $d_{\\mathcal M}(H)$, or $\\mLf$."
))


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    assert "\ufeff" not in raw, "unexpected BOM"
    nl = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")
    for i, (old, new) in enumerate(R, 1):
        c = text.count(old)
        assert c == 1, "item %d: expected 1, found %d\n--- %s" % (i, c, old[:110])
        text = text.replace(old, new)
        print("applied %d" % i)
    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(text.split("\n")))
    print("OK")


if __name__ == "__main__":
    main()
