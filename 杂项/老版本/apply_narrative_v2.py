# -*- coding: utf-8 -*-
"""Apply the remaining v2 narrative items (P1/P2).

#7  explain the different roles of the X-only lifting map and the (X,U^in) context map
#8  explain why A is history-conditioned while B is held context-independent
#10 Stage 0 / Stage 1 -> nominal backbone / deployment-consistent refinement
#11 rename Section IV
#13 sync the Abstract with the new problem-driven story
#14 sync the Conclusion (two-layer summary, fix the "low-rank lifting" misattribution)
#15 reorganise Related Work around four functional roles
#16 title: "Low-Rank Lifting" -> "Low-Rank Transition Modulation"
#17 compress the L_R defence in IV-B and relocate the four-conjunct statement to the diagnostics
#18 unify terminology: "rolled-out latent trajectory" -> "rolled-out history"
"""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")
R = []

# ---------------------------------------------------------------- #16 title
R.append((
    r"\title{Transformer-Koopman: History-Conditioned Low-Rank Lifting with Rollout-Aware Training and Real-Time Predictive Control}",
    r"\title{Transformer-Koopman: History-Conditioned Low-Rank Transition Modulation with Rollout-Aware Training and Real-Time Predictive Control}"
))

# ---------------------------------------------------------------- #13 abstract
R.append((
    "Koopman modeling represents nonlinear dynamics as linear evolution in a lifted space whose accuracy depends critically on the lifting map and the identified operator. Many conventional EDMD and learned-lifting approaches use instantaneous-state observables with a fixed lifted transition, so they neglect short-term temporal correlations and cannot distinguish how the system evolves from different past trajectories. We propose Transformer-Koopman, where a patch-based Transformer encoder maps a finite history window to a structured lifted state and a low-rank history-dependent term modulates a full-rank nominal transition.",
    "Koopman modeling represents nonlinear dynamics as linear evolution in a lifted space whose accuracy depends on the lifting map and the identified operator. Many conventional EDMD and learned-lifting approaches use instantaneous-state observables with a fixed lifted transition, so they neglect short-term temporal correlations and cannot distinguish how the system evolves from different past trajectories. History-aware lifting recovers that information, but one global lifted transition still forces all history-dependent regimes to share a single evolution law. We propose Transformer-Koopman, where a patch-based Transformer encoder maps a finite history window to a structured lifted state and a low-rank history-dependent term modulates a full-rank nominal transition."
))
R.append((
    "The predictor is integrated into a one-iteration real-time-iteration (RTI) MPC that avoids re-running the full Transformer lifting encoder at every stage, achieving a $p95$ latency of 120\\,ms under a 200-ms sampling period and tracking a matched exact scheduled NMPC oracle within $1\\%$.",
    "The predictor is integrated into a one-iteration real-time-iteration (RTI) MPC that avoids re-running the full encoder at every stage, achieving a $p95$ latency of 120\\,ms under a 200-ms sampling period and tracking a matched exact scheduled NMPC oracle within $1\\%$."
))
R.append((
    "We show that a one-step-trained history-conditioned operator develops a training--deployment inconsistency under recursive scheduled propagation that spectral stabilization does not repair, whereas training under the same scheduled rollout used at deployment restores long-horizon accuracy.",
    "We show that a one-step-trained history-conditioned operator develops a training--deployment inconsistency under recursive scheduled propagation that spectral stabilization does not repair, whereas training under the deployment rollout restores long-horizon accuracy."
))
R.append((
    "Modeling and real-time control results on a 2-state soft robotic platform support the reported claims; results on a 6-state manipulator and hardware validation on the soft robot are left for future work.",
    "Modeling and real-time control results on a 2-state soft robotic platform support the reported claims; a 6-state manipulator and hardware validation are left for future work."
))

# ---------------------------------------------------------------- #15 related work
OLD_RW_HEAD = "\\subsection{Koopman Learning and Recursive Prediction}"
R.append((
    OLD_RW_HEAD,
    "\\subsection{Representation: Instantaneous versus History-Based Lifting}"
))
R.append((
    "Two lines relax this restriction. Delay-embedding variants enrich the dictionary with time-shifted measurements or Hankel/HAVOK coordinates \\cite{kamb2020timedelay, brunton2017chaos, arbabi2017ergodic, das2019delay}, so the operator acts on a history-augmented state, but history enters only through the observables. Context-aware and time-varying formulations instead let the effective operator depend on recent data: Koopa computes context-aware operators for non-stationary forecasting \\cite{liu2023koopa}, and MamKO generates time-varying Koopman matrices from online history \\cite{li2025mamko}. Our formulation instead confines history's influence to a single low-rank family identified jointly with the lifting map, and the lifted dynamics remain linear in the lifted state for a given context, providing the conditional-linear structure exploited by the scheduled RTI controller.",
    "Two lines relax this restriction. Delay-embedding variants enrich the dictionary with time-shifted measurements or Hankel/HAVOK coordinates \\cite{kamb2020timedelay, brunton2017chaos, arbabi2017ergodic, das2019delay}, so the operator acts on a history-augmented state, but history enters only through the observables. Transformers model temporal dependencies through self-attention \\cite{vaswani2017attention}, while patch-based tokenization provides an efficient representation of local temporal structure \\cite{nie2023time}. In Koopman lifting, where the relevant temporal context is unknown a priori, Transformers can incorporate short-term information from past trajectories.\n\n"
    "\\subsection{Transition Adaptation: Context-Aware and Time-Varying Operators}\n\n"
    "A history-augmented representation, however, still leaves the transition itself time-invariant. Context-aware and time-varying formulations instead let the effective operator depend on recent data: Koopa computes context-aware operators for non-stationary forecasting \\cite{liu2023koopa}, and MamKO generates time-varying Koopman matrices from online history \\cite{li2025mamko}. Our formulation separates history dependence into two roles: history is encoded into the lifted state, while a low-rank family identified jointly with the lifting map selectively corrects a shared nominal transition, so that the lifted dynamics remain linear in the lifted state for a given context and provide the conditional-linear structure exploited by the scheduled RTI controller."
))
# remove the old Transformer subsection header + its first paragraph (now moved up)
R.append((
    "\\subsection{Transformers for Temporal Sequence Modeling}\n\nTransformers model temporal dependencies through self-attention \\cite{vaswani2017attention}, while patch-based tokenization provides an efficient representation of local temporal structure \\cite{nie2023time}. In Koopman lifting, where the relevant temporal context is unknown a priori, Transformers can incorporate short-term information from past trajectories.\n\nRecent work has explored",
    "Recent work has explored"
))
# move the multi-step paragraph into its own subsection
R.append((
    "Multi-step training is also used in learned Koopman models",
    "\\subsection{Recursive Multi-Step Deployment}\n\nMulti-step training is also used in learned Koopman models"
))

# ---------------------------------------------------------------- #11 section IV rename
R.append((
    "\\section{Transformer-Based Temporal Lifting}",
    "\\section{History-Conditioned Transformer--Koopman Modeling}"
))

# ---------------------------------------------------------------- #7 lifting vs context roles
R.append((
    "where $C_\\phi$ is a context network that observes the same state and input history carried by the augmented predictor state.",
    "where $C_\\phi$ is a context network that observes the same state and input history carried by the augmented predictor state. The lifting map and the context map deliberately use different information. The lifting map consumes only the measured state history, so that the lifted state remains a compact, state-preserving representation of the current dynamical condition. The context map additionally consumes the past inputs, because the effective latent transition can depend not only on the current condition but also on how that condition was reached, and because past inputs are information that the state-history lifting map does not itself observe."
))

# ---------------------------------------------------------------- #8 B rationale
R.append((
    "so that history selectively adjusts the nominal transition rather than regenerating the entire operator.",
    "so that history selectively adjusts the nominal transition rather than regenerating the entire operator. History dependence is deliberately confined to the lifted transition: the current-input channel $\\mB$ is held context-independent, so that the internal evolution can adapt to the recent trajectory without changing the affine dependence on the current decision variable, which keeps the predictor control-affine for a given context."
))

# ---------------------------------------------------------------- #10 Stage 0/1 story
R.append((
    "Training proceeds in two stages. Stage~0 (\\emph{initialization}) fits a time-invariant base operator to the encoder-generated one-step latent distribution. Stage~1 (\\emph{rollout-aware scheduled training}) then trains the full history-conditioned family on the \\emph{propagated}-latent distribution that arises at deployment, by minimizing the rollout-aware scheduled objective $\\mathcal{L}_R$ of Definition~\\ref{def:rollout_aware}.",
    "The history-conditioned transition introduces an additional deployment issue. During one-step training the context is evaluated on measured histories, whereas during recursive prediction future contexts are evaluated on predicted histories, so prediction errors alter the scheduling signal itself. Training therefore proceeds in two stages. Stage~0 (\\emph{initialization}) learns the shared nominal backbone---the encoder and a time-invariant base operator---from encoder-consistent one-step transitions. Stage~1 (\\emph{rollout-aware scheduled training}) then refines the context-dependent correction, training the full history-conditioned family on the \\emph{propagated}-latent distribution that arises at deployment, by minimizing the rollout-aware scheduled objective $\\mathcal{L}_R$ of Definition~\\ref{def:rollout_aware}."
))

# ---------------------------------------------------------------- #17a compress the L_R defence
R.append((
    "We claim only that $\\mathcal{L}_R$ \\emph{mitigates} latent rollout inconsistency and improves deployment-distribution accuracy; we do not claim it guarantees strict manifold invariance. The claim that one-step training insufficiently constrains the rollout distribution is supported by the \\emph{conjunction} of four observations: $\\epsilon_k>0$, increasing $d_{\\mathcal M}(H)$, failure of naive latent propagation, and recovery under rollout-aware training. No single observation is sufficient on its own.",
    "We claim only that $\\mathcal{L}_R$ \\emph{mitigates} latent rollout inconsistency and improves deployment-distribution accuracy. The evidence for that claim, and its limits, are discussed with the diagnostics in Section~\\ref{sec:experiments}."
))

# ---------------------------------------------------------------- #17b relocate the four conjuncts
R.append((
    "we report this honestly rather than presenting the bound as tight.",
    "we report this honestly rather than presenting the bound as tight.\n\nThese measurements bear on the claim that one-step training insufficiently constrains the rollout distribution. That claim rests on the \\emph{conjunction} of four observations---a positive one-step consistency defect ($\\epsilon_k>0$), a rollout defect $d_{\\mathcal M}(H)$ that grows with the horizon, the failure of naive latent propagation, and the recovery obtained under rollout-aware training---and no single observation is sufficient on its own; the latter two are quantified in the experimental study."
))

# ---------------------------------------------------------------- #14 conclusion
R.append((
    "This paper presented Transformer-Koopman, a history-conditioned low-rank lifting framework for learning Koopman models of controlled nonlinear systems from finite history windows. A patch-based Transformer encoder maps the history to a structured lifted state, and---unlike instantaneous-state lifting with a single time-invariant operator---the lifted transition is modulated by the history through a rank-$r$ term $\\mA(\\vc)=\\mA_0+\\mU\\,\\mathrm{diag}(\\gamma_\\psi(\\vc))\\mV^\\top$ ($r=2$).",
    "This paper presented Transformer-Koopman, a framework for learning history-conditioned Koopman models of controlled nonlinear systems from finite history windows. Because the measured state need not reveal the system's internal dynamics, a patch-based Transformer encoder first maps the history to a structured, state-preserving lifted state. Because a single global lifted transition would then still require all history-dependent regimes to share one evolution law, the lifted transition is additionally modulated by the history through a rank-$r$ term $\\mA(\\vc)=\\mA_0+\\mU\\,\\mathrm{diag}(\\gamma_\\psi(\\vc))\\mV^\\top$ ($r=2$), which confines history dependence to a structured correction of a shared nominal operator while keeping the propagation conditional-linear."
))

# ---------------------------------------------------------------- #18 terminology
R.append((
    "The context must therefore be re-evaluated along the rolled-out latent trajectory rather than assumed,",
    "The context must therefore be re-evaluated along the rolled-out history rather than assumed,"
))


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    assert "\ufeff" not in raw, "unexpected BOM"
    nl = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")

    for i, (old, new) in enumerate(R, 1):
        c = text.count(old)
        assert c == 1, "item %d: expected 1 occurrence, found %d\n--- %s" % (i, c, old[:100])
        text = text.replace(old, new)
        print("applied %d" % i)

    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(text.split("\n")))
    print("OK")


if __name__ == "__main__":
    main()
