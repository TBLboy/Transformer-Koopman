# -*- coding: utf-8 -*-
"""Apply Main(9) second-round front-matter review: P0 (technical correctness) and
terminology/clarity items to Main.tex.

P0-1  remove the "history-conditioned => MPC remains a QP" claim (technically wrong:
      the QP arises from the scheduled RTI linearization, not from A(c) alone)
P0-2  add "for a given context" where conditional linearity is claimed
P0-3  disambiguate "encoder" -> "full Transformer lifting encoder"
P0-4  remove the exhaustive-literature novelty claim ("in neither case ...")
Also applied: reviewer's suggested compression of Contributions 1-3, Introduction
method-granularity reduction, antecedent fix in the Transformer-Koopman comparison,
and the concrete latency figure in the Abstract.
Every replacement is asserted to occur exactly once.
"""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")

REPLACE = [
    # --- Abstract: concrete latency figure + disambiguate encoder -------------------
    (r"MPC that avoids re-running the full encoder at every prediction stage, achieving a $p95$ controller latency of 120\,ms, within the sampling period, while tracking a matched exact scheduled NMPC oracle within $1\%$.",
     r"MPC that avoids re-running the full Transformer lifting encoder at every prediction stage, achieving a $p95$ controller latency of 120\,ms under a 200-ms sampling period, while tracking a matched exact scheduled NMPC oracle within $1\%$."),

    # --- P0-4 / P2-11: de-absolutize novelty claim, soften error-accumulation ------
    (r"and context-aware formulations regenerate the operator from recent data \cite{liu2023koopa, li2025mamko}; in neither case is the history placed inside a single low-rank transition family identified jointly with the lifting map. Consequently, prediction errors accumulate during multi-step autoregressive rollout.",
     r"and context-aware formulations regenerate the operator from recent data \cite{liu2023koopa, li2025mamko}. These approaches differ from the formulation considered here, where history selectively modulates a low-rank deviation around a nominal lifted transition learned jointly with the lifting map, and such limitations can become more pronounced under recursive multi-step prediction."),

    # --- Introduction: reduce Methodology-level granularity ------------------------
    (r"The first is a lifting map implemented as a temporal encoder: it processes a finite history window through a Transformer encoder with non-overlapping multivariate patches and combines the resulting history features with the current physical state to form a structured lifted state, from which the physical state is recovered by a simple linear projection.",
     r"The first component uses a Transformer encoder to map a finite history window into a structured lifted state that retains the measured physical state."),

    # --- P0-3: disambiguate encoder in the Introduction ---------------------------
    (r"one-iteration RTI-MPC that avoids re-running the full encoder at every prediction stage, and we establish",
     r"one-iteration RTI-MPC that avoids re-running the full Transformer lifting encoder at every prediction stage, and we establish"),

    # --- P0-1 + P1-5: Contribution 1 ------------------------------------------------
    (r"\item \textbf{Low-rank history-conditioned modulation of the lifted transition.} History is used not only to form the lifted state but also to modulate the effective lifted transition, which is confined to a single low-rank family identified jointly with the lifting map. Unlike context-aware or time-varying Koopman formulations that regenerate the operator from data \cite{liu2023koopa, li2025mamko}, and unlike low-rank Koopman operators that replace the transition itself by a rank-$r$ factorization \cite{forootani2026spectral}, the nominal transition remains full-rank and only its history-dependent deviation is low-rank, so linearity in the lifted state is preserved and the predictive-control problem remains a quadratic program. Ablations show that the selective history dependence is concentrated in the transition modulation.",
     r"\item \textbf{Low-rank history-conditioned modulation of the lifted transition.} We introduce a Koopman model in which finite-history information forms the lifted representation and selectively modulates a full-rank nominal transition through a low-rank history-dependent update, while preserving linear lifted-state propagation for a given context, which is compatible with the scheduled RTI formulation developed later."),

    # --- P1-6: Contribution 2 ------------------------------------------------------
    (r"\item \textbf{Scheduled-rollout inconsistency and deployment-consistent training.} We identify a training--deployment inconsistency that arises when a one-step-trained history-conditioned Koopman model is recursively propagated with its context rescheduled from predicted histories: the latent and context distributions progressively depart from those encountered during one-step fitting, and imposing spectral stability does not repair this failure mode. We therefore train the predictor under the same recursively scheduled propagation used at deployment, exposing it to its self-generated latent states, predicted histories, and context sequence. This restores long-horizon scheduled-propagation accuracy to a level close to recurrent re-encoding.",
     r"\item \textbf{Scheduled-rollout inconsistency and deployment-consistent training.} We identify a training--deployment mismatch that arises when a one-step-trained history-conditioned Koopman model is recursively propagated with its context rescheduled from predicted histories, and show that spectral stabilization alone does not repair this failure mode. Training under the same scheduled propagation used at deployment restores long-horizon prediction accuracy, to a level close to recurrent re-encoding."),

    # --- P1-7: Contribution 3 ------------------------------------------------------
    (r"\item \textbf{Real-time predictive deployment.} The rollout-trained scheduled predictor is integrated into a one-iteration RTI-MPC. By avoiding a full encoder evaluation at every prediction stage, the controller runs in real time on the soft-robot platform and tracks a matched exact scheduled NMPC oracle within $1\%$. A finite-horizon theory---finite-history Markovization, latent rollout error propagation, a bounded prediction-error theorem, and a local RTI approximation result---is established and supported by empirical diagnostics.",
     r"\item \textbf{Real-time predictive deployment.} The rollout-trained scheduled predictor is integrated into a one-iteration RTI-MPC that avoids a full Transformer lifting encoder evaluation at every prediction stage. The resulting controller tracks a matched exact scheduled NMPC oracle within $1\%$, and a finite-horizon analysis supported by empirical diagnostics characterizes the rollout-error propagation and the local RTI approximation."),

    # --- P0-1 / P0-2: Related Work conditional-linearity fix -----------------------
    (r"Our formulation instead confines history's influence to a single low-rank family identified jointly with the lifting map and linear in the lifted state, so predictive control remains a quadratic program.",
     r"Our formulation instead confines history's influence to a single low-rank family identified jointly with the lifting map, and the lifted dynamics remain linear in the lifted state for a given context, providing the conditional-linear structure exploited by the scheduled RTI controller."),

    # --- P2-12: antecedent clarity in the Transformer--Koopman comparison ----------
    (r"Prediction is generated by the identified Koopman model inside a real-time predictive controller rather than by the Transformer itself.",
     r"In contrast, our Transformer is used only for history encoding, while prediction inside the controller is performed by the structured Koopman model."),

    # --- P0-3: disambiguate encoder in the RTI positioning paragraph ---------------
    (r"and the encoder need not be re-run at every prediction stage, letting the single-iteration controller fit inside the sampling period.",
     r"and the full Transformer lifting encoder need not be re-run at every prediction stage, letting the single-iteration controller fit inside the sampling period."),
]


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    assert "\ufeff" not in text, "unexpected BOM"
    nl = "\r\n" if "\r\n" in text else "\n"

    for old, new in REPLACE:
        n = text.count(old)
        assert n == 1, "expected 1 occurrence, got %d for: %s" % (n, old[:80])
        text = text.replace(old, new)
    print("applied %d replacements" % len(REPLACE))

    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(text.replace("\r\n", "\n").split("\n")))
    print("OK")


if __name__ == "__main__":
    main()
